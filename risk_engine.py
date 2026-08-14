import math

def calculate_risk_parameters(evidence, trading_capital=50000, max_risk_per_trade=1000, active_positions=None):
    """
    Calculates Entry Zone, Stop Loss, Target 1, Target 2, Risk/Share, Reward/Share, R:R ratio,
    Position Size Calculator outputs, and Portfolio Concentration Risk checks.
    """
    price = evidence.get("price", {})
    tech = evidence.get("technicals", {})
    analyst = evidence.get("analyst", {})
    sector_name = evidence.get("sector") or "Banking"

    latest = price.get("live")
    if not latest:
        return _default_risk()

    sw_low = tech.get("swing_low")
    target_mean = analyst.get("target_mean")

    entry_low = round(latest, 2)
    entry_high = round(latest * 1.015, 2)

    sl_val = latest * 0.92
    if sw_low and sw_low < latest and sw_low >= latest * 0.85:
        sl_val = sw_low
    sl_val = round(sl_val, 2)

    risk_per_share = round(latest - sl_val, 2)
    if risk_per_share <= 0:
        risk_per_share = round(latest * 0.05, 2)

    t1_val = round(latest + (risk_per_share * 1.5), 2)
    t2_val = round(latest + (risk_per_share * 3.0), 2)
    if target_mean and target_mean > t2_val:
        t2_val = round(target_mean, 2)

    reward_per_share_t1 = round(t1_val - latest, 2)
    reward_per_share_t2 = round(t2_val - latest, 2)

    rr_t1 = round(reward_per_share_t1 / risk_per_share, 2) if risk_per_share > 0 else 1.5
    rr_t2 = round(reward_per_share_t2 / risk_per_share, 2) if risk_per_share > 0 else 3.0

    atr14 = tech.get("atr14") or round(latest * 0.025, 2)

    # Position Size Calculator
    qty = 0
    if risk_per_share > 0:
        qty = math.floor(max_risk_per_trade / risk_per_share)

    capital_required = round(qty * latest, 2)
    max_loss = round(qty * risk_per_share, 2)
    risk_pct = round((max_loss / trading_capital) * 100, 2) if trading_capital else 0.0
    pos_size_pct = round((capital_required / trading_capital) * 100, 2) if trading_capital else 0.0

    # Portfolio Concentration Risk Check
    positions = active_positions or []
    max_open = 5
    max_sector = 2

    sector_count = sum(1 for p in positions if p.get("sector") == sector_name)
    total_open = len(positions)

    concentration_blocked = False
    concentration_reason = "Portfolio risk within limits"

    if total_open >= max_open:
        concentration_blocked = True
        concentration_reason = f"Portfolio limit reached ({total_open}/{max_open} active positions)"
    elif sector_count >= max_sector:
        concentration_blocked = True
        concentration_reason = f"Portfolio concentration risk ({sector_count}/{max_sector} active {sector_name} positions)"

    return {
        "entry_price": latest,
        "buy_zone": f"₹{entry_low:.2f} - ₹{entry_high:.2f}",
        "stop_loss": sl_val,
        "stop_loss_str": f"₹{sl_val:.2f}",
        "stop_loss_pct": round(((latest - sl_val) / latest) * 100, 2),
        "target_1": t1_val,
        "target_1_str": f"₹{t1_val:.2f}",
        "target_2": t2_val,
        "target_2_str": f"₹{t2_val:.2f}",
        "risk_per_share": risk_per_share,
        "reward_per_share": reward_per_share_t1,
        "rr_ratio": rr_t1,
        "rr_ratio_t2": rr_t2,
        "atr14": atr14,
        "portfolio_concentration": {
            "is_blocked": concentration_blocked,
            "reason": concentration_reason,
            "sector_count": sector_count,
            "total_open": total_open
        },
        "calculator": {
            "quantity": qty,
            "capital_required": capital_required,
            "max_loss": max_loss,
            "risk_pct": risk_pct,
            "position_size_pct": pos_size_pct
        }
    }

def _default_risk():
    return {
        "entry_price": 100.0,
        "buy_zone": "₹100.00 - ₹101.50",
        "stop_loss": 92.0,
        "stop_loss_str": "₹92.00",
        "stop_loss_pct": 8.0,
        "target_1": 112.0,
        "target_1_str": "₹112.00",
        "target_2": 124.0,
        "target_2_str": "₹124.00",
        "risk_per_share": 8.0,
        "reward_per_share": 12.0,
        "rr_ratio": 1.5,
        "rr_ratio_t2": 3.0,
        "atr14": 2.5,
        "portfolio_concentration": {"is_blocked": False, "reason": "Portfolio risk within limits", "sector_count": 0, "total_open": 0},
        "calculator": {
            "quantity": 125,
            "capital_required": 12500.0,
            "max_loss": 1000.0,
            "risk_pct": 2.0,
            "position_size_pct": 25.0
        }
    }
