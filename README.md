# MarketPulse V5 — Empirical Edge Validation, Paper Trading, Feature Attribution, & Strategy Robustness Platform

MarketPulse is a **LOCAL**, Python + Flask based NSE Indian Stock Intraday & Swing Momentum Discovery, Trading Decision Intelligence, Signal Performance Tracking, Paper Trading, Strategy Ablation, and Out-of-Sample Edge Validation Platform.

---

## 🌟 Core V5 Features

- 📊 **MarketPulse Edge Status Engine**: Transparent research panel categorizing strategies into strict empirical statuses (`NOT ENOUGH DATA`, `PROMISING`, `OOS VALIDATED`, `ROBUST EDGE`, `EDGE DETERIORATING`, `NO DEMONSTRATED EDGE`, `OVERFIT RISK`).
- 📝 **Paper Trading & Live Shadow Mode (`paper_trading.py`)**: Executes on top of the production pipeline (`market data` → `screening` → `scoring` → `decision` → `risk` → `paper trade`). Tracks trade lifecycles (`OPEN`, `TARGET1`, `TARGET2`, `STOP`, `CLOSED`) and outputs `SHADOW SIGNAL` during market hours.
- 🔬 **Feature Attribution & Strategy Ablation (`feature_attribution.py` & `ablation.py`)**: Measures incremental delta profit factor for RVOL, Relative Strength, Sector Strength, and Regime filters.
- 🧪 **Parameter Sensitivity & Strategy Lab 2.0 (`backtest.py`)**: Neighborhood parameter testing ($1.3x\text{--}2.0x$ RVOL) evaluating parameter stability (`ROBUST` vs `FRAGILE`), Walk-Forward splits, Monte Carlo simulations, and realistic transaction costs (0.15%).
- 📉 **Strategy Decay Monitor (`performance_engine.py`)**: Rolling trade window tracking (last 20, 50, 100 trades) to detect `EDGE DETERIORATING`.
- ⚠️ **Survivorship Bias Warning Tag**: Explicit warning when historical tests evaluate surviving constituents without point-in-time universe changes.
- 🎨 **Action Center & Edge Research Panel (`dashboard.html`)**: Live Market Regime, India VIX, Today's Decision Breakdown, Edge Status panel, and Paper Trading Performance dashboard.

---

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch MarketPulse Server**:
   ```bash
   python app.py
   ```
   Open **http://localhost:5000** in your browser.

3. **Run Unit Test Suite (30+ Tests)**:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

## ⚠️ Disclaimer

MarketPulse is an **empirical analysis, paper trading, and systematic research tool only**. It does NOT execute trades or connect to live broker execution APIs. No real trade is placed. Output is strictly for informational and educational research purposes.
