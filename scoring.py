import math


def clamp(x, lo=0, hi=100): return max(lo, min(hi, x))
def pct(e, path):
    cur=e
    for p in path:
        cur=cur.get(p) if isinstance(cur,dict) else None
    return cur


def deterministic_evaluate(e):
    t=e.get("technicals",{}); p=e.get("price",{}); r=e.get("range_52w",{}); a=e.get("analyst",{}); n=e.get("news",{})
    bull=20; bear=20; br=[]; rr=[]
    rvol=t.get("rvol"); pos=r.get("position_pct"); sma=t.get("price_vs_sma_pct"); trend=t.get("trend")
    close=t.get("day_range_position_pct"); upside=a.get("upside_pct"); buy=a.get("buy_pct"); sell=a.get("sell_pct")
    neg=n.get("negative") or 0; posnews=n.get("positive") or 0; total=n.get("total") or 0; wr=t.get("window_return_pct")
    if rvol is not None:
        bull += min(20, max(0,(rvol-1)*8)); bear += min(12, max(0,(1-rvol)*12))
        if rvol >= 2: br.append(f"RVOL {rvol:.2f} supports participation")
        if rvol < 1: rr.append(f"RVOL {rvol:.2f} is below average")
    if pos is not None:
        if pos >= 85: bull += 18; br.append(f"52-week position {pos:.1f}% is strong")
        elif pos < 30: bear += 18; rr.append(f"52-week position {pos:.1f}% is weak")
    if sma is not None and trend == "up": bull += 12; br.append(f"price is {sma:.1f}% above SMA")
    elif sma is not None and (sma < 0 or trend == "down"): bear += 12; rr.append(f"price is {sma:.1f}% versus SMA")
    if close is not None:
        if close >= 70: bull += 8; br.append(f"day range close {close:.1f}% is firm")
        elif close <= 30: bear += 8; rr.append(f"day range close {close:.1f}% is weak")
    if upside is not None and upside >= 10: bull += 10; br.append(f"analyst upside {upside:.1f}% is favorable")
    elif upside is not None and upside <= 0: bear += 10; rr.append(f"analyst upside {upside:.1f}% is absent")
    if buy is not None and buy >= 80: bull += 8; br.append(f"analyst buy share {buy:.1f}% is high")
    elif buy is not None and buy < 55: bear += 8; rr.append(f"analyst buy share {buy:.1f}% is low")
    if sell is not None and sell >= 25: bear += 8; rr.append(f"analyst sell share {sell:.1f}% is elevated")
    if posnews > neg and total: bull += 6; br.append("news tone is positive")
    elif neg > posnews and total: bear += 6; rr.append("news tone is negative")
    if wr is not None and wr > 0: bull += 8; br.append(f"window return {wr:.1f}% is positive")
    elif wr is not None and wr < 0: bear += 8; rr.append(f"window return {wr:.1f}% is negative")
    if r.get("pct_from_high") is not None and r["pct_from_high"] <= -20: bear += 8; rr.append(f"stock is {r['pct_from_high']:.1f}% from 52-week high")
    bull=round(clamp(bull),1); bear=round(clamp(bear),1); net=round(bull-bear,1)
    leadership=(pos is not None and pos>=60) or (rvol is not None and rvol>=3)
    if net >= 25 and leadership: verdict="BUY"
    elif net <= -15: verdict="AVOID"
    else: verdict="WATCH"
    conf=max(1,min(10,round(4+net/15)))
    if verdict=="BUY": conf=max(7,conf)
    else: conf=min(6,conf)
    winner="Bull" if bull>=bear else "Bear"
    rationale=(br[0] if winner=="Bull" and br else rr[0] if rr else "Evidence is mixed; confirmation is limited.")
    catalyst=(br[1] if winner=="Bull" and len(br)>1 else br[0] if br else "data unavailable")
    
    latest = p.get("live")
    day_chg = p.get("day_change_pct")
    buy_zone = None
    target = None
    stop_loss = None
    if verdict == "BUY" and latest is not None:
        buy_zone = f"₹{latest:.2f} - ₹{latest*1.015:.2f}"
        sw_low = t.get("swing_low")
        if sw_low is not None and sw_low < latest and sw_low > latest * 0.85:
            stop_loss = f"₹{sw_low:.2f}"
        else:
            stop_loss = f"₹{latest * 0.92:.2f} (8% SL)"
        t_mean = a.get("target_mean")
        if t_mean is not None and t_mean > latest:
            target = f"₹{t_mean:.2f}"
        else:
            target = f"₹{latest * 1.15:.2f} (15% Target)"

    # Identify matching NSE strategies
    strategies = []
    if verdict == "BUY" and conf >= 8:
        strategies.append("Strong Buy")
    if rvol is not None and rvol >= 1.4 and (day_chg is None or day_chg >= 1.0) and (close is None or close >= 65):
        strategies.append("BOOM Momentum")
    if pos is not None and pos >= 88:
        strategies.append("52W High Breakout")
    if pos is not None and pos <= 40 and upside is not None and upside >= 12 and (rvol is None or rvol >= 1.1):
        strategies.append("Value Reversal")
            
    scores={
      "bull":{"score":bull,"reasons":br[:4]}, "bear":{"score":bear,"reasons":rr[:4]},
      "fundamentalist":{"score":round(clamp((50+(upside or 0)*1.5)),1),"reasons":br[:2] if upside is not None else ["data unavailable"]},
      "technician":{"score":round(clamp(50+(sma or 0)*1.2+(rvol or 1)*5),1),"reasons":br[:2] if sma is not None else ["data unavailable"]},
      "newsdesk":{"score":round(clamp(50+((posnews-neg)*8)),1),"reasons":["positive news" if posnews>neg else "negative news" if neg>posnews else "mixed news"]},
    }
    return {"scores":scores,"verdict":{"winner":winner,"verdict":verdict,"confidence":conf,"rationale":rationale,"key_catalyst":catalyst,"bull_score":bull,"bear_score":bear,"net":net,"buy_zone":buy_zone,"target":target,"stop_loss":stop_loss,"strategies":strategies},"verifier_ok":True}

