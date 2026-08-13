import json, os, re, shutil, subprocess
from scoring import deterministic_evaluate
import requests


def detect_engine():
    forced=os.getenv("LLM_PROVIDER", "").strip().lower()
    if forced in ("claude_code","anthropic","openai"): return forced
    if shutil.which("claude"): return "claude_code"
    if os.getenv("ANTHROPIC_API_KEY"): return "anthropic"
    if os.getenv("OPENAI_API_KEY"): return "openai"
    return "deterministic"


def prompt_for(e):
    return f"""You are a disciplined Indian-equity panel. Use ONLY the evidence JSON below. Never invent or estimate missing values. If a needed value is missing, say 'data unavailable'. A BUY requires genuinely favorable risk/reward with confirmation from momentum/volume. WATCH means promising but unconfirmed. AVOID means poor risk/reward. Return JSON only. Every agent gets conviction 0-100 and a point <=25 words. Judge gets winner, verdict BUY/WATCH/AVOID, confidence 1-10, rationale <=2 lines, key_catalyst. If verdict is BUY, also provide suggested 'buy_zone' (range), 'target' (price), and 'stop_loss' (price) based on technical swing levels or analyst targets present in the evidence. If not BUY, set these to null.\n\nEvidence:\n{json.dumps(e, separators=(',',':'))}\n\nSchema: {{\"scores\":{{\"bull\":{{\"score\":0,\"point\":\"\"}},\"bear\":{{\"score\":0,\"point\":\"\"}},\"fundamentalist\":{{\"score\":0,\"point\":\"\"}},\"technician\":{{\"score\":0,\"point\":\"\"}},\"newsdesk\":{{\"score\":0,\"point\":\"\"}}}},\"verdict\":{{\"winner\":\"Bull\",\"verdict\":\"WATCH\",\"confidence\":5,\"rationale\":\"\",\"key_catalyst\":\"\",\"buy_zone\":null,\"target\":null,\"stop_loss\":null}}}}"""


def claude_call(prompt):
    model=os.getenv("CLAUDE_MODEL","haiku")
    p=subprocess.run(["claude","-p",prompt,"--output-format","json","--model",model],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=120)
    if p.returncode!=0: raise RuntimeError("claude failed")
    env=json.loads(p.stdout)
    if env.get("is_error"): raise RuntimeError("claude returned error")
    raw=env.get("result", env)
    if isinstance(raw,str): raw=json.loads(raw)
    return raw


def anthropic_call(prompt):
    key=os.getenv("ANTHROPIC_API_KEY")
    r=requests.post("https://api.anthropic.com/v1/messages",headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},json={"model":os.getenv("ANTHROPIC_MODEL","claude-3-5-haiku-latest"),"max_tokens":1200,"messages":[{"role":"user","content":prompt}]},timeout=45)
    r.raise_for_status(); data=r.json(); return json.loads(data["content"][0]["text"])


def openai_call(prompt):
    key=os.getenv("OPENAI_API_KEY")
    r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":os.getenv("OPENAI_MODEL","gpt-4o-mini"),"temperature":0,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":"Return JSON only."},{"role":"user","content":prompt}]},timeout=45)
    r.raise_for_status(); return json.loads(r.json()["choices"][0]["message"]["content"])


def evidence_numbers(e):
    raw=json.dumps(e)
    vals=set()
    for m in re.findall(r"-?\d+(?:\.\d+)?", raw):
        try: vals.add(round(float(m),4))
        except: pass
    return vals


def verify_result(e, result):
    allowed=evidence_numbers(e)
    text=json.dumps(result.get("scores",{}))+json.dumps(result.get("verdict",{}))
    # Ignore JSON score/confidence fields and detect only numbers embedded in textual reasoning.
    text_fields=[]
    for a in result.get("scores",{}).values():
        text_fields += a.get("reasons",[]) if isinstance(a,dict) else []
        if isinstance(a,dict): text_fields.append(a.get("point",""))
    text_fields += [result.get("verdict",{}).get("rationale",""), result.get("verdict",{}).get("key_catalyst","")]
    for txt in text_fields:
        for token in re.findall(r"-?\d+(?:\.\d+)?", txt or ""):
            try:
                x=float(token)
                if not any(abs(x-y)<0.011 for y in allowed): return False
            except: pass
    return True


def normalize_llm(raw, e):
    scores={}
    for k in ("bull","bear","fundamentalist","technician","newsdesk"):
        x=raw.get("scores",{}).get(k,{})
        scores[k]={"score":max(0,min(100,float(x.get("score",50)))),"reasons":[x.get("point","data unavailable")][:1]}
    v=raw.get("verdict",{})
    verdict=v.get("verdict","WATCH") if v.get("verdict") in ("BUY","WATCH","AVOID") else "WATCH"
    conf=max(1,min(10,int(v.get("confidence",5))))
    
    # Extract trade guide levels
    buy_zone = v.get("buy_zone")
    target = v.get("target")
    stop_loss = v.get("stop_loss")
    
    # Calculate deterministic fallback levels if not provided by LLM
    if verdict == "BUY" and (not buy_zone or not target or not stop_loss):
        latest = e.get("price", {}).get("live")
        if latest:
            if not buy_zone: buy_zone = f"₹{latest:.2f} - ₹{latest*1.015:.2f}"
            if not stop_loss:
                sw_low = e.get("technicals", {}).get("swing_low")
                stop_loss = f"₹{sw_low:.2f}" if sw_low and sw_low < latest and sw_low > latest * 0.85 else f"₹{latest * 0.92:.2f} (8% SL)"
            if not target:
                t_mean = e.get("analyst", {}).get("target_mean")
                target = f"₹{t_mean:.2f}" if t_mean and t_mean > latest else f"₹{latest * 1.15:.2f} (15% Target)"
                
    return {"scores":scores,"verdict":{"winner":v.get("winner","Bull"),"verdict":verdict,"confidence":conf,"rationale":v.get("rationale","data unavailable"),"key_catalyst":v.get("key_catalyst","data unavailable"),"bull_score":scores["bull"]["score"],"bear_score":scores["bear"]["score"],"net":round(scores["bull"]["score"]-scores["bear"]["score"],1),"buy_zone":buy_zone,"target":target,"stop_loss":stop_loss}}


def evaluate_with_engine(e):
    engine=detect_engine()
    if engine=="deterministic": return deterministic_evaluate(e)
    try:
        prompt=prompt_for(e)
        raw=claude_call(prompt) if engine=="claude_code" else anthropic_call(prompt) if engine=="anthropic" else openai_call(prompt)
        result=normalize_llm(raw,e)
        if not verify_result(e,result): raise RuntimeError("grounding verifier failed")
        result["verifier_ok"]=True
        return result
    except Exception:
        result=deterministic_evaluate(e)
        result["verifier_ok"]=False
        return result
