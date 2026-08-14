def evaluate_breakout_extension_and_validity(evidence):
    """
    Evaluates breakout extension distance and false-breakout risks.
    Classifications:
    - Extension: FRESH BREAKOUT, HEALTHY MOMENTUM, EXTENDED, SEVERELY EXTENDED
    - Validity: CONFIRMED, QUESTIONABLE, FALSE BREAKOUT RISK
    """
    price = evidence.get("price", {})
    tech = evidence.get("technicals", {})
    r52 = evidence.get("range_52w", {})

    latest = price.get("live")
    high = price.get("day_high")
    low = price.get("day_low")
    op = price.get("day_open")
    rvol = tech.get("rvol") or 1.0
    sw_hi = tech.get("swing_high")
    pos52 = r52.get("position_pct") or 50.0

    if not latest or not sw_hi:
        return {
            "extension_status": "FRESH BREAKOUT",
            "extension_pct": 0.0,
            "is_too_extended": False,
            "breakout_validity": "CONFIRMED",
            "false_breakout_risk": False
        }

    # 1. Extension Percentage beyond Swing High
    dist_pct = ((latest - sw_hi) / sw_hi) * 100 if sw_hi > 0 else 0.0

    if dist_pct > 12.0:
        extension_status = "SEVERELY EXTENDED"
        is_too_extended = True
    elif dist_pct > 8.0:
        extension_status = "EXTENDED"
        is_too_extended = True
    elif dist_pct > 2.0:
        extension_status = "HEALTHY MOMENTUM"
        is_too_extended = False
    else:
        extension_status = "FRESH BREAKOUT"
        is_too_extended = False

    # 2. Upper Wick & Rejection Calculation
    upper_wick_ratio = 0.0
    if high and low and high > low:
        upper_wick = high - max(op or latest, latest)
        candle_range = high - low
        upper_wick_ratio = upper_wick / candle_range

    false_risk = False
    validity = "CONFIRMED"

    if upper_wick_ratio >= 0.40 and dist_pct >= 0:
        validity = "FALSE BREAKOUT RISK"
        false_risk = True
    elif rvol < 1.0 and dist_pct > 0:
        validity = "QUESTIONABLE"

    return {
        "extension_status": extension_status,
        "extension_pct": round(dist_pct, 2),
        "is_too_extended": is_too_extended,
        "breakout_validity": validity,
        "false_breakout_risk": false_risk,
        "upper_wick_ratio": round(upper_wick_ratio, 2)
    }
