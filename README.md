# MarketPulse V2 — Autonomous NSE Indian Stock Momentum Discovery, AI Debate, Risk Analysis, Backtesting, & Telegram Alert Platform

MarketPulse is a **LOCAL**, Python + Flask based NSE Indian Stock Intraday & Swing Momentum Discovery, Signal Validation, Risk Management, Backtesting, and Research Platform.

---

## 🌟 Core Features

- 🏛️ **Market Regime 2.0 Engine**: Evaluates NIFTY 50, Bank NIFTY, India VIX, EMAs, and Risk Modes (`STRONG_RISK_ON`, `RISK_ON`, `NORMAL`, `CAUTIOUS`, `RISK_OFF`).
- ⚡ **Intraday Engine (`intraday_engine.py`)**: 5m primary timeframe, VWAP, EMA 9/20/50, Opening Range (9:15–9:30 IST), Volume Acceleration, Intraday Score /100.
- 📈 **Swing Engine (`swing_engine.py`)**: Daily & Weekly timeframes, 2–6 week horizon, EMA 20/50/100/200, RS vs NIFTY/Sector, Analyst upside, Swing Score /100.
- 🛑 **Late Breakout Extension Guard (`false_breakout_engine.py`)**: Flags setups $>10\%$ past resistance as `"BREAKOUT — TOO EXTENDED"` and BLOCKS BUY signals.
- 🛡️ **Portfolio Concentration Guard (`risk_engine.py`)**: Enforces sector concentration limits (`MAX_SECTOR_POSITIONS`, `MAX_OPEN_POSITIONS`, `MAX_PORTFOLIO_RISK`).
- 🧪 **Strategy Lab 2.0 & Monte Carlo (`backtest.py`)**: Walk-Forward Testing (Train/Validation/Out-of-Sample) and Monte Carlo Robustness Simulation (500 trade-reordering iterations).
- 📱 **Telegram Intelligence (`telegram.py`)**: `⚡ PRE-BOOM WATCH` alerts, `🚀 BREAKOUT CONFIRMED` alerts, `🟢 INTRADAY BUY` alerts, `📈 SWING BUY` alerts, and Daily Reports with Top Blocked Opportunities.
- 🎨 **Production SaaS UI (`dashboard.html`)**: Responsive modal drawers for Watchlist, Strategy Lab, Paste Stocks, Evidence Explorer, Top Opportunities Cards, Top Blocked Opportunities Panel, and Live BOOM Scanner Filters.

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
