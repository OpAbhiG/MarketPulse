import yfinance as yf
from datetime import datetime

def evaluate_market_regime():
    """
    Evaluates NIFTY 50 and broad market indicators to compute Market Regime & Risk Mode.
    Outputs risk_mode: RISK_ON, NORMAL, CAUTIOUS, or RISK_OFF.
    """
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="6mo")
        if hist.empty:
            return _default_regime("Market data offline")

        close = hist["Close"]
        latest = float(close.iloc[-1])
        prev = float(close.iloc[-2]) if len(close) > 1 else latest
        day_chg = ((latest - prev) / prev) * 100

        ema20 = float(close.ewm(span=20).mean().iloc[-1]) if len(close) >= 20 else latest
        ema50 = float(close.ewm(span=50).mean().iloc[-1]) if len(close) >= 50 else latest
        sma200 = float(close.rolling(window=200).mean().iloc[-1]) if len(close) >= 200 else latest

        # Trend Evaluation
        trend = "BULLISH" if latest >= ema20 and ema20 >= ema50 else "BEARISH" if latest < ema50 else "NEUTRAL"

        # Momentum
        ret_20d = ((latest - float(close.iloc[-20])) / float(close.iloc[-20])) * 100 if len(close) >= 20 else 0
        momentum = "STRONG" if ret_20d >= 3.0 else "WEAK" if ret_20d <= -2.0 else "MODERATE"

        # Volatility check via India VIX if accessible, else candle high/low range
        volatility = "NORMAL"
        vix_val = 14.5
        try:
            vix = yf.Ticker("^INDIAVIX")
            v_hist = vix.history(period="5d")
            if not v_hist.empty:
                vix_val = float(v_hist["Close"].iloc[-1])
                if vix_val >= 22.0:
                    volatility = "HIGH"
                elif vix_val <= 12.0:
                    volatility = "LOW"
        except Exception:
            pass

        # Risk Mode Logic
        score = 50
        if trend == "BULLISH": score += 25
        elif trend == "NEUTRAL": score += 10
        if momentum == "STRONG": score += 15
        elif momentum == "MODERATE": score += 5
        if latest > sma200: score += 10

        if vix_val >= 24.0: score -= 25

        score = max(0, min(100, score))

        if score >= 75:
            risk_mode = "RISK_ON"
        elif score >= 55:
            risk_mode = "NORMAL"
        elif score >= 40:
            risk_mode = "CAUTIOUS"
        else:
            risk_mode = "RISK_OFF"

        return {
            "trend": trend,
            "momentum": momentum,
            "breadth": "POSITIVE" if day_chg >= 0 else "NEGATIVE",
            "volatility": volatility,
            "vix": round(vix_val, 2),
            "risk_mode": risk_mode,
            "score": score,
            "nifty_price": round(latest, 2),
            "nifty_day_change_pct": round(day_chg, 2),
            "updated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return _default_regime(str(e))

def _default_regime(reason):
    return {
        "trend": "NEUTRAL",
        "momentum": "MODERATE",
        "breadth": "POSITIVE",
        "volatility": "NORMAL",
        "vix": 14.5,
        "risk_mode": "NORMAL",
        "score": 65,
        "nifty_price": 24500.0,
        "nifty_day_change_pct": 0.2,
        "updated_at": datetime.utcnow().isoformat(),
        "note": f"Fallback regime used ({reason})"
    }
