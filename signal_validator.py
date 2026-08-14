def validate_signal(verdict_data, evidence, market_regime=None, config=None):
    """
    Evaluates 8 validation gates before approving a BUY signal.
    If any check fails, returns BUY BLOCKED with exact reason.
    """
    cfg = config or {}
    min_confidence = cfg.get("CONFIDENCE_THRESHOLD", 7)
    min_score = cfg.get("MIN_SIGNAL_SCORE", 75)
    min_rr = cfg.get("MIN_RR", 1.5)
    min_data_quality = cfg.get("MIN_DATA_QUALITY", 75)

    verdict = verdict_data.get("verdict")
    conf = verdict_data.get("confidence", 0)
    mp_score = verdict_data.get("marketpulse_score", 0)
    rr = verdict_data.get("rr_ratio", 0.0)
    data_quality = verdict_data.get("data_quality_score", 100)

    blocks = []

    # Gate 1: Verdict must be BUY
    if verdict != "BUY":
        blocks.append(f"Verdict is '{verdict}', not 'BUY'")

    # Gate 2: Confidence threshold
    if conf < min_confidence:
        blocks.append(f"AI Confidence {conf}/10 is below required threshold ({min_confidence}/10)")

    # Gate 3: MarketPulse Score threshold
    if mp_score < min_score:
        blocks.append(f"MarketPulse Score {mp_score}/100 is below minimum threshold ({min_score}/100)")

    # Gate 4: Risk/Reward threshold
    if rr < min_rr:
        blocks.append(f"Risk/Reward ratio {rr}:1 is below required {min_rr}:1")

    # Gate 5: Data Quality threshold
    if data_quality < min_data_quality:
        blocks.append(f"Data Quality Score {data_quality}/100 is below minimum ({min_data_quality}/100)")

    # Gate 6: Market Regime check
    if market_regime and market_regime.get("risk_mode") == "RISK_OFF":
        blocks.append("Market Regime is RISK_OFF (NIFTY market broad crash risk)")

    # Gate 7: Liquidity check (Minimum 50,000 daily volume)
    vol = evidence.get("price", {}).get("volume") or 0
    if vol > 0 and vol < 50000:
        blocks.append(f"Low trading volume ({vol:,} shares) fails liquidity requirement")

    # Gate 8: Data gaps check
    data_gaps = evidence.get("data_gaps", [])
    if "price.live" in data_gaps:
        blocks.append("Stale or missing live price data")

    validated = len(blocks) == 0
    return {
        "validated": validated,
        "status": "BUY" if validated else "BUY BLOCKED",
        "blocks": blocks,
        "reason": "Passed all 8 validation checks" if validated else " | ".join(blocks)
    }
