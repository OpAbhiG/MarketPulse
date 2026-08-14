import math

def calculate_boom_score(evidence, market_regime=None, sector_data=None):
    """
    Calculates a 0-100 BOOM Score based on 7 factors:
    - Price Momentum (20)
    - Relative Volume (20)
    - Breakout Strength (20)
    - Trend Alignment (15)
    - Intraday Strength (10)
    - Sector Strength (10)
    - Market Regime (5)
    """
    price = evidence.get("price", {})
    tech = evidence.get("technicals", {})
    r52 = evidence.get("range_52w", {})

    day_chg = price.get("day_change_pct") or 0.0
    rvol = tech.get("rvol") or 1.0
    pos52 = r52.get("position_pct") or 50.0
    trend = tech.get("trend") or "sideways"
    close_pos = tech.get("day_range_position_pct") or 50.0
    sma_dist = tech.get("price_vs_sma_pct") or 0.0

    # 1. Price Momentum (Max 20)
    p_score = 0
    if day_chg >= 5.0: p_score = 20
    elif day_chg >= 3.0: p_score = 16
    elif day_chg >= 1.5: p_score = 12
    elif day_chg >= 0.5: p_score = 8
    elif day_chg >= 0.0: p_score = 4

    # 2. Relative Volume (Max 20)
    v_score = 0
    if rvol >= 3.0: v_score = 20
    elif rvol >= 2.0: v_score = 16
    elif rvol >= 1.4: v_score = 12
    elif rvol >= 1.1: v_score = 8
    elif rvol >= 0.9: v_score = 4

    # 3. Breakout Strength (Max 20)
    b_score = 0
    if pos52 >= 90.0: b_score = 20
    elif pos52 >= 80.0: b_score = 16
    elif pos52 >= 70.0: b_score = 12
    elif pos52 >= 60.0: b_score = 8
    else: b_score = 4

    # 4. Trend Alignment (Max 15)
    t_score = 0
    if trend == "up" and sma_dist >= 2.0: t_score = 15
    elif trend == "up": t_score = 10
    elif trend == "sideways": t_score = 5

    # 5. Intraday Strength (Max 10)
    i_score = 0
    if close_pos >= 80.0: i_score = 10
    elif close_pos >= 60.0: i_score = 7
    elif close_pos >= 40.0: i_score = 4

    # 6. Sector Strength (Max 10)
    sec_score = 7
    if sector_data and sector_data.get("is_outperforming"):
        sec_score = 10

    # 7. Market Regime (Max 5)
    reg_score = 3
    if market_regime:
        rmode = market_regime.get("risk_mode", "NORMAL")
        if rmode == "RISK_ON": reg_score = 5
        elif rmode == "NORMAL": reg_score = 4
        elif rmode == "CAUTIOUS": reg_score = 2
        else: reg_score = 0

    total_boom = p_score + v_score + b_score + t_score + i_score + sec_score + reg_score
    total_boom = max(0, min(100, total_boom))

    # Classification
    if total_boom >= 90:
        classification = "BOOM+"
    elif total_boom >= 80:
        classification = "BOOM"
    elif total_boom >= 70:
        classification = "STRONG MOMENTUM"
    elif total_boom >= 60:
        classification = "MOMENTUM WATCH"
    else:
        classification = "NORMAL"

    # Determine 3 BOOM Types
    boom_type = "NORMAL"
    if pos52 >= 85 and rvol >= 1.5 and day_chg >= 1.0:
        boom_type = "CONFIRMED BREAKOUT"
    elif rvol >= 1.2 and day_chg >= 0.5 and trend == "up":
        boom_type = "BOOM MOMENTUM"
    elif pos52 >= 70 and rvol >= 1.1:
        boom_type = "EARLY BOOM"

    # Evaluate Breakout Quality
    swing_hi = tech.get("swing_high")
    latest = price.get("live")
    breakout_quality = "NO BREAKOUT"
    if swing_hi and latest:
        if latest > swing_hi and rvol >= 1.5:
            breakout_quality = "CONFIRMED BREAKOUT"
        elif latest > swing_hi:
            breakout_quality = "BREAKOUT"
        elif latest >= swing_hi * 0.98:
            breakout_quality = "APPROACHING BREAKOUT"

    return {
        "score": total_boom,
        "classification": classification,
        "boom_type": boom_type,
        "breakout_quality": breakout_quality,
        "breakdown": {
            "price_momentum": p_score,
            "relative_volume": v_score,
            "breakout_strength": b_score,
            "trend_alignment": t_score,
            "intraday_strength": i_score,
            "sector_strength": sec_score,
            "market_regime": reg_score
        }
    }
