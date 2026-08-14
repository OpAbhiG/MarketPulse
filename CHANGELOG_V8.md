# Changelog (V8) — MarketPulse Autonomous NSE Platform

All notable changes in MarketPulse V8 release.

## [v8.0.0] - 2026-08-14

### Added
- **Independent Signal Evaluator (`independent_evaluator.py`)**: Observer-only module recording forward price paths without modifying signal scores or decisions.
- **Immutable Signal Snapshots & Signal Replay (`signal_replay.py` & `database.py`)**: Point-in-time state recording to SQLite `signal_snapshots` table and full Signal Replay UI (`WHAT MARKETPULSE KNEW` vs `WHAT ACTUALLY HAPPENED`).
- **Statistical Confidence & Bootstrap Engine (`statistics_engine.py`)**: Calculates 95% Confidence Intervals for Win Rate, Profit Factor, Expectancy, and Average R.
- **Strategy Health Kill-Switch (`strategy_health.py`)**: States (`HEALTHY`, `WATCH`, `PAUSED`, `RETIRED`). Automatically blocks BUY signals when `PAUSED`.
- **Data & Regime Drift Detector (`drift_detector.py`)**: Compares market ATR, RVOL, and volatility against training distributions to flag `DATA/REGIME DRIFT WARNING`.
- **Slippage Stress Testing (`backtest.py`)**: Stress tests slippage rates ($0.05\%\text{--}0.50\%$) and computes break-even slippage thresholds.
- **V6 REST API Endpoints**: `/api/evaluator`, `/api/signal-replay/<signal_id>`, `/api/statistics`, `/api/strategy-health`, `/api/drift-detector`.
- **Documentation Suite**: `V6_AUDIT.md`, `EDGE_VALIDATION_METHODOLOGY.md`, `SIGNAL_REPLAY_GUIDE.md`, `STRATEGY_HEALTH_GUIDE.md`, `STATISTICAL_VALIDATION_REPORT.md`.

### Changed
- Updated `dashboard.html` Action Center with V6 Edge Monitor, Strategy Health badges, and side-by-side performance matrix (`BACKTEST` vs `OOS` vs `SHADOW` vs `PAPER`).
