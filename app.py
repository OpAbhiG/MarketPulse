import json, os, re, sqlite3, subprocess, threading, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
from flask import Flask, jsonify, request, send_file

from data_sources import load_demo_evidence, load_live_evidence, load_universe
from llm import evaluate_with_engine, detect_engine

BASE = Path(__file__).resolve().parent

# Writable paths for Vercel Serverless environment
if os.getenv("VERCEL"):
    DB_PATH = Path("/tmp") / "audit.sqlite3"
    UNIVERSE_PATH = Path("/tmp") / "universe.json"
    ENV_PATH = Path("/tmp") / ".env"
    
    # Initialize templates inside /tmp if not present
    import shutil
    if (BASE / "universe.json").exists() and not UNIVERSE_PATH.exists():
        try:
            shutil.copy(BASE / "universe.json", UNIVERSE_PATH)
        except Exception:
            pass
    if (BASE / ".env").exists() and not ENV_PATH.exists():
        try:
            shutil.copy(BASE / ".env", ENV_PATH)
        except Exception:
            pass
    elif not ENV_PATH.exists():
        try:
            ENV_PATH.write_text("", encoding="utf-8")
        except Exception:
            pass
else:
    DB_PATH = BASE / "audit.sqlite3"
    UNIVERSE_PATH = BASE / "universe.json"
    ENV_PATH = BASE / ".env"


def load_env(path=ENV_PATH, force=False):
    if not path.exists():
        return
    try:
        content = path.read_text(encoding="utf-8")
        for raw in content.splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                if force or key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass

load_env()

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

AGENTS = [
    ("scout", "Scout", "screens the stock universe for movers", "Scanned", "Shortlisted"),
    ("technician", "Technician", "reads price action, RVOL & trend", "Analyzed", "Avg RVOL"),
    ("fundamentalist", "Fundamentalist", "weighs valuation & analyst targets", "Covered", "Avg upside"),
    ("newsdesk", "Newsdesk", "pulls live news & scores sentiment", "Headlines", "Net tone"),
    ("bull", "Bull", "argues the case to buy", "Cases", "Avg score"),
    ("bear", "Bear", "argues the case against", "Cases", "Avg score"),
    ("judge", "Judge", "weighs the debate, issues verdict + confidence", "Verdicts", "Buy"),
    ("messenger", "Messenger", "sends signals to Telegram", "Sent", "Engine"),
]

state_lock = threading.Lock()
state = {
    "running": False, "run_id": None, "mode": "live", "engine": "deterministic",
    "started_at": None, "updated_at": None, "completed_at": None,
    "active_step": "idle",
    "agents": {}, "kpis": {"universe": 0, "debate": 0, "buy_signals": 0, "top_pick": None},
    "verdicts": [], "log": [], "telegram": {"configured": False, "sent": 0},
}

def fresh_agents():
    return {aid: {"id": aid, "name": name, "role": role, "stat1_label": s1, "stat2_label": s2,
                  "status": "offline", "stat1": 0, "stat2": "—"} for aid, name, role, s1, s2 in AGENTS}

