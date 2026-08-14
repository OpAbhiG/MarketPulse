import os
import time
import uuid
import json
import threading
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory

import data_sources
import scoring
import database
from market_regime import evaluate_market_regime
from sector_engine import fetch_sector_heatmaps
from backtest import run_strategy_backtest
from performance import calculate_system_performance, get_confidence_calibration, get_agent_performance_metrics
from telegram import send_telegram_alert, format_telegram_signal_message
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
data_sources.load_env(ENV_PATH)

app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")

RUN_STATE = {
    "running": False,
    "active_step": "idle",
    "mode": "live",
    "engine": "deterministic",
    "run_id": None,
    "started_at": None,
    "completed_at": None,
    "verdicts": [],
    "market_regime": None,
    "sectors": [],
    "kpis": {"universe": 0, "shortlisted": 0, "debate": 0, "buy_signals": 0, "top_pick": None},
    "log": [],
    "agents": {
        "scout": {"id": "scout", "name": "Scout", "role": "screens the stock universe for movers", "status": "offline", "stat1": 0, "stat1_label": "Scanned", "stat2": 0, "stat2_label": "Shortlisted"},
        "technician": {"id": "technician", "name": "Technician", "role": "reads price action, RVOL & trend", "status": "offline", "stat1": 0, "stat1_label": "Analyzed", "stat2": "—", "stat2_label": "Avg RVOL"},
        "fundamentalist": {"id": "fundamentalist", "name": "Fundamentalist", "role": "weighs valuation & analyst targets", "status": "offline", "stat1": 0, "stat1_label": "Covered", "stat2": "—", "stat2_label": "Avg upside"},
        "newsdesk": {"id": "newsdesk", "name": "Newsdesk", "role": "pulls live news & scores sentiment", "status": "offline", "stat1": 0, "stat1_label": "Headlines", "stat2": "—", "stat2_label": "Net tone"},
        "bull": {"id": "bull", "name": "Bull", "role": "argues the case to buy", "status": "offline", "stat1": 0, "stat1_label": "Cases", "stat2": "—", "stat2_label": "Avg score"},
        "bear": {"id": "bear", "name": "Bear", "role": "argues the case against", "status": "offline", "stat1": 0, "stat1_label": "Cases", "stat2": "—", "stat2_label": "Avg score"},
        "judge": {"id": "judge", "name": "Judge", "role": "weighs debate, issues verdict & score", "status": "offline", "stat1": 0, "stat1_label": "Verdicts", "stat2": "—", "stat2_label": "Buy"},
        "messenger": {"id": "messenger", "name": "Messenger", "role": "sends validated signals to Telegram", "status": "offline", "stat1": 0, "stat1_label": "Sent", "stat2": "—", "stat2_label": "Engine"}
    }
}

STATE_LOCK = threading.Lock()

def add_log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with STATE_LOCK:
        RUN_STATE["log"].append(f"{ts} · {msg}")
        if len(RUN_STATE["log"]) > 100:
            RUN_STATE["log"].pop(0)

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "dashboard.html")

@app.get("/status")
def get_status():
    with STATE_LOCK:
        return jsonify(RUN_STATE)

@app.get("/config")
def get_config():
    conf_thresh = int(os.getenv("CONFIDENCE_THRESHOLD", "7"))
    univ = data_sources.load_universe(os.path.join(BASE_DIR, "universe.json"))
    return jsonify({
        "brand": os.getenv("BRAND", "MarketPulse"),
        "confidence_threshold": conf_thresh,
        "llm_provider": os.getenv("LLM_PROVIDER", "auto"),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "agent_delay": float(os.getenv("AGENT_DELAY", "0.35")),
        "shortlist_per_bucket": int(os.getenv("SHORTLIST_PER_BUCKET", "4")),
        "universe": univ,
        "port": int(os.getenv("PORT", "5000"))
    })

@app.get("/market-regime")
def get_market_regime():
    reg = evaluate_market_regime()
    return jsonify({"ok": True, "market_regime": reg})

@app.get("/sectors")
def get_sectors():
    secs = fetch_sector_heatmaps()
    return jsonify({"ok": True, "sectors": secs})

@app.get("/signals")
def get_signals():
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM verdicts ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return jsonify({"ok": True, "signals": [dict(r) for r in rows]})

@app.get("/watchlist")
def get_user_watchlist():
    items = database.get_watchlist()
    return jsonify({"ok": True, "watchlist": items})

@app.post("/watchlist")
def add_user_watchlist():
    data = request.get_json(silent=True) or {}
    sym = data.get("symbol")
    if not sym: return jsonify({"ok": False, "error": "Symbol required"}), 400
    database.add_to_watchlist(sym, data.get("notes", ""))
    return jsonify({"ok": True, "watchlist": database.get_watchlist()})

@app.delete("/watchlist/<symbol>")
def delete_user_watchlist(symbol):
    database.remove_from_watchlist(symbol)
    return jsonify({"ok": True, "watchlist": database.get_watchlist()})

@app.get("/performance")
def get_perf_stats():
    sys_perf = calculate_system_performance()
    calib = get_confidence_calibration()
    return jsonify({"ok": True, "system_performance": sys_perf, "calibration": calib})

