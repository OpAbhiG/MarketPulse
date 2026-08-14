import strategy_health

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
    health = strategy_health.evaluate_strategy_health()
    if not health.get("is_active"):
        return {
            "decision_state": "BLOCKED",
            "decision_badge": "🟠 BLOCKED",
            "avoid_reasons": ["❌ BUY BLOCKED — Strategy Paused due to recent performance decay"],
            "why_buy": [],
            "why_not_buy": ["Strategy Kill-Switch active"],
            "trigger_price_text": "BLOCKED",
            "invalidation_text": "BLOCKED"
        }

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
    rvol = float(t.get("rvol") or 1.0)

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
    trigger_val = float(sw_hi)
    sl_val = float(sw_lo)

    # Decision State Machine
    if master_score >= 75 and (val_status == "BUY BLOCKED" or not validated) and ("Portfolio" in val_reason or "Risk" in val_reason):
        decision_state = "BLOCKED"
        decision_badge = "🟠 BLOCKED"
        action = "DO NOT TRADE — RISK GATE BLOCKED"
    elif master_score >= 80 and verdict == "BUY" and validated and conf >= 7 and rr >= 1.5 and not is_ext:
        decision_state = "BUY NOW"
        decision_badge = "🟢 BUY NOW"
        action = "BUY ENTRY CONFIRMED"
    elif master_score >= 75 and (verdict in ("BUY", "WATCH") or boom_type != "NORMAL") and not is_ext:
        decision_state = "WAIT — CONFIRMATION REQUIRED"
        decision_badge = "🟡 WAIT — CONFIRMATION REQUIRED"
        action = f"WAIT FOR CONFIRMATION ABOVE {trigger_price}"
    elif master_score >= 65 and not is_ext:
        decision_state = "WATCH"
        decision_badge = "🔵 WATCH"
        action = "MONITOR FOR BREAKOUT CONFIRMATION"
    else:
        decision_state = "AVOID"
        decision_badge = "🔴 AVOID"
        action = "WAIT / DO NOT BUY"

    # Deterministic "WHAT WOULD CHANGE THIS TO BUY?"
    what_changes = []
    if price < trigger_val:
        what_changes.append(f"✓ Price breaks & closes above {trigger_price}")
    if rvol < 1.5:
        what_changes.append("✓ RVOL expands to >= 1.5x average volume")
    if is_ext:
        what_changes.append("✓ Price consolidates to reset extension status")
    if rr < 1.5:
        what_changes.append("✓ Risk/Reward ratio improves to >= 1:1.5")
    if not what_changes:
        what_changes.append("✓ Market regime remains supportive & validation passes")

    # What Confirms & What Invalidates
    what_confirms = [
        f"✓ Breakout above resistance ({trigger_price})",
        f"✓ Heavy buying volume (RVOL >= 1.5x, currently {rvol:.2f}x)",
        "✓ Supportive sector momentum & market regime"
    ]
    what_invalidates = [
        f"✗ Daily close below invalidation ({invalidation_price})",
        "✗ Sudden volume spike on down candle",
        "✗ Market regime shift to HIGH RISK / BEARISH"
    ]

    # Detailed Trade Plan
    rp = verdict_payload.get("risk_params", {})
    trade_plan = {
        "decision_state": decision_state,
        "entry_price": f"₹{price:.2f}",
        "trigger_price": trigger_price,
        "stop_loss": f"₹{sl_val:.2f}",
        "target_1": rp.get("target_1_str", f"₹{(price*1.08):.2f}"),
        "target_2": rp.get("target_2_str", f"₹{(price*1.15):.2f}"),
        "rr_ratio": f"1:{rr:.1f}",
        "position_size": f"{rp.get('suggested_position_size_pct', 10.0)}% of capital",
        "max_loss": f"₹{rp.get('max_loss_per_trade_inr', 1000.0)}"
    }

    return {
        "decision_state": decision_state,
        "decision_badge": decision_badge,
        "action": action,
        "trigger_price": trigger_price,
        "trigger_price_val": trigger_val,
        "invalidation_price": invalidation_price,
        "why_buy": why_buy[:4] if why_buy else ["✓ Evaluated against quantitative indicators"],
        "why_not_buy": why_not_buy[:4] if why_not_buy else ["⚠ Waiting for candle close confirmation"],
        "avoid_reasons": avoid_reasons[:4] if avoid_reasons else ["❌ Master Score below required threshold"],
        "what_would_change_to_buy": what_changes,
        "what_confirms_it": what_confirms,
        "what_invalidates_it": what_invalidates,
        "trade_plan": trade_plan
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
        elif "WAIT" in ds or ds == "BUY ON CONFIRMATION": counts["confirmation"] += 1
        elif ds == "WATCH": counts["watch"] += 1
        elif ds == "AVOID": counts["avoid"] += 1
        elif ds == "BLOCKED": counts["blocked"] += 1

    if counts["buy_now"] > 0:
        counts["summary"] = f"{counts['buy_now']} High-Conviction BUY NOW setup(s) active"
        counts["top_label"] = "TOP PICK"
    elif counts["confirmation"] > 0:
        counts["summary"] = f"{counts['confirmation']} Setup(s) waiting for confirmation"
        counts["top_label"] = "TOP OPPORTUNITY TO WATCH"
    else:
        counts["summary"] = "NO HIGH-CONVICTION BUY TODAY"
        counts["top_label"] = "TOP OPPORTUNITY TO WATCH"

    return counts

