# Changelog (V6) — MarketPulse Autonomous NSE Platform

All notable changes in MarketPulse V6 release.

## [v6.0.0] - 2026-08-14

### Added
- **Signal Performance Engine (`performance_engine.py`)**: SQLite persistence (`performance_predictions` table) tracking forward outcomes (+1D to +20D for Swing; +5m to +EOD for Intraday), MFE, MAE, Win Rate, Profit Factor, Expectancy.
- **Empirical Score Calibration Engine (`calibration_engine.py`)**: Calibration matrix verifying $P(+1R)$, $P(+2R)$, $P(\text{stop})$, and Expected R across score buckets ($90\text{--}100$, $80\text{--}89$, $75\text{--}79$, $<70$).
- **Breakout Quality Engine (`breakout_quality_engine.py`)**: Breakout Quality Model (`A+`, `A`, `B`, `WEAK`, `FALSE BREAKOUT RISK`, `EXTENDED`, `NO TRADE`).
- **Market Breadth Engine (`breadth_engine.py`)**: Advance/Decline ratio, % stocks above EMA20/EMA50/EMA200, 20D Highs/Lows -> Breadth Score /100.
- **Event Risk Engine (`event_risk.py`)**: Event risk detector (earnings, corporate actions, regulatory events).
- **Time-of-Day Adjusted Intraday RVOL (`intraday_engine.py`)**: Scaling relative to elapsed trading minutes (9:15–15:30 IST).
- **Expected Value ($EV$) Ranking (`opportunity_engine.py`)**: Candidates ranked by Expected Value ($EV$) after costs and slippage.
- **Baseline Benchmarking Engine (`backtest.py`)**: Outperformance comparison against NIFTY 50 Buy & Hold, Simple EMA, and Random Entry baselines. Displays `"PROVEN EDGE"`.
- **Documentation Suite**: `SCORING_METHODOLOGY_V4.md`, `IMPLEMENTATION_REPORT_V4.md`, `PERFORMANCE_REPORT.md`, `STRATEGY_BENCHMARK_REPORT.md`.

### Changed
- Updated `dashboard.html` with Proven Edge Banner and Action Center updates.