@app.get("/agent-performance")
def get_agent_perf_stats():
    agent_perf = get_agent_performance_metrics()
    return jsonify({"ok": True, "agent_performance": agent_perf})

@app.post("/backtest")
def trigger_backtest():
    data = request.get_json(silent=True) or {}
    strat_name = data.get("strategy_name", "Momentum Breakout")
    rvol_min = float(data.get("rvol_min", 1.2))
    res = run_strategy_backtest(strategy_name=strat_name, rvol_min=rvol_min)
    return jsonify({"ok": True, "backtest": res})

@app.post("/api/parse-pasted-stocks")
def parse_pasted_stocks():
    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")
    symbols = data_sources.extract_nse_symbols(raw_text)
    return jsonify({"ok": True, "symbols": symbols, "count": len(symbols)})

def background_analysis_pipeline(custom_symbols=None):
    with STATE_LOCK:
        run_id = f"run_{int(time.time())}"
        RUN_STATE.update({
            "running": True,
            "run_id": run_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "active_step": "scout",
            "verdicts": [],
            "log": []
        })

    add_log(f"Starting pipeline run ID: {run_id}")

    # Evaluate Market Regime & Sector Intelligence
    regime = evaluate_market_regime()
    sectors = fetch_sector_heatmaps()
    with STATE_LOCK:
        RUN_STATE["market_regime"] = regime
        RUN_STATE["sectors"] = sectors

    # Step 1: Scout
    add_log("Step 1/7: Scout screening NSE universe...")
    with STATE_LOCK:
        RUN_STATE["agents"]["scout"]["status"] = "working"
    
    univ_path = os.path.join(BASE_DIR, "universe.json")
    univ_dict = data_sources.load_universe(univ_path)
    
    if custom_symbols and len(custom_symbols) > 0:
        flat = [s.upper().replace(".NS","") + ".NS" for s in custom_symbols]
    else:
        flat = []
        for cat in ["large", "mid", "small"]:
            flat.extend(univ_dict.get(cat, []))

    add_log(f"Fetching evidence for {len(flat)} tickers...")
    evidences = data_sources.load_live_evidence(flat if flat else univ_dict)

    with STATE_LOCK:
        RUN_STATE["kpis"]["universe"] = len(evidences)
        RUN_STATE["agents"]["scout"]["stat1"] = len(evidences)
        RUN_STATE["agents"]["scout"]["stat2"] = len(evidences)
        RUN_STATE["agents"]["scout"]["status"] = "done"

    # Step 2-6: Technician, Fundamentalist, Newsdesk, Debate, Judge
    add_log("Step 2-6/7: Agent debate & risk scoring...")
    verdicts = []
    buy_signals = 0

    for ev in evidences:
        v = scoring.deterministic_evaluate(ev, market_regime=regime)
        verdicts.append(v)
        database.save_verdict(run_id, v)
        if v.get("verdict") == "BUY":
            buy_signals += 1

    top_pick = max(verdicts, key=lambda x: x.get("marketpulse_score", 0)) if verdicts else None

    # Step 7: Messenger (Telegram)
    add_log("Step 7/7: Messenger Telegram validation...")
    with STATE_LOCK:
        RUN_STATE["agents"]["messenger"]["status"] = "working"

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    sent_count = 0

    if bot_token and chat_id:
        for v in verdicts:
            if v.get("validated") and v.get("verdict") == "BUY":
                msg = format_telegram_signal_message(v)
                res = send_telegram_alert(bot_token, chat_id, msg, symbol=v.get("symbol"), signal_type="BUY SIGNAL")
                if res.get("sent"):
                    sent_count += 1

    with STATE_LOCK:
        RUN_STATE["agents"]["messenger"]["stat1"] = sent_count
        RUN_STATE["agents"]["messenger"]["status"] = "done"
        RUN_STATE.update({
            "running": False,
            "active_step": "done",
            "completed_at": datetime.now().isoformat(),
            "verdicts": verdicts,
            "kpis": {
                "universe": len(evidences),
                "shortlisted": len(evidences),
                "debate": len(evidences),
                "buy_signals": buy_signals,
                "top_pick": top_pick
            }
        })
        database.save_run({
            "id": run_id,
            "started_at": RUN_STATE["started_at"],
            "completed_at": RUN_STATE["completed_at"],
            "engine": RUN_STATE["engine"],
            "mode": RUN_STATE["mode"],
            "universe_count": len(evidences),
            "shortlisted_count": len(evidences),
            "boom_count": len([v for v in verdicts if v.get("boom_score", 0) >= 70]),
            "buy_count": buy_signals,
            "status": "COMPLETED"
        })

    add_log("Pipeline cycle completed successfully!")

@app.post("/start")
@app.post("/scan")
def trigger_start():
    data = request.get_json(silent=True) or {}
    custom_syms = data.get("symbols")
    with STATE_LOCK:
        if RUN_STATE["running"]:
            return jsonify({"ok": False, "error": "Analysis cycle already running"}), 400

    thread = threading.Thread(target=background_analysis_pipeline, args=(custom_syms,))
    thread.daemon = True
    thread.start()
    return jsonify({"ok": True, "mode": "live"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"MarketPulse Dashboard live at:")
    print(f" • Localhost: http://localhost:{port}")
    print(f" • IP Access: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
