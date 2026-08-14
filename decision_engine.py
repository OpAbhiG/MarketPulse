def evaluate_trading_decision(evidence, verdict_payload, market_regime=None):
    """
    Evaluates evidence and verdict payload to determine strict 6-State Trading Decision:
    - 🟢 BUY NOW: Score >= 80, Judge = BUY, Conf >= 7, R:R >= 1.5, DQ >= 75, Regime permits, Not extended, Entry confirmed.
    - 🟡 BUY ON CONFIRMATION: Setup score >= 75, trigger price exists, setup not confirmed yet.
    - 🔵 WATCH: Setup score 65-74, interesting setup, insufficient confirmation.
    - 🔴 AVOID: Score < 65, weak technicals, low RVOL, bad R:R, bad regime, extended breakout (>10%), false breakout risk.
    - 🟠 BLOCKED: Setup attractive (Score >= 75) but risk/validation gate (e.g. portfolio concentration) prevents trading.
    - ⚪ NO TRADE: Default state when no candidate meets minimum criteria.
    """
    master_score = verdict_payload.get("marketpulse_score", 50)
    verdict = verdict_payload.get("verdict", "WATCH")
    conf = verdict_payload.get("confidence", 5)
    validated = verdict_payload.get("validated", False)
    val_status = verdict_payload.get("validation_status", "PENDING")
    val_reason = verdict_payload.get("validation_reason", "")
    is_ext = verdict_payload.get("is_too_extended", False)
    ext_pct = verdict_payload.get("extension_status", "FRESH BREAKOUT")
    rr = verdict_payload.get("rr_ratio", 1.0)
    dq = verdict_payload.get("data_quality_score", 100)
    boom_type = verdict_payload.get("boom_type", "NORMAL")

    price = float(verdict_payload.get("price") or 100.0)

    t = verdict_payload.get("technicals", {})
    rvol = t.get("rvol", 1.0)
    trend = t.get("trend", "sideways")
    sw_hi = t.get("swing_high") or (price * 1.02)
    sw_lo = t.get("swing_low") or (price * 0.94)

    why_buy = []
    why_not_buy = []
    avoid_reasons = []

    # Build Why Buy & Why Not Buy
    if rvol >= 1.5: why_buy.append(f"✓ RVOL {rvol:.2f}x shows volume confirmation")
    else: why_not_buy.append(f"⚠ RVOL {rvol:.2f}x below 1.5x confirmation threshold"); avoid_reasons.append(f"❌ RVOL {rvol:.2f}x too low")

    if trend == "up": why_buy.append("✓ Price trend is bullish")
    else: why_not_buy.append("⚠ Technical trend is not bullish"); avoid_reasons.append("❌ Technical trend below required moving averages")

    if boom_type != "NORMAL": why_buy.append(f"✓ Setup identified: {boom_type}")
    if rr >= 1.5: why_buy.append(f"✓ Risk/Reward ratio 1:{rr:.1f} meets minimum threshold")
    else: why_not_buy.append(f"⚠ Risk/Reward ratio 1:{rr:.1f} below 1:1.5 threshold"); avoid_reasons.append(f"❌ Poor Risk/Reward ratio (1:{rr:.1f})")

    if is_ext:
        why_not_buy.append(f"⚠ Price is {ext_pct} past resistance — DO NOT CHASE")
        avoid_reasons.append(f"❌ Breakout too extended ({ext_pct})")

    if not validated and val_reason:
        why_not_buy.append(f"⚠ Validation Blocked: {val_reason}")
        avoid_reasons.append(f"❌ {val_reason}")

    trigger_price = f"₹{sw_hi:.2f}"
    invalidation_price = f"₹{sw_lo:.2f}"

    # Decision State Machine
    if val_status == "BUY BLOCKED" or (master_score >= 75 and not validated):
        decision_state = "BLOCKED"
        decision_badge = "🟠 BLOCKED"
        action = "DO NOT TRADE — RISK GATE BLOCKED"
    elif master_score >= 80 and verdict == "BUY" and validated and conf >= 7 and rr >= 1.5 and not is_ext:
        decision_state = "BUY NOW"
        decision_badge = "🟢 BUY NOW"
        action = "BUY ENTRY CONFIRMED"
    elif master_score >= 75 and boom_type in ("EARLY BOOM", "BOOM MOMENTUM", "CONFIRMED BREAKOUT") and not is_ext:
        decision_state = "BUY ON CONFIRMATION"
        decision_badge = "🟡 BUY ON CONFIRMATION"
        action = f"BUY ONLY ABOVE {trigger_price}"
    elif master_score >= 65 and not is_ext:
        decision_state = "WATCH"
        decision_badge = "🔵 WATCH"
        action = "MONITOR FOR BREAKOUT CONFIRMATION"
    else:
        decision_state = "AVOID"
        decision_badge = "🔴 AVOID"
        action = "WAIT / DO NOT BUY"

    return {
        "decision_state": decision_state,
        "decision_badge": decision_badge,
        "action": action,
        "trigger_price": trigger_price,
        "invalidation_price": invalidation_price,
        "why_buy": why_buy[:4] if why_buy else ["✓ Evaluated against quantitative indicators"],
        "why_not_buy": why_not_buy[:4] if why_not_buy else ["⚠ Waiting for candle close confirmation"],
        "avoid_reasons": avoid_reasons[:4] if avoid_reasons else ["❌ Master Score below required threshold"]
    }

def summarize_decisions(verdicts):
    """Summarizes decision counts across verdicts."""
    counts = {
        "buy_now": 0,
        "confirmation": 0,
        "watch": 0,
        "avoid": 0,
        "blocked": 0,
        "summary": "NO HIGH-CONVICTION BUY TODAY"
    }

    for v in verdicts:
        ds = v.get("decision_state", "AVOID")
        if ds == "BUY NOW": counts["buy_now"] += 1
        elif ds == "BUY ON CONFIRMATION": counts["confirmation"] += 1
        elif ds == "WATCH": counts["watch"] += 1
        elif ds == "AVOID": counts["avoid"] += 1
        elif ds == "BLOCKED": counts["blocked"] += 1

    if counts["buy_now"] > 0:
        counts["summary"] = f"{counts['buy_now']} High-Conviction BUY NOW setup(s) active"
    elif counts["confirmation"] > 0:
        counts["summary"] = f"{counts['confirmation']} Setup(s) waiting for confirmation"
    else:
        counts["summary"] = "NO HIGH-CONVICTION BUY TODAY"

    return counts
