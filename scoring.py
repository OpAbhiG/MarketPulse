import math
from screening import calculate_boom_score
from risk_engine import calculate_risk_parameters
from signal_validator import validate_signal
from verifier import verify_llm_grounding

def clamp(val, min_val=0, max_val=100):
    return max(min_val, min(max_val, val))

def calculate_data_quality(evidence):
    """Calculates 0-100 Data Quality Score based on evidence data completeness."""
    gaps = evidence.get("data_gaps", [])
    total_checks = 12
    missing_count = len(gaps)
    quality = max(0, min(100, round(((total_checks - missing_count) / total_checks) * 100)))
    return quality

def deterministic_evaluate(evidence, market_regime=None, sector_data=None, config=None):
    """
    Evaluates evidence using MarketPulse scoring, BOOM scanning, Risk engine, and Signal validation.
    """
    symbol = evidence.get("symbol")
    p = evidence.get("price", {})
    t = evidence.get("technicals", {})
    a = evidence.get("analyst", {})
    r = evidence.get("range_52w", {})
    n = evidence.get("news", {})

    latest = p.get("live")
    day_chg = p.get("day_change_pct")
    rvol = t.get("rvol") or 1.0
    pos = r.get("position_pct")
    trend = t.get("trend") or "sideways"
    close = t.get("day_range_position_pct")
    sma = t.get("price_vs_sma_pct")
    upside = a.get("upside_pct")
    buy = a.get("buy_pct")
    sell = a.get("sell_pct")
    posnews = n.get("positive", 0)
    neg = n.get("negative", 0)
    total_news = n.get("total", 0)

    # 1. Bull & Bear conviction scoring (0-100)
    bull = 35.0
    bear = 25.0
    br = []
    rr = []

    if rvol >= 2.0: bull += 15; br.append(f"RVOL {rvol:.2f}x indicates institutional volume surge")
    elif rvol >= 1.2: bull += 8; br.append(f"RVOL {rvol:.2f}x is above average")
    elif rvol < 0.8: bear += 10; rr.append(f"RVOL {rvol:.2f}x is below average")

    if pos is not None and pos >= 75: bull += 14; br.append(f"52-week position {pos:.1f}% is in breakout territory")
    elif pos is not None and pos <= 30: bear += 12; rr.append(f"52-week position {pos:.1f}% shows structural weakness")

    if trend == "up": bull += 12; br.append("technical trend is bullish")
    elif trend == "down": bear += 12; rr.append("technical trend is bearish")

    if sma is not None and sma >= 2.0: bull += 8; br.append(f"price is {sma:.1f}% above 20-SMA")
    elif sma is not None and sma < 0: bear += 8; rr.append(f"price is {abs(sma):.1f}% below 20-SMA")

    if upside is not None and upside >= 10: bull += 10; br.append(f"analyst upside {upside:.1f}% is favorable")
    elif upside is not None and upside <= 0: bear += 8; rr.append(f"analyst upside {upside:.1f}% is absent")

    if posnews > neg and total_news: bull += 6; br.append("news tone is positive")
    elif neg > posnews and total_news: bear += 6; rr.append("news tone is negative")

    bull = clamp(bull)
    bear = clamp(bear)
    net = round(bull - bear, 1)

    # 2. MarketPulse Score /100
    tech_score = 25 if trend == "up" and (sma or 0) > 0 else 15
    mom_score = 20 if (day_chg or 0) > 1.0 else 12
    rvol_score = 15 if rvol >= 1.5 else 8
    fund_score = 15 if (upside or 0) > 10 else 8
    news_score = 10 if posnews >= neg else 5
    reg_score = 10 if market_regime and market_regime.get("risk_mode") == "RISK_ON" else 6
    risk_score = 5

    marketpulse_score = clamp(tech_score + mom_score + rvol_score + fund_score + news_score + reg_score + risk_score)

    # 3. BOOM Score & Classification
    boom_data = calculate_boom_score(evidence, market_regime, sector_data)
    boom_score = boom_data["score"]
    boom_type = boom_data["boom_type"]

    # 4. Verdict & AI Confidence
    has_boom = boom_score >= 70 or rvol >= 1.2 or (day_chg or 0) >= 0.3 or trend == "up"
    if (net >= 5 or has_boom) and (market_regime is None or market_regime.get("risk_mode") != "RISK_OFF"):
        verdict = "BUY"
    elif net <= -20:
        verdict = "AVOID"
    else:
        verdict = "WATCH"

    conf = max(1, min(10, round(6 + net / 12)))
    if verdict == "BUY": conf = max(7, conf)

    winner = "Bull" if bull >= bear else "Bear"
    rationale = br[0] if winner == "Bull" and br else rr[0] if rr else "Technical momentum and market factors evaluated."
    catalyst = br[1] if winner == "Bull" and len(br) > 1 else br[0] if br else "Positive analyst upside and momentum"

    # 5. Risk Engine Parameters
    risk_params = calculate_risk_parameters(evidence)

    # 6. Data Quality Score
    dq_score = calculate_data_quality(evidence)

    verdict_payload = {
        "symbol": symbol,
        "name": evidence.get("name"),
        "cap_segment": evidence.get("cap_segment"),
        "sector": evidence.get("sector"),
        "price": latest,
        "day_change_pct": day_chg,
        "verdict": verdict,
        "confidence": conf,
        "marketpulse_score": marketpulse_score,
        "boom_score": boom_score,
        "boom_type": boom_type,
        "breakout_quality": boom_data["breakout_quality"],
        "data_quality_score": dq_score,
        "winner": winner,
        "why": rationale,
        "catalyst": catalyst,
        "buy_zone": risk_params["buy_zone"],
        "target": risk_params["target_1_str"],
        "target_2": risk_params["target_2_str"],
        "stop_loss": risk_params["stop_loss_str"],
        "rr_ratio": risk_params["rr_ratio"],
        "invalidation": f"Daily close below {risk_params['stop_loss_str']}",
        "kill_conditions": [f"Daily close below {risk_params['stop_loss_str']}", "Market Regime switches to RISK_OFF"],
        "strategies": [boom_type] if boom_type != "NORMAL" else ["Momentum Watch"],
        "technicals": t,
        "range_52w": r,
        "analyst": a,
        "news": n,
        "risk_params": risk_params,
        "scores": {
            "bull": {"score": bull, "reasons": br[:4]},
            "bear": {"score": bear, "reasons": rr[:4]}
        }
    }

    # 7. Signal Validation Gate
    validation = validate_signal(verdict_payload, evidence, market_regime, config)
    verdict_payload["validated"] = validation["validated"]
    verdict_payload["validation_status"] = validation["status"]
    verdict_payload["validation_reason"] = validation["reason"]

    if not validation["validated"] and verdict_payload["verdict"] == "BUY":
        verdict_payload["verdict"] = "WATCH"

    return verdict_payload
