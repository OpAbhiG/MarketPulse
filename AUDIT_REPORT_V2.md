# Complete Architecture & Code Quality Audit Report (V2) — MarketPulse Platform

**Date**: 2026-08-14  
**Scope**: Full codebase & UI audit covering `app.py`, `dashboard.html`, `scoring.py`, `screening.py`, `market_regime.py`, `sector_engine.py`, `risk_engine.py`, `signal_validator.py`, `verifier.py`, `database.py`, `performance.py`, `backtest.py`, `telegram.py`, `data_sources.py`.

---

## 1. Executive Summary

MarketPulse is a local Python/Flask application designed for NSE Indian stock momentum discovery, AI debate, risk calculation, backtesting, and Telegram alerts. While the base pipeline functions, a comprehensive audit revealed key UI button action gaps, missing Intraday vs Swing engine separation, missing late breakout extension guards, missing portfolio concentration controls, and missing empirical calibration matrices.

---

## 2. Detailed Findings & Audit Matrix

### A. Frontend & Button UX Audit (`dashboard.html`)
- ⚠️ **Watchlist Drawer**: Clicking `📋 Watchlist` button did not open an interactive drawer with add/remove symbol controls.
- ⚠️ **Strategy Lab Modal**: Clicking `🧪 Strategy Lab` button lacked an interactive modal interface for running backtests or Monte Carlo simulations.
- ⚠️ **Paste NSE Stocks Drawer**: Clicking `📋 Paste NSE Stocks` lacked a dedicated popup form for pasting NSE raw text and triggering immediate stock analysis.
- ⚠️ **Start Agents State Machine**: Button lacked visual progress steps (`Loading data` → `Scout` → `Technician` → `Fundamentalist` → `Newsdesk` → `Bull/Bear` → `Judge` → `Risk` → `Validator` → `Messenger`).
- ⚠️ **Missing Top Blocked Opportunities Section**: High-scoring stocks rejected by risk or validation gates were hidden instead of displayed in a dedicated panel with rejection rationale.
- ⚠️ **Missing Evidence Explorer**: Lacked an expandable drawer detailing the 10 score components ("Why this score?") with timestamps.

### B. Backend Flask Routes (`app.py`)
- ⚠️ **Deprecated Route Decorators**: Used `@app.get` and `@app.post` shorthand decorators which fail on certain Flask installations. Replaced with standard `@app.route(..., methods=[...])`.
- ⚠️ **Missing REST Routes**:
  - `GET /health`: System health monitor endpoint.
  - `GET /opportunities`: Unified top intraday and top swing recommendations.
  - `POST /analyze` & `POST /paste-stocks`: Custom ticker extraction and analysis endpoints.
  - `GET /history` & `GET /runs/<run_id>`: Execution run history logs.
  - `GET /strategies`: Custom strategy configuration endpoints.

### C. Recommendation Engine & Strategy Separation
- ⚠️ **Combined Intraday & Swing Scoring**: Intraday (5m timeframe, VWAP, EMA 9/20/50, Opening Range Breakout) and Swing trading (Daily/Weekly, 20/50/100/200 EMAs, RS vs NIFTY/Sector, Analyst targets) were mixed into a single scoring system.
- ⚠️ **Solution**: Separate into dedicated `intraday_engine.py` and `swing_engine.py` modules.

### D. Late Breakout Guard & False Breakout Detector (`screening.py`)
- ⚠️ **Chasing Extended Moves**: Missing a Late Breakout Detector (`FRESH BREAKOUT`, `HEALTHY MOMENTUM`, `EXTENDED`, `SEVERELY EXTENDED`). Stocks $>10\%$ past resistance level must be blocked with `"BREAKOUT TOO EXTENDED"`.
- ⚠️ **False Breakout Engine**: Missing upper wick, volume rejection, and resistance rejection checks.

### E. Risk Engine 2.0 & Portfolio Risk Guard (`risk_engine.py`)
- ⚠️ **Portfolio Concentration Risk**: Evaluated single-stock position sizing but lacked portfolio concentration guards (`MAX_OPEN_POSITIONS`, `MAX_SECTOR_POSITIONS`, `MAX_PORTFOLIO_RISK`, `MAX_CORRELATED_POSITIONS`). If 5 IT stocks triggered `BUY`, concentration risk was ignored.

### F. Strategy Lab 2.0, Walk-Forward, & Monte Carlo (`backtest.py`)
- ⚠️ **Overfitting & Walk-Forward Validation**: Missing Train / Validation / Out-of-Sample dataset splits to detect strategy decay across market regimes.
- ⚠️ **Monte Carlo Robustness Simulation**: Missing trade sequence randomization (1,000 iterations) to compute drawdown distribution, 5th/50th/95th percentile outcomes, and probability of ruin.

### G. Telegram Intelligence & Pre-BOOM Alerts (`telegram.py`)
- ⚠️ **Pre-BOOM Alerts**: Lacked `⚡ PRE-BOOM WATCH` ("No BUY yet. Waiting for confirmation.") and `🚀 BREAKOUT CONFIRMED` alert types.

---

## 3. Action Plan & Next Steps

1. **Fix All Button Actions**: Implement modal drawers for Watchlist, Strategy Lab, Paste Stocks, Evidence Explorer, and visual stepper for Start Agents.
2. **Build `intraday_engine.py` & `swing_engine.py`**: Separate Intraday (Score /100) and Swing (Score /100) evaluation modules.
3. **Build `opportunity_engine.py`**: Master Opportunity Ranking engine with Late Breakout Guard and No-Forced-Signal Policy ("NO HIGH-CONVICTION SETUP").
4. **Build `false_breakout_engine.py`**: Volume rejection and resistance rejection detector.
5. **Build Portfolio Risk Guard (`risk_engine.py`)**: Sector concentration limits and max open positions guard.
6. **Build Strategy Lab 2.0 (`backtest.py`)**: Walk-forward testing and Monte Carlo robustness simulation.
7. **Build Telegram Intelligence (`telegram.py`)**: Pre-BOOM Watch alerts and Breakout Confirmed alerts.
8. **Build System Health Monitor (`/health`)**: Status checks for Flask, SQLite, Market Data, LLM, and Telegram.
