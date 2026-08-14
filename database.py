import sqlite3
import json
import os
import time
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "marketpulse.db")

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id TEXT PRIMARY KEY,
        started_at TEXT,
        completed_at TEXT,
        engine TEXT,
        mode TEXT,
        universe_count INTEGER,
        shortlisted_count INTEGER,
        boom_count INTEGER,
        buy_count INTEGER,
        status TEXT,
        error TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        cap_segment TEXT,
        sector TEXT,
        updated_at TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        symbol TEXT,
        timestamp TEXT,
        data_json TEXT,
        data_quality_score INTEGER,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_outputs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        symbol TEXT,
        agent_id TEXT,
        output_json TEXT,
        timestamp TEXT,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verdicts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT,
        symbol TEXT,
        verdict TEXT,
        confidence INTEGER,
        marketpulse_score INTEGER,
        boom_score INTEGER,
        why TEXT,
        catalyst TEXT,
        buy_zone TEXT,
        target TEXT,
        stop_loss TEXT,
        rr_ratio REAL,
        validated INTEGER,
        validation_reason TEXT,
        timestamp TEXT,
        FOREIGN KEY(run_id) REFERENCES runs(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        run_id TEXT,
        signal_type TEXT,
        verdict TEXT,
        confidence INTEGER,
        marketpulse_score INTEGER,
        boom_score INTEGER,
        entry_price REAL,
        stop_loss REAL,
        target_1 REAL,
        target_2 REAL,
        rr_ratio REAL,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signal_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        signal_id INTEGER,
        event_type TEXT,
        price REAL,
        return_pct REAL,
        timestamp TEXT,
        FOREIGN KEY(signal_id) REFERENCES signals(id)
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telegram_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        msg_hash TEXT UNIQUE,
        symbol TEXT,
        signal_type TEXT,
        message_text TEXT,
        telegram_msg_id INTEGER,
        sent_at TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_regimes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        trend TEXT,
        momentum TEXT,
        breadth TEXT,
        volatility TEXT,
        risk_mode TEXT,
        score INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sector_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        sector_name TEXT,
        return_1d REAL,
        return_5d REAL,
        return_20d REAL,
        trend TEXT,
        momentum_rank INTEGER
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        total_signals INTEGER,
        buy_signals INTEGER,
        target_1_hits INTEGER,
        target_2_hits INTEGER,
        sl_hits INTEGER,
        win_rate REAL,
        profit_factor REAL,
        expectancy REAL,
        max_drawdown REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS backtest_runs (
        id TEXT PRIMARY KEY,
        strategy_name TEXT,
        run_date TEXT,
        total_trades INTEGER,
        win_rate REAL,
        profit_factor REAL,
        expectancy REAL,
        max_drawdown REAL,
        cagr REAL,
        trades_json TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        symbol TEXT PRIMARY KEY,
        added_at TEXT,
        notes TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS strategies (
        id TEXT PRIMARY KEY,
        name TEXT,
        rules_json TEXT,
        created_at TEXT
    )""")

    # Indexes for high performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_verdicts_symbol ON verdicts(symbol);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_run ON evidence(run_id);")

    conn.commit()
    conn.close()

def save_run(run_data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO runs (id, started_at, completed_at, engine, mode, universe_count, shortlisted_count, boom_count, buy_count, status, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_data.get("id"),
        run_data.get("started_at"),
        run_data.get("completed_at"),
        run_data.get("engine"),
        run_data.get("mode"),
        run_data.get("universe_count", 0),
        run_data.get("shortlisted_count", 0),
        run_data.get("boom_count", 0),
        run_data.get("buy_count", 0),
        run_data.get("status"),
        run_data.get("error")
    ))
    conn.commit()
    conn.close()

def save_verdict(run_id, v):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO verdicts (run_id, symbol, verdict, confidence, marketpulse_score, boom_score, why, catalyst, buy_zone, target, stop_loss, rr_ratio, validated, validation_reason, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        v.get("symbol"),
        v.get("verdict"),
        v.get("confidence"),
        v.get("marketpulse_score", 70),
        v.get("boom_score", 50),
        v.get("why"),
        v.get("catalyst"),
        v.get("buy_zone"),
        v.get("target"),
        v.get("stop_loss"),
        v.get("rr_ratio", 1.5),
        1 if v.get("validated") else 0,
        v.get("validation_reason", "Passed validation"),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()

def get_watchlist():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM watchlist ORDER BY added_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_to_watchlist(symbol, notes=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO watchlist (symbol, added_at, notes) VALUES (?, ?, ?)",
              (symbol.upper().replace(".NS",""), datetime.utcnow().isoformat(), notes))
    conn.commit()
    conn.close()

def remove_from_watchlist(symbol):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol.upper().replace(".NS",""),))
    conn.commit()
    conn.close()

# Initialize DB on module import
init_db()
