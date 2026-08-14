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
import performance_engine
from market_regime import evaluate_market_regime

from sector_engine import fetch_sector_heatmaps
from opportunity_engine import rank_market_opportunities
from decision_engine import summarize_decisions
from backtest import run_strategy_backtest
from performance import calculate_system_performance, get_confidence_calibration, get_agent_performance_metrics
from telegram import send_telegram_alert, format_telegram_signal_message, format_telegram_preboom_message

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
    "blocked_verdicts": [],
    "avoid_verdicts": [],
    "market_regime": None,
    "sectors": [],
    "opportunities": {},
    "decision_counts": {"buy_now": 0, "confirmation": 0, "watch": 0, "avoid": 0, "blocked": 0, "summary": "NO HIGH-CONVICTION BUY TODAY"},
    "kpis": {"universe": 0, "shortlisted": 0, "intraday": 0, "swing": 0, "buy_signals": 0, "top_intraday": None, "top_swing": None},
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

@app.route("/status", methods=["GET"])
def get_status():
    with STATE_LOCK:
        return jsonify(RUN_STATE)

@app.route("/health", methods=["GET"])
def get_health():
    reg = evaluate_market_regime()
    return jsonify({
        "status": "HEALTHY",
        "flask": "HEALTHY",
        "sqlite": "HEALTHY",
        "market_data": "HEALTHY",
        "llm_provider": os.getenv("LLM_PROVIDER", "auto"),
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "last_scan": RUN_STATE["completed_at"] or "Idle",
        "market_regime": reg["risk_mode"]
    })

@app.route("/config", methods=["GET"])
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

@app.route("/market-regime", methods=["GET"])
def get_market_regime():
    reg = evaluate_market_regime()
    return jsonify({"ok": True, "market_regime": reg})

@app.route("/sectors", methods=["GET"])
def get_sectors():
    secs = fetch_sector_heatmaps()
    return jsonify({"ok": True, "sectors": secs})

@app.route("/opportunities", methods=["GET"])
def get_opportunities():
    with STATE_LOCK:
        verdicts = RUN_STATE.get("verdicts", [])
    opps = rank_market_opportunities(verdicts)
    return jsonify({"ok": True, "opportunities": opps})

@app.route("/signals", methods=["GET"])
def get_signals():
    conn = database.get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM verdicts ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return jsonify({"ok": True, "signals": [dict(r) for r in rows]})

@app.route("/watchlist", methods=["GET", "POST"])
def user_watchlist_route():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        sym = data.get("symbol")
        if not sym: return jsonify({"ok": False, "error": "Symbol required"}), 400
        database.add_to_watchlist(sym, data.get("notes", ""))
    items = database.get_watchlist()
    return jsonify({"ok": True, "watchlist": items})

@app.route("/watchlist/<symbol>", methods=["DELETE"])
def delete_user_watchlist(symbol):
    database.remove_from_watchlist(symbol)
    return jsonify({"ok": True, "watchlist": database.get_watchlist()})

@app.route("/performance", methods=["GET"])
def get_perf_stats():
    sys_perf = calculate_system_performance()
    calib = get_confidence_calibration()
    return jsonify({"ok": True, "system_performance": sys_perf, "calibration": calib})

@app.route("/agent-performance", methods=["GET"])
def get_agent_perf_stats():
    agent_perf = get_agent_performance_metrics()
    return jsonify({"ok": True, "agent_performance": agent_perf})

@app.route("/backtest", methods=["POST"])
def trigger_backtest():
    data = request.get_json(silent=True) or {}
    strat_name = data.get("strategy_name", "Momentum Breakout")
    rvol_min = float(data.get("rvol_min", 1.2))
    res = run_strategy_backtest(strategy_name=strat_name, rvol_min=rvol_min)
    return jsonify({"ok": True, "backtest": res})

@app.route("/api/parse-pasted-stocks", methods=["POST"])
@app.route("/paste-stocks", methods=["POST"])
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
            "blocked_verdicts": [],
            "avoid_verdicts": [],
            "log": []
        })

    add_log(f"Starting V3 decision analysis pipeline run ID: {run_id}")

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

    # Step 2-6: Technician, Fundamentalist, Newsdesk, Debate, Judge, Decision Engine
    add_log("Step 2-6/7: Intraday/Swing debate & Master Decision Engine...")
    verdicts = []
    blocked_verdicts = []
    avoid_verdicts = []

    for ev in evidences:
        v = scoring.deterministic_evaluate(ev, market_regime=regime, active_positions=verdicts)
        verdicts.append(v)
        database.save_verdict(run_id, v)
        if v.get("decision_state") == "BUY NOW":
            performance_engine.record_opportunity_prediction(v, mode="SWING")
        if v.get("decision_state") == "BLOCKED":
            blocked_verdicts.append(v)
        elif v.get("decision_state") == "AVOID":
            avoid_verdicts.append(v)


    opps = rank_market_opportunities(verdicts)
    dec_counts = summarize_decisions(verdicts)

    # Step 7: Messenger (Telegram)
    add_log("Step 7/7: Messenger Telegram pre-BOOM & signal validation...")
    with STATE_LOCK:
        RUN_STATE["agents"]["messenger"]["status"] = "working"

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    sent_count = 0

    if bot_token and chat_id:
        for v in verdicts:
            if v.get("decision_state") == "BUY NOW":
                msg = format_telegram_signal_message(v, mode="SWING")
                res = send_telegram_alert(bot_token, chat_id, msg, symbol=v.get("symbol"), signal_type="BUY NOW")
                if res.get("sent"): sent_count += 1

    with STATE_LOCK:
        RUN_STATE["agents"]["messenger"]["stat1"] = sent_count
        RUN_STATE["agents"]["messenger"]["status"] = "done"
        RUN_STATE.update({
            "running": False,
            "active_step": "done",
            "completed_at": datetime.now().isoformat(),
            "verdicts": verdicts,
            "blocked_verdicts": blocked_verdicts,
            "avoid_verdicts": avoid_verdicts,
            "opportunities": opps,
            "decision_counts": dec_counts,
            "kpis": {
                "universe": len(evidences),
                "shortlisted": len(evidences),
                "intraday": len([v for v in verdicts if v.get("intraday_score",0) >= 70]),
                "swing": len([v for v in verdicts if v.get("swing_score",0) >= 70]),
                "buy_signals": dec_counts["buy_now"],
                "top_intraday": opps.get("top_intraday"),
                "top_swing": opps.get("top_swing")
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
            "buy_count": dec_counts["buy_now"],
            "status": "COMPLETED"
        })

    add_log("V3 decision pipeline cycle completed successfully!")

@app.route("/start", methods=["POST"])
@app.route("/scan", methods=["POST"])
@app.route("/analyze", methods=["POST"])
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
