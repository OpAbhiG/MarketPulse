# Changelog (V5) — MarketPulse Autonomous NSE Platform

All notable changes in MarketPulse V5 release.

## [v5.0.0] - 2026-08-14

### Added
- **Master Decision Engine (`decision_engine.py`)**: 6 strict decision states (`🟢 BUY NOW`, `🟡 BUY ON CONFIRMATION`, `🔵 WATCH`, `🔴 AVOID`, `🟠 BLOCKED`, `⚪ NO TRADE`). Formats explicit `WHY BUY?`, `WHY NOT BUY?`, `TRIGGER`, `INVALIDATION`, and `AVOID REASONS`.
- **MarketPulse Action Center Header**: Today's Decision Breakdown (`BUY NOW`, `BUY ON CONFIRMATION`, `WATCH`, `AVOID`, `BLOCKED`). If `BUY NOW = 0`, explicitly displays `"NO HIGH-CONVICTION BUY TODAY"`.
- **🔴 STOCKS TO AVOID Panel**: Dedicated dashboard panel displaying explicit bulleted rejection reasons (❌ Low RVOL, ❌ Weak RS, ❌ Poor R:R, ❌ Market regime, ❌ Extended breakout, ❌ False breakout risk).
- **Realistic Transaction Cost Model (`backtest.py`)**: Incorporates STT, Brokerage, Exchange charges, GST, SEBI charges, Stamp duty, and Slippage (~0.15% per trade) into backtest P&L.
- **Documentation Suite**: `SCORING_METHODOLOGY.md`, `TRADING_DECISION_GUIDE.md`, `IMPLEMENTATION_REPORT_V3.md`, `TEST_REPORT_V3.md`.
- **Unit Test Suite (`tests/test_v3_decisions.py`)**: Adds 4 unit tests verifying decision states and No-Forced-Signal policy.

### Changed
- Refactored `opportunity_engine.py` to ensure `top_pick` is ONLY set if a candidate earns `BUY NOW` status. Resolves UI contradictions.
- Refactored `dashboard.html` with Action Center, mode toggles (`[ INTRADAY ]` vs `[ SWING ]`), decision filter buttons (`[ ALL ]` `[ BUY NOW ]` `[ CONFIRMATION ]` `[ WATCH ]` `[ AVOID ]`), and standardized Stock Decision Cards.
