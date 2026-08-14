import math
from datetime import datetime

def calculate_time_of_day_rvol(raw_rvol):
    """
    Scales RVOL based on elapsed trading minutes in the NSE session (9:15 to 15:30 IST = 375 mins).
    Prevents morning volume distortion.
    """
    now = datetime.now()
    market_start_mins = 9 * 60 + 15  # 9:15 AM
    curr_mins = now.hour * 60 + now.minute
    
    elapsed = max(15, min(375, curr_mins - market_start_mins)) if (curr_mins >= market_start_mins) else 375
    time_factor = round(elapsed / 375.0, 2)

    # Time-adjusted expected volume scaling
    tod_rvol = round(raw_rvol / max(0.2, time_factor), 2) if time_factor < 1.0 else raw_rvol
    return max(0.5, tod_rvol)

def calculate_intraday_score(evidence, market_regime=None, sector_data=None):
    """
    Evaluates NSE stock for Intraday trading (5m primary timeframe, VWAP, EMA 9/20/50, Opening Range).
    Outputs Intraday Score /100 and setup classification.
    """
    price = evidence.get("price", {})
    tech = evidence.get("technicals", {})

    latest = price.get("live") or 100.0
    day_chg = price.get("day_change_pct") or 0.0
    raw_rvol = tech.get("rvol") or 1.0
    tod_rvol = calculate_time_of_day_rvol(raw_rvol)

    close_pos = tech.get("day_range_position_pct") or 50.0
    trend = tech.get("trend") or "sideways"
    sma_dist = tech.get("price_vs_sma_pct") or 0.0

    vwap = tech.get("vwap") or (latest * 0.995)
    ema9 = tech.get("ema9") or (latest * 0.998)
    ema20 = tech.get("ema20") or (latest * 0.992)
    ema50 = tech.get("ema50") or (latest * 0.985)
    rsi = tech.get("rsi") or 58.0
    vol_accel = tech.get("vol_accel") or 1.25

    # 1. Intraday Price Momentum (Max 20)
    p_score = 0
    if day_chg >= 3.5: p_score = 20
    elif day_chg >= 2.0: p_score = 16
    elif day_chg >= 1.0: p_score = 12
    elif day_chg >= 0.3: p_score = 8
    elif day_chg >= 0.0: p_score = 4

    # 2. Time-of-Day Adjusted RVOL (Max 20)
    v_score = 0
    if tod_rvol >= 2.5: v_score = 20
    elif tod_rvol >= 1.8: v_score = 16
    elif tod_rvol >= 1.2: v_score = 12
    elif tod_rvol >= 0.9: v_score = 8
    else: v_score = 4

    # 3. VWAP & Short Trend Alignment (Max 15)
    vwap_score = 0
    if latest >= vwap and latest >= ema9 and ema9 >= ema20:
        vwap_score = 15
    elif latest >= vwap:
        vwap_score = 10
    elif latest >= ema20:
        vwap_score = 5

    # 4. Opening Range & Breakout (Max 15)
    b_score = 0
    if close_pos >= 85.0: b_score = 15
    elif close_pos >= 70.0: b_score = 11
    elif close_pos >= 50.0: b_score = 7

    # 5. Volume Acceleration (Max 10)
    accel_score = 0
    if vol_accel >= 1.5: accel_score = 10
    elif vol_accel >= 1.1: accel_score = 7
    elif vol_accel >= 0.9: accel_score = 4

    # 6. Relative Strength vs Sector (Max 10)
    rs_score = 6
    if sector_data and sector_data.get("is_outperforming"):
        rs_score = 10

    # 7. Sector Strength (Max 5)
    sec_score = 3
    if sector_data and sector_data.get("sector_20d_return", 0) > 1.0:
        sec_score = 5

    # 8. Market Regime Alignment (Max 5)
    reg_score = 3
    if market_regime:
        rmode = market_regime.get("risk_mode", "NORMAL")
        if rmode in ("STRONG_RISK_ON", "RISK_ON"): reg_score = 5
        elif rmode == "NORMAL": reg_score = 4
        elif rmode == "CAUTIOUS": reg_score = 2
        else: reg_score = 0

    total_score = p_score + v_score + vwap_score + b_score + accel_score + rs_score + sec_score + reg_score
    total_score = max(0, min(100, total_score))

    # Intraday Classification
    if total_score >= 85 and tod_rvol >= 1.5 and latest >= vwap:
        classification = "CONFIRMED INTRADAY"
    elif total_score >= 75 and tod_rvol >= 1.2:
        classification = "BREAKOUT WATCH"
    elif total_score >= 65:
        classification = "MOMENTUM SETUP"
    elif total_score >= 55:
        classification = "EARLY MOMENTUM"
    else:
        classification = "AVOID"

    return {
        "score": total_score,
        "classification": classification,
        "vwap": round(vwap, 2),
        "ema9": round(ema9, 2),
        "ema20": round(ema20, 2),
        "rsi": round(rsi, 1),
        "rvol": round(tod_rvol, 2),
        "raw_rvol": round(raw_rvol, 2),
        "tod_rvol": round(tod_rvol, 2),
        "vol_accel": round(vol_accel, 2),
        "breakdown": {
            "momentum": p_score,
            "rvol": v_score,
            "vwap_trend": vwap_score,
            "breakout": b_score,
            "vol_accel": accel_score,
            "relative_strength": rs_score,
            "sector": sec_score,
            "market_regime": reg_score
        }
    }
