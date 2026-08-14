# Changelog (V7) — MarketPulse Autonomous NSE Platform

All notable changes in MarketPulse V7 release.

## [v7.0.0] - 2026-08-14

### Added
- **Paper Trading Engine & Shadow Mode (`paper_trading.py`)**: Production pipeline integration, order lifecycle (`OPEN`, `TARGET1`, `TARGET2`, `STOP`, `INVALIDATED`, `EXPIRED`, `CLOSED`), Net P&L tracking, Shadow Mode indicator.
- **Feature Attribution Engine (`feature_attribution.py`)**: Incremental delta profit factor and expectancy metrics for RVOL, Relative Strength, Sector Strength, Regime, and Breakout Quality.
- **Strategy Ablation Engine (`ablation.py`)**: Component removal tests evaluating edge impact.
- **Parameter Sensitivity & Edge Status Rating (`backtest.py`)**: Neighborhood parameter testing (`ROBUST` / `FRAGILE`) and 7 Edge Status categories (`NOT ENOUGH DATA`, `PROMISING`, `OOS VALIDATED`, `ROBUST EDGE`, `EDGE DETERIORATING`, `NO DEMONSTRATED EDGE`, `OVERFIT RISK`).
- **Strategy Decay Monitoring (`performance_engine.py`)**: Rolling trade window tracking (last 20, 50, 100 trades) detecting `EDGE DETERIORATING`.
- **Survivorship Bias Warning Tag (`dashboard.html` & `backtest.py`)**: Explicit warning for historical constituent evaluations.
- **REST API Endpoints**: `/api/paper-trading`, `/api/feature-attribution`, `/api/strategy-ablation`.
- **Documentation Suite**: `V5_AUDIT.md`, `PAPER_TRADING_GUIDE.md`, `EDGE_VALIDATION_REPORT.md`, `FEATURE_ATTRIBUTION_REPORT.md`, `STRATEGY_ROBUSTNESS_REPORT.md`.

### Changed
- Updated `dashboard.html` Action Center header with `MARKETPULSE EDGE STATUS` research panel.
