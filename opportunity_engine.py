from intraday_engine import calculate_intraday_score
from swing_engine import calculate_swing_score
from false_breakout_engine import evaluate_breakout_extension_and_validity

def rank_market_opportunities(verdicts_list, min_conviction_threshold=75):
    """
    Ranks candidates across Intraday and Swing categories.
    Enforces No-Forced-Signal Policy: returns 'NO HIGH-CONVICTION SETUP' if no candidate qualifies.
    """
    if not verdicts_list:
        return {
            "top_intraday": None,
            "top_swing": None,
            "top_boom": None,
            "best_rr": None,
            "safest_setup": None,
            "opportunities_summary": "NO HIGH-CONVICTION SETUP"
        }

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

    top_intraday = intraday_candidates[0] if intraday_candidates else None
    top_swing = swing_candidates[0] if swing_candidates else None

    top_boom = max(verdicts_list, key=lambda x: x.get("boom_score", 0)) if verdicts_list else None
    best_rr = max(verdicts_list, key=lambda x: x.get("rr_ratio", 0)) if verdicts_list else None
    safest = max(verdicts_list, key=lambda x: x.get("data_quality_score", 0)) if verdicts_list else None

    has_valid_opportunity = (top_intraday is not None) or (top_swing is not None)

    return {
        "top_intraday": top_intraday,
        "top_swing": top_swing,
        "top_boom": top_boom,
        "best_rr": best_rr,
        "safest_setup": safest,
        "has_opportunity": has_valid_opportunity,
        "opportunities_summary": "High conviction setups available" if has_valid_opportunity else "NO HIGH-CONVICTION SETUP"
    }
