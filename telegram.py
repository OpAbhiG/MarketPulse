import hashlib
import requests
import json
import logging
from datetime import datetime
from database import get_connection

def send_telegram_alert(token, chat_id, text, symbol=None, signal_type="BUY SIGNAL"):
    """
    Sends a formatted alert to Telegram with deduplication and disclaimer.
    Never logs secret bot tokens.
    """
    if not token or not chat_id:
        return {"ok": False, "error": "Telegram token or chat_id not configured"}

    # Deduplication Hash Check
    msg_hash = hashlib.sha256(f"{symbol}_{signal_type}_{text[:100]}".encode('utf-8')).hexdigest()
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM telegram_messages WHERE msg_hash = ?", (msg_hash,))
    if c.fetchone():
        conn.close()
        return {"ok": True, "deduped": True, "note": "Duplicate message suppressed"}

    # Enforce standard disclaimer
    disclaimer = "\n\n— Analysis only. No trade was placed.\nNot investment advice."
    full_text = text.strip() + disclaimer

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": full_text,
        "parse_mode": "HTML"
    }

    try:
        resp = requests.post(url, json=payload, timeout=8)
        data = resp.json()
        if data.get("ok"):
            msg_id = data.get("result", {}).get("message_id")
            c.execute("""
                INSERT INTO telegram_messages (msg_hash, symbol, signal_type, message_text, telegram_msg_id, sent_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (msg_hash, symbol or "SYSTEM", signal_type, text[:200], msg_id, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            return {"ok": True, "sent": True, "message_id": msg_id}
        else:
            conn.close()
            return {"ok": False, "error": data.get("description", "Telegram API error")}
    except Exception as e:
        conn.close()
        return {"ok": False, "error": f"Telegram request failed: {str(e)}"}

def format_telegram_signal_message(v):
    """
    Formats a validated BUY signal for Telegram.
    """
    sym = v.get("symbol")
    cap = v.get("cap_segment", "large")
    conf = v.get("confidence", 7)
    mp_score = v.get("marketpulse_score", 80)
    boom_score = v.get("boom_score", 75)

    return f"""🟢 <b>BUY SIGNAL — {sym}</b> ({cap} cap)

Verdict: BUY | Confidence: {conf}/10
MarketPulse Score: {mp_score}/100
BOOM Score: {boom_score}/100

Entry Zone: {v.get('buy_zone', '—')}
Stop Loss: {v.get('stop_loss', '—')}
Target 1: {v.get('target', '—')}
Target 2: {v.get('target_2', '—')}
Risk/Reward: 1:{v.get('rr_ratio', 1.5)}

Why: {v.get('why', 'Strong technical momentum')}
Key Catalyst: {v.get('catalyst', 'Positive analyst upside')}

Invalidation: {v.get('invalidation', 'Daily close below stop loss')}"""

def format_daily_summary_message(verdicts, market_regime=None):
    """
    Formats the daily market summary report for Telegram.
    """
    dt_str = datetime.now().strftime("%d %b %Y")
    reg_str = market_regime.get("trend", "BULLISH") if market_regime else "BULLISH"
    reg_score = market_regime.get("score", 75) if market_regime else 75

    buys = [v for v in verdicts if v.get("verdict") == "BUY"]
    booms = [v for v in verdicts if v.get("boom_score", 0) >= 70]

    buy_list_str = "\n".join([f"• <b>{b['symbol']}</b> — {b['confidence']}/10 (Zone: {b.get('buy_zone','—')})" for b in buys[:5]]) if buys else "No BUY signals fired."

    return f"""📊 <b>MARKETPULSE — DAILY REPORT</b>

Date: {dt_str}
Market Regime: {reg_str} (Score: {reg_score}/100)

Stocks Scanned: {len(verdicts)}
BOOM Momentum: {len(booms)}
BUY Signals: {len(buys)}

<b>Top BUY Signals:</b>
{buy_list_str}"""
