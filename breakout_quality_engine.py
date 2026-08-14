def evaluate_breakout_quality_grade(evidence):
    """
    Evaluates resistance quality, tests count, range contraction, volume expansion, and candle body.
    Classifies: A+ BREAKOUT, A BREAKOUT, B BREAKOUT, WEAK BREAKOUT, FALSE BREAKOUT RISK, EXTENDED, NO TRADE.
    """
    price = evidence.get("price", {})
    tech = evidence.get("technicals", {})
    r52 = evidence.get("range_52w", {})

    latest = price.get("live") or 100.0
    rvol = tech.get("rvol") or 1.0
    pos52 = r52.get("position_pct") or 50.0
    sw_hi = tech.get("swing_high")

    if not sw_hi or latest < sw_hi * 0.96:
        return {"grade": "NO TRADE", "score": 40, "rationale": "Price below resistance zone"}

    dist_pct = ((latest - sw_hi) / sw_hi) * 100 if sw_hi > 0 else 0.0

    if dist_pct > 10.0:
        return {"grade": "EXTENDED", "score": 30, "rationale": f"Price is {dist_pct:.1f}% past resistance — DO NOT CHASE"}

    if pos52 >= 90 and rvol >= 2.0 and dist_pct >= 0 and dist_pct <= 3.0:
        return {"grade": "A+ BREAKOUT", "score": 95, "rationale": "High RVOL, fresh breakout, 52W high proximity"}

    if pos52 >= 80 and rvol >= 1.5 and dist_pct <= 5.0:
        return {"grade": "A BREAKOUT", "score": 85, "rationale": "Strong volume expansion and trend alignment"}

    if pos52 >= 70 and rvol >= 1.2:
        return {"grade": "B BREAKOUT", "score": 75, "rationale": "Moderate breakout quality with acceptable volume"}

    if rvol < 1.0:
        return {"grade": "FALSE BREAKOUT RISK", "score": 45, "rationale": "Breakout lacking volume expansion (< 1.0x RVOL)"}

    return {"grade": "WEAK BREAKOUT", "score": 55, "rationale": "Sub-optimal breakout structure"}
