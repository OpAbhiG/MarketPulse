# MarketPulse V3 — Autonomous NSE Indian Stock Momentum Discovery, AI Debate, Risk Analysis, Backtesting, & Telegram Alert Platform

MarketPulse is a **LOCAL**, Python + Flask based NSE Indian Stock Intraday & Swing Momentum Discovery, Trading Decision Intelligence, Signal Validation, Risk Management, Backtesting, and Research Platform.

---

## 🌟 Core Features

- 🟢 **Master Decision Engine (`decision_engine.py`)**: Enforces 6 strict decision states (`🟢 BUY NOW`, `🟡 BUY ON CONFIRMATION`, `🔵 WATCH`, `🔴 AVOID`, `🟠 BLOCKED`, `⚪ NO TRADE`).
- ⚡ **Intraday Engine (`intraday_engine.py`)**: 5m primary decision timeframe, VWAP, EMA 9/20/50, Opening Range (9:15–9:30 IST), Volume Acceleration, Intraday Score /100.
- 📈 **Swing Engine (`swing_engine.py`)**: Daily & Weekly timeframes, 2–6 week horizon, EMA 20/50/100/200, RS vs NIFTY/Sector, Analyst upside, Swing Score /100.
- 🛑 **Late Breakout Extension Guard (`false_breakout_engine.py`)**: Flags setups $>10\%$ past resistance as `"BREAKOUT — TOO EXTENDED"` and BLOCKS BUY signals.
- 🔴 **STOCKS TO AVOID Section**: Dedicated panel showing explicit rejection rationale (❌ Low RVOL, ❌ Weak RS, ❌ Below EMA20, ❌ Poor R:R, ❌ Market regime, ❌ Extended breakout, ❌ False breakout risk).
- 🛡️ **Portfolio Concentration Guard (`risk_engine.py`)**: Enforces sector concentration limits (`MAX_SECTOR_POSITIONS`, `MAX_OPEN_POSITIONS`, `MAX_PORTFOLIO_RISK`).
- 🧪 **Strategy Lab 2.0 & Monte Carlo (`backtest.py`)**: Realistic NSE transaction cost model (STT, Brokerage, Slippage), Walk-Forward Testing, and Monte Carlo Robustness Simulation.
- 📱 **Telegram Intelligence (`telegram.py`)**: `⚡ PRE-BOOM WATCH` alerts, `🚀 BREAKOUT CONFIRMED` alerts, `🟢 BUY NOW` alerts, and Daily Reports with Top Blocked Opportunities.
- 🎨 **Action Center Dashboard (`dashboard.html`)**: Market Regime status, NIFTY 50, VIX, Data age, Today's Decision Breakdown, mode toggles (`[ INTRADAY ]` vs `[ SWING ]`), and decision filter buttons.

---

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. **Launch MarketPulse**:
   ```bash
   python app.py
   ```
   Open **http://localhost:5000** in your browser.

4. **Run Unit Test Suite**:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

## ⚠️ Disclaimer

MarketPulse is an **analysis and systematic research tool only**. It does NOT execute trades or connect to broker execution APIs. No trade was placed. All output is strictly for informational and educational purposes. Not investment advice.
