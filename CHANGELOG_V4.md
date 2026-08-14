# Changelog (V4) — MarketPulse Autonomous NSE Platform

All notable changes in MarketPulse V4 release.

## [v4.0.0] - 2026-08-14

### Added
- **Intraday Engine (`intraday_engine.py`)**: 5m primary timeframe, VWAP, EMA 9/20/50, Opening Range 9:15–9:30 IST, Volume Acceleration, Intraday Score /100.
- **Swing Engine (`swing_engine.py`)**: Daily & Weekly timeframes, 2–6 week horizon, EMA 20/50/100/200, RS vs NIFTY/Sector, Analyst upside, Swing Score /100.
- **False Breakout Detector (`false_breakout_engine.py`)**: Late Breakout Extension Guard (`FRESH BREAKOUT`, `HEALTHY MOMENTUM`, `EXTENDED`, `SEVERELY EXTENDED` -> `BUY BLOCKED` if $>10\%$ past resistance) and upper wick rejection detector.
- **Master Opportunity Ranking Engine (`opportunity_engine.py`)**: Unified Master Score /100 with component score breakdown. Enforces No-Forced-Signal Policy ("NO HIGH-CONVICTION SETUP").
- **Portfolio Concentration Guard (`risk_engine.py`)**: Sector concentration limits (`MAX_SECTOR_POSITIONS`, `MAX_OPEN_POSITIONS`, `MAX_PORTFOLIO_RISK`).
- **Strategy Lab 2.0 (`backtest.py`)**: Walk-Forward Testing (Train/Validation/Out-of-Sample) and Monte Carlo Robustness Simulation (500 trade-reordering iterations).
- **Telegram Pre-BOOM Alerts (`telegram.py`)**: `⚡ PRE-BOOM WATCH` alerts, `🚀 BREAKOUT CONFIRMED` alerts, `🟢 INTRADAY BUY` alerts, `📈 SWING BUY` alerts, and Daily Summaries with Top Blocked Opportunities.
- **SaaS UI Modal Drawers (`dashboard.html`)**: Watchlist Drawer, Strategy Lab Modal, Paste Stocks Modal, Evidence Explorer Drawer, Top Opportunities Cards, Top Blocked Opportunities Panel, and Live BOOM Scanner Filters.
- **Unit Test Suite (`tests/test_v2_engines.py`)**: 11 unit tests verifying all engines.

### Changed
- Refactored `scoring.py` to evaluate Intraday, Swing, Extension, and Master Opportunity scores.
- Refactored `app.py` REST routes to expose `/health`, `/opportunities`, `/sectors`, `/market-regime`, `/performance`, `/backtest`, `/paste-stocks`.