state["agents"] = fresh_agents()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      started_at TEXT NOT NULL, completed_at TEXT, mode TEXT, engine TEXT,
      universe_count INTEGER DEFAULT 0, shortlist_count INTEGER DEFAULT 0,
      buy_count INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS verdicts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id INTEGER NOT NULL, created_at TEXT NOT NULL, symbol TEXT NOT NULL,
      verdict TEXT, confidence INTEGER, winner TEXT, rationale TEXT, catalyst TEXT,
      price REAL, day_change_pct REAL, evidence_json TEXT, result_json TEXT,
      verifier_ok INTEGER DEFAULT 1,
      FOREIGN KEY(run_id) REFERENCES runs(id)
    );
    """)
    conn.commit(); conn.close()

init_db()


def now_ist():
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(timespec="seconds")


def safe_num(v):
    try:
        return float(v)
    except Exception:
        return None


def log(msg):
    with state_lock:
        state["log"].append(f"{now_ist()} · {msg}")
        state["log"] = state["log"][-80:]
        state["updated_at"] = now_ist()


def set_agent(aid, status=None, stat1=None, stat2=None):
    with state_lock:
        a = state["agents"][aid]
        if status is not None: a["status"] = status
        if stat1 is not None: a["stat1"] = stat1
        if stat2 is not None: a["stat2"] = stat2
        state["updated_at"] = now_ist()


def post_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False, "Telegram not configured"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=15)
        if r.ok and r.json().get("ok"):
            return True, "sent"
        return False, "Telegram rejected request"
    except Exception:
        return False, "Telegram request failed"


def signal_text(v):
    e = v["evidence"]
    cap = e.get("cap_segment", "")
    symbol = e.get("symbol", "")
    price = e.get("price", {}).get("live")
    chg = e.get("price", {}).get("day_change_pct")
    
    # Extract trade guide levels
    verdict_data = v.get("verdict", {})
    guide_text = ""
    if verdict_data.get("buy_zone") or verdict_data.get("target") or verdict_data.get("stop_loss"):
        guide_text = (f"🎯 <b>Trade Setup Guide</b>:\n"
                      f"• Buy Zone: {verdict_data.get('buy_zone', 'data unavailable')}\n"
                      f"• Target Price: {verdict_data.get('target', 'data unavailable')}\n"
                      f"• Stop Loss: {verdict_data.get('stop_loss', 'data unavailable')}\n\n")
                      
    return (f"🟢 BUY SIGNAL — {symbol} ({cap} cap)\n"
            f"Verdict: BUY | Confidence: {verdict_data.get('confidence', 0)}/10\n"
            f"Winner: {verdict_data.get('winner', 'Bull')}\n\n"
            f"{guide_text}"
            f"Why: {verdict_data.get('rationale', 'data unavailable')}\n"
            f"Key catalyst: {verdict_data.get('key_catalyst', 'data unavailable')}\n"
            f"Live price: ₹{price if price is not None else 'data unavailable'} | Day change: {chg if chg is not None else 'data unavailable'}%\n"
            "— Analysis only. No trade was placed. Not investment advice.")


def summary_text(fired, mode, engine):
    lines = [f"<b>Indian Stock Analysis — Daily Summary</b>", f"Mode: {mode} | Engine: {engine}"]
    if fired:
        lines.append("BUY signals fired:")
        for v in fired:
            lines.append(f"• {v['evidence']['symbol']} — {v['verdict']['confidence']}/10")
    else:
        lines.append("no BUY signals fired")
    lines.append("Analysis only. No orders were placed.")
    return "\n".join(lines)


def run_cycle():
    with state_lock:
        state["running"] = True
        state["mode"] = "live"
        state["run_id"] = None
        state["started_at"] = now_ist(); state["completed_at"] = None
        state["agents"] = fresh_agents()
        state["verdicts"] = []
        state["log"] = []
        state["kpis"] = {"universe": 0, "debate": 0, "buy_signals": 0, "top_pick": None}
        state["telegram"] = {"configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")), "sent": 0}
        state["active_step"] = "scout"

    delay = max(0.05, float(os.getenv("AGENT_DELAY", "0.35")))
    threshold = max(1, min(10, int(os.getenv("CONFIDENCE_THRESHOLD", "7"))))
    engine = detect_engine()
    with state_lock: state["engine"] = engine

    conn = db()
    cur = conn.execute("INSERT INTO runs(started_at, mode, engine) VALUES (?, ?, ?)", (state["started_at"], "live", engine))
    run_id = cur.lastrowid; conn.commit()
    with state_lock: state["run_id"] = run_id

    try:
        log("Loading live data")
        universe = load_universe(UNIVERSE_PATH)
        if isinstance(universe, dict):
            all_symbols = [x for bucket in universe.values() for x in bucket]
        else:
            all_symbols = list(universe)
        set_agent("scout", "working")
        evidence = load_live_evidence(universe)
        shortlist = []
        for bucket in ("large", "mid", "small"):
            items = [e for e in evidence if e.get("cap_segment") == bucket]
            items.sort(key=lambda x: (x.get("price", {}).get("day_change_pct") is not None,
                                      x.get("price", {}).get("day_change_pct") or -999), reverse=True)
            shortlist.extend(items[:int(os.getenv("SHORTLIST_PER_BUCKET", "4"))])
        set_agent("scout", "done", len(evidence), len(shortlist))
        with state_lock:
            state["kpis"]["universe"] = len(evidence)
            state["kpis"]["debate"] = len(shortlist)
        log(f"Scout shortlisted {len(shortlist)} stocks from {len(evidence)}")
        time.sleep(delay)

        # Agent live stats before debate
        with state_lock: state["active_step"] = "technician"
        set_agent("technician", "working")
        rv = [e.get("technicals", {}).get("rvol") for e in shortlist if e.get("technicals", {}).get("rvol") is not None]
        avg_rvol = round(sum(rv)/len(rv), 2) if rv else None
        set_agent("technician", "done", len(shortlist), avg_rvol if avg_rvol is not None else "—")
        time.sleep(delay)

        with state_lock: state["active_step"] = "fundamentalist"
        set_agent("fundamentalist", "working")
        ups = [e.get("analyst", {}).get("upside_pct") for e in shortlist if e.get("analyst", {}).get("upside_pct") is not None]
        avg_up = round(sum(ups)/len(ups), 1) if ups else None
        set_agent("fundamentalist", "done", len(ups), f"{avg_up}%" if avg_up is not None else "—")
        time.sleep(delay)

        with state_lock: state["active_step"] = "newsdesk"
        set_agent("newsdesk", "working")
        heads = sum((e.get("news", {}).get("total") or 0) for e in shortlist)
        tones = []
        for e in shortlist:
            n=e.get("news", {}); total=n.get("total") or 0
            if total: tones.append(((n.get("positive") or 0)-(n.get("negative") or 0))/total)
        net_tone = round(sum(tones)/len(tones), 2) if tones else None
        set_agent("newsdesk", "done", heads, net_tone if net_tone is not None else "—")
        time.sleep(delay)

        with state_lock: state["active_step"] = "debate"
        set_agent("bull", "working")
        set_agent("bear", "working")
        time.sleep(delay)

        results=[]
        for idx, ev in enumerate(shortlist):
            # one combined call per stock
            res = evaluate_with_engine(ev)
            results.append({"evidence": ev, **res})
            set_agent("bull", "working", idx+1, round(res["scores"]["bull"]["score"],1))
            set_agent("bear", "working", idx+1, round(res["scores"]["bear"]["score"],1))
            with state_lock:
                state["verdicts"].append({
                    "symbol": ev["symbol"], "name": ev["name"], "cap_segment": ev["cap_segment"],
                    "verdict": res["verdict"]["verdict"], "confidence": res["verdict"]["confidence"],
                    "winner": res["verdict"]["winner"], "why": res["verdict"]["rationale"],
                    "price": ev["price"]["live"], "day_change_pct": ev["price"]["day_change_pct"],
                    "catalyst": res["verdict"]["key_catalyst"], "verifier_ok": res.get("verifier_ok", True),
                    "scores": res.get("scores", {}),
                    "buy_zone": res["verdict"].get("buy_zone"),
                    "target": res["verdict"].get("target"),
                    "stop_loss": res["verdict"].get("stop_loss"),
                    "news": ev.get("news", {})
                })
            conn.execute("INSERT INTO verdicts(run_id, created_at, symbol, verdict, confidence, winner, rationale, catalyst, price, day_change_pct, evidence_json, result_json, verifier_ok) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, now_ist(), ev["symbol"], res["verdict"]["verdict"], res["verdict"]["confidence"], res["verdict"]["winner"],
                 res["verdict"]["rationale"], res["verdict"]["key_catalyst"], ev["price"]["live"], ev["price"]["day_change_pct"],
                 json.dumps(ev), json.dumps(res), int(res.get("verifier_ok", True))))
            conn.commit()

        set_agent("bull", "done", len(results), round(sum(r["scores"]["bull"]["score"] for r in results)/len(results),1) if results else 0)
        set_agent("bear", "done", len(results), round(sum(r["scores"]["bear"]["score"] for r in results)/len(results),1) if results else 0)
        time.sleep(delay)

        with state_lock: state["active_step"] = "judge"
        set_agent("judge", "working")
        fired=[r for r in results if r["verdict"]["verdict"] == "BUY" and r["verdict"]["confidence"] >= threshold]
        top = sorted(results, key=lambda r: r["verdict"]["confidence"], reverse=True)[0] if results else None
        set_agent("judge", "done", len(results), len(fired))
        with state_lock:
            state["kpis"]["buy_signals"] = len(fired)
            state["kpis"]["top_pick"] = ({"symbol": top["evidence"]["symbol"], "confidence": top["verdict"]["confidence"]} if top else None)
        time.sleep(delay)

        with state_lock: state["active_step"] = "messenger"
        set_agent("messenger", "working")
        sent=0
        for r in fired:
            ok, _ = post_telegram(signal_text(r))
            if ok: sent += 1
        post_telegram(summary_text(fired, "live", engine))
        set_agent("messenger", "done", sent, engine)
        with state_lock: state["telegram"]["sent"] = sent
        conn.execute("UPDATE runs SET completed_at=?, universe_count=?, shortlist_count=?, buy_count=? WHERE id=?",
                     (now_ist(), len(evidence), len(shortlist), len(fired), run_id))
        conn.commit()
        log(f"Run complete: {len(fired)} BUY signal(s)")
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if token and token in tb:
            tb = tb.replace(token, "[REDACTED_TELEGRAM_BOT_TOKEN]")
        print(f"Error in background run_cycle:\n{tb}")
        log("Run stopped safely due to an internal error")
    finally:
        conn.close()
        with state_lock:
            state["running"] = False
            state["completed_at"] = now_ist()
            state["active_step"] = "idle"
            for a in state["agents"].values():
                if a["status"] == "working": a["status"] = "done"
            state["updated_at"] = now_ist()


@app.get("/")
def index():
    return send_file(BASE / "dashboard.html")

@app.post("/start")
def start():
    if state["running"]:
        return jsonify({"ok": False, "error": "A run is already active"}), 409
    threading.Thread(target=run_cycle, daemon=True).start()
    return jsonify({"ok": True, "mode": "live"})

@app.get("/status")
def status():
    with state_lock:
        return jsonify(json.loads(json.dumps(state)))

@app.get("/config")
def config():
    universe = load_universe(UNIVERSE_PATH)
    return jsonify({
        "brand": os.getenv("BRAND", "MarketPulse"),
        "confidence_threshold": int(os.getenv("CONFIDENCE_THRESHOLD", "7")),
        "agent_delay": float(os.getenv("AGENT_DELAY", "0.35")),
        "shortlist_per_bucket": int(os.getenv("SHORTLIST_PER_BUCKET", "4")),
        "port": int(os.getenv("PORT", "5000")),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "llm_provider": os.getenv("LLM_PROVIDER", "auto"),
        "universe": universe
    })

@app.post("/config")
def save_config():
    data = request.get_json(silent=True) or {}
    
    # 1. Save universe if present
    if "universe" in data:
        try:
            univ_data = data["universe"]
            if isinstance(univ_data, (dict, list)):
                UNIVERSE_PATH.write_text(json.dumps(univ_data, indent=2), encoding="utf-8")
        except Exception as e:
            return jsonify({"ok": False, "error": f"Failed to save universe.json: {str(e)}"}), 400
            
    # 2. Save .env config
    try:
        env_lines = []
        keys = [
            ("TELEGRAM_BOT_TOKEN", data.get("telegram_bot_token")),
            ("TELEGRAM_CHAT_ID", data.get("telegram_chat_id")),
            ("LLM_PROVIDER", data.get("llm_provider")),
            ("BRAND", data.get("brand")),
            ("CONFIDENCE_THRESHOLD", data.get("confidence_threshold")),
            ("AGENT_DELAY", data.get("agent_delay")),
            ("SHORTLIST_PER_BUCKET", data.get("shortlist_per_bucket")),
            ("PORT", data.get("port")),
            ("CLAUDE_MODEL", os.getenv("CLAUDE_MODEL", "haiku")),
        ]
        for key, val in keys:
            if val is not None:
                env_lines.append(f"{key}={val}")
            else:
                env_lines.append(f"{key}={os.getenv(key, '')}")
        ENV_PATH.write_text("\n".join(env_lines), encoding="utf-8")
        load_env(ENV_PATH, force=True)
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to write .env file: {str(e)}"}), 500
        
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"Local dashboard: http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
