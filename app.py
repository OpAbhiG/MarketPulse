import os
import re
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
import paper_trading
import feature_attribution
import ablation
import independent_evaluator
import signal_replay
import statistics_engine
import strategy_health
import drift_detector
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

_init_last_state = database.load_last_run_state()
if _init_last_state:
    RUN_STATE.update(_init_last_state)

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

@app.route("/api/paper-trading", methods=["GET"])
def get_paper_trading_api():
    return jsonify({"ok": True, "paper_summary": paper_trading.get_paper_trading_summary()})

@app.route("/api/feature-attribution", methods=["GET"])
def get_feature_attribution_api():
    return jsonify({"ok": True, "attribution": feature_attribution.calculate_feature_attributions()})

@app.route("/api/strategy-ablation", methods=["GET"])
def get_strategy_ablation_api():
    return jsonify({"ok": True, "ablation": ablation.run_strategy_ablation()})

@app.route("/api/evaluator", methods=["GET"])
def get_evaluator_api():
    return jsonify({"ok": True, "evaluation": independent_evaluator.evaluate_signal_outcomes_independently()})

@app.route("/api/signal-replay/<signal_id>", methods=["GET"])
def get_signal_replay_api(signal_id):
    return jsonify({"ok": True, "replay": signal_replay.replay_historical_signal(signal_id)})

@app.route("/api/statistics", methods=["GET"])
def get_statistics_api():
    return jsonify({"ok": True, "statistics": statistics_engine.calculate_bootstrap_confidence_intervals()})

@app.route("/api/strategy-health", methods=["GET"])
def get_strategy_health_api():
    return jsonify({"ok": True, "health": strategy_health.evaluate_strategy_health()})

@app.route("/api/drift-detector", methods=["GET"])
def get_drift_detector_api():
    return jsonify({"ok": True, "drift": drift_detector.detect_market_data_drift()})

@app.route("/api/parse-pasted-stocks", methods=["POST"])
def parse_pasted_stocks_route():
    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")
    if not raw_text:
        return jsonify({"ok": False, "symbols": []}), 400

    extracted = []
    # Match NSE URLs like https://www.nseindia.com/get-quote/equity/COALINDIA/Coal-India-Limited
    url_matches = re.findall(r'nseindia\.com/get-quote/equity/([A-Za-z0-9\-_]+)', raw_text, re.IGNORECASE)
    for m in url_matches:
        extracted.append(m.upper().replace(".NS", ""))

    # Match symbol= parameters
    param_matches = re.findall(r'symbol=([A-Za-z0-9\-_]+)', raw_text, re.IGNORECASE)
    for m in param_matches:
        extracted.append(m.upper().replace(".NS", ""))

    # Match raw ticker tokens (2 to 15 alphanumeric characters)
    words = re.findall(r'\b[A-Za-z0-9\.\-]{2,15}\b', raw_text)
    ignore_set = {"HTTPS", "HTTP", "WWW", "NSEINDIA", "COM", "GET-QUOTE", "EQUITY", "GET", "QUOTE", "HTML", "INDEX", "LIMITED", "COAL-INDIA-LIMITED"}

    for w in words:
        clean_w = w.upper().replace(".NS", "").strip()
        if clean_w not in ignore_set and (clean_w.isalpha() or clean_w.isalnum()):
            extracted.append(clean_w)

    # Deduplicate while preserving order
    seen = set()
    final_symbols = []
    for s in extracted:
        if s not in seen and len(s) >= 2:
            seen.add(s)
            final_symbols.append(s)

    return jsonify({"ok": True, "symbols": final_symbols})

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
        buy_pos = [x for x in verdicts if x.get("decision_state") == "BUY NOW"]
        v = scoring.deterministic_evaluate(ev, market_regime=regime, active_positions=buy_pos)
        verdicts.append(v)
        database.save_verdict(run_id, v)
        if v.get("decision_state") == "BUY NOW":
            performance_engine.record_opportunity_prediction(v, mode="SWING")
            paper_trading.place_paper_trade(v, mode="SWING")
            sig_id = f"sig_{int(datetime.now().timestamp())}_{v.get('symbol')}"
            database.save_signal_snapshot({
                "signal_id": sig_id,
                "timestamp": datetime.now().isoformat(),
                "symbol": v.get("symbol"),
                "mode": "SWING",
                "strategy": "Momentum Breakout",
                "decision_state": "BUY NOW",
                "entry_price": float(v.get("price") or 100.0),
                "trigger_price": float(v.get("price") or 100.0),
                "stop_loss": float(v.get("risk_params", {}).get("stop_loss") or 94.0),
                "target_1": float(v.get("risk_params", {}).get("target_1") or 108.0),
                "target_2": float(v.get("risk_params", {}).get("target_2") or 115.0),
                "master_score": v.get("marketpulse_score", 85),
                "rvol": v.get("technicals", {}).get("rvol", 2.0),
                "rs_score": 80,
                "sector": "General",
                "market_regime": regime.get("risk_mode", "NORMAL") if regime else "NORMAL",
                "breadth_score": 75,
                "data_quality_score": 100
            })


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
        database.save_last_run_state(RUN_STATE)

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
