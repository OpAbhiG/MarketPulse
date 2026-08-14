def rank_market_opportunities(verdicts_list, min_conviction_threshold=75):
    """
    Ranks candidates across Intraday and Swing categories.
    Enforces No-Forced-Signal Policy & No Contradictory UI State:
    - top_pick is ONLY set if candidate decision_state == 'BUY NOW'.
    - If buy_now candidates = 0, top_pick is None and summary is 'NO HIGH-CONVICTION BUY TODAY'.
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

    # Count decisions
    buy_now_list = [v for v in verdicts_list if v.get("decision_state") == "BUY NOW"]
    confirmation_list = [v for v in verdicts_list if v.get("decision_state") == "BUY ON CONFIRMATION"]
    watch_list = [v for v in verdicts_list if v.get("decision_state") == "WATCH"]
    avoid_list = [v for v in verdicts_list if v.get("decision_state") == "AVOID"]
    blocked_list = [v for v in verdicts_list if v.get("decision_state") == "BLOCKED"]

    # Filter Intraday candidates
    intraday_candidates = [
        v for v in verdicts_list 
        if (v.get("intraday_score", 0) >= min_conviction_threshold) and not v.get("is_too_extended")
    ]
    intraday_candidates.sort(key=lambda x: x.get("intraday_score", 0), reverse=True)

    # Filter Swing candidates
    swing_candidates = [
        v for v in verdicts_list 
        if (v.get("swing_score", 0) >= min_conviction_threshold) and not v.get("is_too_extended")
    ]
    swing_candidates.sort(key=lambda x: x.get("swing_score", 0), reverse=True)

    # Only assign top pick if buy_now exists
    top_intraday = intraday_candidates[0] if (intraday_candidates and intraday_candidates[0].get("decision_state") == "BUY NOW") else None
    top_swing = swing_candidates[0] if (swing_candidates and swing_candidates[0].get("decision_state") == "BUY NOW") else None

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
        "buy_now_count": len(buy_now_list),
        "confirmation_count": len(confirmation_list),
        "watch_count": len(watch_list),
        "avoid_count": len(avoid_list),
        "blocked_count": len(blocked_list),
        "has_opportunity": has_buy_now,
        "opportunities_summary": f"{len(buy_now_list)} BUY NOW setup(s) active" if has_buy_now else "NO HIGH-CONVICTION BUY TODAY"
    }
