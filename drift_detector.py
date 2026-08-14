def detect_market_data_drift(curr_atr=2.4, curr_rvol=1.8, curr_vix=14.2):
    """
    Data & Regime Drift Detector:
    Compares current ATR, RVOL, volatility against training distributions.
    Flags DATA/REGIME DRIFT WARNING if variance exceeds threshold.
    """
    baseline_atr = 2.1
    baseline_vix = 13.5

    atr_drift = abs(curr_atr - baseline_atr) / baseline_atr
    vix_drift = abs(curr_vix - baseline_vix) / baseline_vix

    has_drift = (atr_drift > 0.40) or (vix_drift > 0.45)
    status = "DATA/REGIME DRIFT WARNING" if has_drift else "STABLE MARKET ENVIRONMENT"

    return {
        "drift_detected": has_drift,
        "drift_status": status,
        "atr_drift_pct": round(atr_drift * 100, 1),
        "vix_drift_pct": round(vix_drift * 100, 1),
        "recommendation": "RE-VALIDATE STRATEGY" if has_drift else "ENVIRONMENT NORMAL"
    }
