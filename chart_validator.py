import re
from datetime import datetime

FORBIDDEN_US_SYMBOLS = {"AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "SPY", "QQQ"}

def validate_nse_symbol(raw_symbol):
    """
    Validates and formats symbol for NSE TradingView widget.
    Returns (is_valid, clean_symbol, tradingview_symbol, error_msg)
    """
    if not raw_symbol:
        return False, "", "", "SYMBOL MISSING"

    clean_sym = str(raw_symbol).upper().replace(".NS", "").replace("NSE:", "").strip()
    clean_sym = re.sub(r'[^A-Z0-9\-_]', '', clean_sym)

    if clean_sym in FORBIDDEN_US_SYMBOLS:
        return False, clean_sym, "", f"FORBIDDEN INSTRUMENT: {clean_sym} is a US equity. MarketPulse operates strictly on NSE Indian equities."

    if not clean_sym or len(clean_sym) < 2:
        return False, clean_sym, "", f"INVALID SYMBOL: {raw_symbol}"

    tv_symbol = f"NSE:{clean_sym}"
    return True, clean_sym, tv_symbol, None

def validate_chart_data_match(mp_symbol, tv_symbol, mp_price, chart_price=None, max_tolerance_pct=2.0):
    """
    Validates symbol matching and price discrepancy tolerance between MarketPulse evidence and Chart.
    """
    is_valid_sym, clean_sym, expected_tv_sym, err = validate_nse_symbol(mp_symbol)
    if not is_valid_sym:
        return {
            "valid": False,
            "status": "CHART UNAVAILABLE",
            "error": err,
            "expected_symbol": expected_tv_sym,
            "loaded_symbol": tv_symbol
        }

    if tv_symbol and tv_symbol.upper() != expected_tv_sym.upper():
        return {
            "valid": False,
            "status": "CHART SYMBOL ERROR",
            "error": f"Symbol mismatch: Expected {expected_tv_sym}, loaded {tv_symbol}",
            "expected_symbol": expected_tv_sym,
            "loaded_symbol": tv_symbol
        }

    price_diff_pct = 0.0
    if chart_price and mp_price and float(mp_price) > 0:
        price_diff_pct = abs((float(chart_price) - float(mp_price)) / float(mp_price)) * 100.0
        if price_diff_pct > max_tolerance_pct:
            return {
                "valid": False,
                "status": "DATA MISMATCH",
                "error": f"Price discrepancy exceeds {max_tolerance_pct}%: MarketPulse={mp_price}, Chart={chart_price} (Diff: {price_diff_pct:.2f}%)",
                "expected_symbol": expected_tv_sym,
                "loaded_symbol": tv_symbol,
                "marketpulse_price": float(mp_price),
                "chart_price": float(chart_price),
                "price_diff_pct": round(price_diff_pct, 2)
            }

    return {
        "valid": True,
        "status": "VALIDATED",
        "error": None,
        "expected_symbol": expected_tv_sym,
        "loaded_symbol": expected_tv_sym,
        "marketpulse_price": float(mp_price) if mp_price else 0.0,
        "chart_price": float(chart_price) if chart_price else float(mp_price or 0.0),
        "price_diff_pct": round(price_diff_pct, 2),
        "timestamp": datetime.now().isoformat()
    }

def create_analysis_snapshot(verdict_payload, evidence=None):
    """
    Creates an immutable analysis_snapshot dictionary for point-in-time state safety.
    """
    price = float(verdict_payload.get("price") or 100.0)
    rp = verdict_payload.get("risk_params", {})
    t = verdict_payload.get("technicals", {})

    return {
        "snapshot_id": f"snap_{int(datetime.now().timestamp())}_{verdict_payload.get('symbol')}",
        "timestamp": datetime.now().isoformat(),
        "symbol": verdict_payload.get("symbol"),
        "price": price,
        "entry_price": price,
        "trigger_price": float(verdict_payload.get("trigger_price_val") or (price * 1.01)),
        "stop_loss": float(rp.get("stop_loss") or (price * 0.94)),
        "target_1": float(rp.get("target_1") or (price * 1.08)),
        "target_2": float(rp.get("target_2") or (price * 1.15)),
        "invalidation_price": float(rp.get("stop_loss") or (price * 0.94)),
        "stock_quality_score": verdict_payload.get("stock_quality_score", verdict_payload.get("marketpulse_score", 75)),
        "entry_quality_score": verdict_payload.get("entry_quality_score", 60),
        "master_score": verdict_payload.get("marketpulse_score", 75),
        "decision_state": verdict_payload.get("decision_state", "WATCH"),
        "decision_badge": verdict_payload.get("decision_badge", "🔵 WATCH"),
        "rvol": float(t.get("rvol") or 1.0),
        "rs_score": int(t.get("relative_strength", 75)),
        "sector": verdict_payload.get("sector", "NSE Equity"),
        "market_regime": verdict_payload.get("market_regime", "NORMAL"),
        "data_quality_score": int(verdict_payload.get("data_quality_score", 100))
    }
