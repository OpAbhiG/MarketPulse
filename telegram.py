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

    msg_hash = hashlib.sha256(f"{symbol}_{signal_type}_{text[:100]}".encode('utf-8')).hexdigest()
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM telegram_messages WHERE msg_hash = ?", (msg_hash,))
    if c.fetchone():
        conn.close()
        return {"ok": True, "deduped": True, "note": "Duplicate message suppressed"}

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

def format_telegram_preboom_message(v):
    """Formats PRE-BOOM WATCH alert."""
    sym = v.get("symbol")
    return f"""⚡ <b>PRE-BOOM WATCH — {sym}</b>

BOOM Score: {v.get('boom_score', 75)}/100
Current Price: ₹{v.get('price', '—')}
Setup: Early BOOM (Approaching Breakout)
Sector: {v.get('sector', '—')}

<i>No BUY yet. Waiting for confirmation.</i>"""

def format_telegram_signal_message(v, mode="SWING"):
    """Formats Intraday / Swing BUY signal alert."""
    sym = v.get("symbol")
    cap = v.get("cap_segment", "large")
    conf = v.get("confidence", 7)
    mp_score = v.get("marketpulse_score", 80)
    tag = "🟢 INTRADAY BUY" if mode == "INTRADAY" else "📈 SWING BUY"

    return f"""{tag} — {sym} ({cap} cap)

Verdict: BUY | Confidence: {conf}/10
MarketPulse Score: {mp_score}/100
Setup: {v.get('boom_type', 'BOOM Momentum')}

Entry Zone: {v.get('buy_zone', '—')}
Stop Loss: {v.get('stop_loss', '—')}
Target 1: {v.get('target', '—')}
Target 2: {v.get('target_2', '—')}
Risk/Reward: 1:{v.get('rr_ratio', 1.5)}

Why: {v.get('why', 'Strong technical momentum')}
Key Catalyst: {v.get('catalyst', 'Positive analyst upside')}

Invalidation: {v.get('invalidation', 'Daily close below stop loss')}"""

def format_daily_summary_message(verdicts, blocked_verdicts=None, market_regime=None):
    """Formats the daily market summary report with Top Blocked Opportunities."""
    dt_str = datetime.now().strftime("%d %b %Y")
    reg_str = market_regime.get("trend", "BULLISH") if market_regime else "BULLISH"
    reg_score = market_regime.get("score", 75) if market_regime else 75

    buys = [v for v in verdicts if v.get("verdict") == "BUY"]
    blocked = blocked_verdicts or [v for v in verdicts if not v.get("validated")]

    buy_list_str = "\n".join([f"• <b>{b['symbol']}</b> — {b['confidence']}/10 (Zone: {b.get('buy_zone','—')})" for b in buys[:5]]) if buys else "No BUY signals fired."
    blocked_str = "\n".join([f"• <b>{b['symbol']}</b> (Score {b.get('marketpulse_score',0)}) — {b.get('validation_reason','Blocked')}" for b in blocked[:3]]) if blocked else "None"

    return f"""📊 <b>MARKETPULSE — DAILY REPORT</b>

Date: {dt_str}
Market Regime: {reg_str} (Score: {reg_score}/100)

Stocks Scanned: {len(verdicts)}
BUY Signals: {len(buys)}

<b>Top BUY Signals:</b>
{buy_list_str}

<b>Top Blocked Opportunities:</b>
{blocked_str}"""
