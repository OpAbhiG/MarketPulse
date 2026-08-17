from calibration_engine import get_calibrated_win_probability

def calculate_expected_value(v, fee_pct=0.15, slippage_pct=0.10):
    """
    Calculates Expected Value (EV) for a candidate:
    EV = [P(win) * avg_win] - [P(loss) * avg_loss] - fees - slippage
    """
    score = v.get("marketpulse_score", 50)
    p_win = get_calibrated_win_probability(score)
    p_loss = 1.0 - p_win

    rr = v.get("rr_ratio", 1.5)
    avg_win = rr * 4.0  # Assumed 4% base risk unit
    avg_loss = 4.0

    ev = (p_win * avg_win) - (p_loss * avg_loss) - (fee_pct * 2) - slippage_pct
    return round(ev, 2)

def rank_market_opportunities(verdicts_list, min_conviction_threshold=75):
    """
    Ranks candidates across Intraday and Swing categories based on Expected Value (EV).
    Enforces No-Forced-Signal Policy & EV Optimization.
    """
    if not verdicts_list:
        return {
            "top_intraday": None,
            "top_swing": None,
            "top_boom": None,
            "best_rr": None,
            "safest_setup": None,
            "buy_now_count": 0,
            "confirmation_count": 0,
            "watch_count": 0,
            "avoid_count": 0,
            "blocked_count": 0,
            "opportunities_summary": "NO HIGH-CONVICTION BUY TODAY"
        }

    # Attach EV to every candidate
    for v in verdicts_list:
        v["expected_value"] = calculate_expected_value(v)
        v["opportunity_quality_score"] = round((v.get("marketpulse_score", 50) * 0.6) + (max(0, v["expected_value"]) * 8.0), 1)

    buy_now_list = [v for v in verdicts_list if v.get("decision_state") == "BUY NOW"]
    confirmation_list = [v for v in verdicts_list if v.get("decision_state") == "BUY ON CONFIRMATION"]
    watch_list = [v for v in verdicts_list if v.get("decision_state") == "WATCH"]
    avoid_list = [v for v in verdicts_list if v.get("decision_state") == "AVOID"]
    blocked_list = [v for v in verdicts_list if v.get("decision_state") == "BLOCKED"]

    # Filter & Sort Intraday candidates by EV
    intraday_candidates = [
        v for v in verdicts_list 
        if (v.get("intraday_score", 0) >= min_conviction_threshold) and not v.get("is_too_extended")
    ]
    intraday_candidates.sort(key=lambda x: (x.get("expected_value", 0), x.get("intraday_score", 0)), reverse=True)

    # Filter & Sort Swing candidates by EV
    swing_candidates = [
        v for v in verdicts_list 
        if (v.get("swing_score", 0) >= min_conviction_threshold) and not v.get("is_too_extended")
    ]
    swing_candidates.sort(key=lambda x: (x.get("expected_value", 0), x.get("swing_score", 0)), reverse=True)

    top_intraday = intraday_candidates[0] if (intraday_candidates and intraday_candidates[0].get("decision_state") == "BUY NOW") else None
    top_swing = swing_candidates[0] if (swing_candidates and swing_candidates[0].get("decision_state") == "BUY NOW") else None

    # Best Pick Overall (Highest Master Score / EV setup that is not AVOID)
    eligible = [v for v in verdicts_list if v.get("decision_state") not in ("AVOID", "BLOCKED")]
    if eligible:
        eligible.sort(key=lambda x: (x.get("marketpulse_score", 0), x.get("expected_value", 0)), reverse=True)
        best_pick = eligible[0]
    else:
        best_pick = max(verdicts_list, key=lambda x: x.get("marketpulse_score", 0)) if verdicts_list else None

    # Budget Stocks (Priced under ₹500, non-AVOID, sorted by Master Score)
    budget_candidates = [
        v for v in verdicts_list 
        if (v.get("price") or 9999) <= 500 and v.get("decision_state") != "AVOID"
    ]
    top_boom = max(verdicts_list, key=lambda x: x.get("boom_score", 0)) if verdicts_list else None
    best_rr = max(verdicts_list, key=lambda x: x.get("rr_ratio", 0)) if verdicts_list else None
    safest = max(verdicts_list, key=lambda x: x.get("data_quality_score", 0)) if verdicts_list else None

    has_buy_now = len(buy_now_list) > 0

    return {
        "top_intraday": top_intraday,
        "top_swing": top_swing,
        "top_boom": top_boom,
        "best_rr": best_rr,
        "safest_setup": safest,
        "best_pick": best_pick,
        "budget_stocks": budget_candidates,
        "buy_now_count": len(buy_now_list),
        "confirmation_count": len(confirmation_list),
        "watch_count": len(watch_list),
        "avoid_count": len(avoid_list),
        "blocked_count": len(blocked_list),
        "has_opportunity": has_buy_now,
        "opportunities_summary": f"{len(buy_now_list)} BUY NOW setup(s) active" if has_buy_now else "NO HIGH-CONVICTION BUY TODAY"
    }



