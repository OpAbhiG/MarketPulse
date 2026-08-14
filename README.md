# MarketPulse — Autonomous NSE Stock Momentum & AI Signal Intelligence Platform

MarketPulse is a production-quality local **NSE Indian Stock Momentum Discovery, AI Debate, Risk Analysis, Backtesting, and Telegram Alert platform**.

It runs entirely locally on your Windows machine without broker order execution, cloud backends, or automated trading.

---

## 🚀 Key Features

1. **Market Regime Engine (`market_regime.py`)**: Analyzes NIFTY 50, NIFTY Bank, VIX, EMAs, and broad market breadth to classify Risk Mode (`RISK_ON`, `NORMAL`, `CAUTIOUS`, `RISK_OFF`).
2. **Sector Intelligence Engine (`sector_engine.py`)**: Computes sector 1D, 5D, 20D returns and Stock Relative Strength vs Sector.
3. **BOOM Scanner (`screening.py`)**: Calculates 0-100 BOOM Score and detects `EARLY BOOM`, `BOOM MOMENTUM`, and `CONFIRMED BREAKOUT` setups.
4. **Hallucination Protection (`verifier.py`)**: Validates numeric claims against ground-truth evidence before approving outputs.
5. **Risk Engine & Position Sizer (`risk_engine.py`)**: Calculates Entry Zone, Stop Loss, Target 1 ($\text{R:R} \ge 1.5$), Target 2 ($\text{R:R} \ge 3.0$), ATR14, and quantity sizing.
6. **Signal Validator (`signal_validator.py`)**: 8-gate validation gate ensuring only low-risk, high-quality setups issue `BUY` signals (`BUY BLOCKED` otherwise).
7. **SQLite Database Persistence (`database.py`)**: Tracks runs, evidence, signals, performance analytics, and backtests.
8. **Strategy Lab Backtesting (`backtest.py`)**: Historical momentum strategy backtester with walk-forward validation and no look-ahead bias.
9. **Telegram Signal Alerting (`telegram.py`)**: Sends validated BUY signals and daily reports with hash deduplication and standard disclaimer.
10. **Clean SaaS Dashboard (`dashboard.html`)**: Responsive UI with embedded TradingView candlestick charts.

---

## 🛠️ Installation & Setup Guide

1. Clone or download the repository.
2. Open terminal in project folder:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run the dashboard:
   ```bash
   python app.py
   # OR run double-click: start_dashboard.bat
   ```
4. Access the web dashboard in your browser:
   👉 **`http://localhost:5000`** *(or `http://127.0.0.1:5000`)*

---

## ⚠️ Disclaimer
> Analysis only. No trade was placed. Not investment advice. MarketPulse is an analysis and signal-generation platform only and does not execute broker orders or guarantee returns.
