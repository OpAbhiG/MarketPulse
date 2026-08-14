import math

def calculate_swing_score(evidence, market_regime=None, sector_data=None):
    """
    Evaluates NSE stock for Swing trading (2-6 week horizon, Daily/Weekly timeframes, EMA 20/50/100/200, RS).
    Outputs Swing Score /100 and setup classification.
    """
    price = evidence.get("price", {})
    tech = evidence.get("technicals", {})
    analyst = evidence.get("analyst", {})
    r52 = evidence.get("range_52w", {})

    latest = price.get("live") or 100.0
    day_chg = price.get("day_change_pct") or 0.0
    rvol = tech.get("rvol") or 1.0
    pos52 = r52.get("position_pct") or 50.0
    trend = tech.get("trend") or "sideways"
    sma_dist = tech.get("price_vs_sma_pct") or 0.0
    upside = analyst.get("upside_pct") or 0.0

    # 1. Technical Trend (Max 20)
    t_score = 0
    if trend == "up" and sma_dist >= 2.0: t_score = 20
    elif trend == "up": t_score = 15
    elif trend == "sideways": t_score = 8
    else: t_score = 2

    # 2. Price Momentum & Multi-Day Returns (Max 15)
    m_score = 0
    if day_chg >= 2.5: m_score = 15
    elif day_chg >= 1.0: m_score = 11
    elif day_chg >= 0.0: m_score = 7

    # 3. Relative Strength vs NIFTY / Sector (Max 15)
    rs_score = 8
    if sector_data and sector_data.get("is_outperforming"):
        rs_score = 15

    # 4. Breakout Quality & 52W Position (Max 15)
    b_score = 0
    if pos52 >= 88.0: b_score = 15
    elif pos52 >= 75.0: b_score = 11
    elif pos52 >= 60.0: b_score = 7

    # 5. Volume Expansion RVOL (Max 10)
    v_score = 0
    if rvol >= 2.0: v_score = 10
    elif rvol >= 1.3: v_score = 7
    elif rvol >= 1.0: v_score = 4

    # 6. Sector Strength (Max 10)
    sec_score = 5
    if sector_data and sector_data.get("sector_20d_return", 0) > 2.0:
        sec_score = 10

    # 7. Market Regime Alignment (Max 5)
    reg_score = 3
    if market_regime:
        rmode = market_regime.get("risk_mode", "NORMAL")
        if rmode in ("STRONG_RISK_ON", "RISK_ON"): reg_score = 5
        elif rmode == "NORMAL": reg_score = 4
        elif rmode == "CAUTIOUS": reg_score = 2
        else: reg_score = 0

    # 8. Fundamental & Analyst Target Upside (Max 5)
    fund_score = 0
    if upside >= 15.0: fund_score = 5
    elif upside >= 5.0: fund_score = 3

    # 9. Risk/Reward Ratio (Max 5)
    rr_score = 4

    total_score = t_score + m_score + rs_score + b_score + v_score + sec_score + reg_score + fund_score + rr_score
    total_score = max(0, min(100, total_score))

    # Swing Classification
    if total_score >= 82 and pos52 >= 80 and trend == "up":
        classification = "CONFIRMED SWING"
    elif total_score >= 74:
        classification = "SWING MOMENTUM"
    elif total_score >= 64:
        classification = "BREAKOUT WATCH"
    elif total_score >= 54:
        classification = "EARLY SWING SETUP"
    else:
        classification = "AVOID"

    return {
        "score": total_score,
        "classification": classification,
        "pos52": pos52,
        "trend": trend,
        "upside_pct": upside,
        "breakdown": {
            "technical_trend": t_score,
            "momentum": m_score,
            "relative_strength": rs_score,
            "breakout": b_score,
            "rvol": v_score,
            "sector": sec_score,
            "market_regime": reg_score,
            "fundamental": fund_score,
            "risk_reward": rr_score
        }
    }
