# Architecture & Code Quality Audit Report — MarketPulse Platform

**Date**: 2026-08-14  
**Scope**: Complete codebase inspection of `app.py`, `dashboard.html`, `scoring.py`, `screening.py`, `market_regime.py`, `sector_engine.py`, `risk_engine.py`, `signal_validator.py`, `verifier.py`, `database.py`, `performance.py`, `backtest.py`, `telegram.py`, `data_sources.py`.

---

## 1. Overview of Existing Architecture

MarketPulse is a local Python/Flask application that scans NSE stock tickers, fetches Yahoo Finance market data (`data_sources.py`), calculates technical/momentum metrics, runs Bull vs Bear AI debates (`llm.py`), scores candidates (`scoring.py`), validates signals (`signal_validator.py`), calculates risk/position sizing (`risk_engine.py`), logs runs to SQLite (`database.py`), and notifies Telegram (`telegram.py`).

---

## 2. Key Issues & Vulnerabilities Identified

### A. Screening & Breakout Engine (`screening.py`)
- ⚠️ **Missing Late Breakout Protection**: Currently, a stock with a massive price gain is tagged as `CONFIRMED BREAKOUT` even if it is already extended $>10\%$ above its breakout resistance level. This creates a high risk of chasing top-of-move traps.
- ⚠️ **EARLY BOOM Signal Guard**: `EARLY BOOM` setups were not explicitly isolated from `BUY` signal generation. An `EARLY BOOM` must remain `WATCH` until confirmation occurs.
- ⚠️ **Fixed Breakout Distances**: Missing explicit `distance_to_breakout_pct` and `invalidation_level` fields in screening outputs.

### B. Master Scoring Model (`scoring.py`)
- ⚠️ **Component Breakdown Visibility**: The Master MarketPulse Score was calculated as a composite value, but individual component contributions (Technical 20, RVOL 15, Breakout 15, Trend 10, Relative Strength 10, Sector 10, Regime 5, Liquidity 5, Risk/Reward 5, Data Quality 5 = 100) were not saved in JSON or exposed to the dashboard.

### C. Sector Intelligence & Relative Strength (`sector_engine.py`)
- ⚠️ **Multi-Timeframe RS**: Relative Strength was only evaluated over a 20-day window. Missing 1D, 5D, 20D, and 60D comparison matrices (Stock vs NIFTY, Stock vs Sector, Sector vs NIFTY).
- ⚠️ **Relative Strength Score**: Missing a 0–100 normalized RS Score for stock ranking.

### D. Market Regime 2.0 (`market_regime.py`)
- ⚠️ **Missing `STRONG_RISK_ON` State**: Market regime classified `RISK_ON`, `NORMAL`, `CAUTIOUS`, `RISK_OFF`, but lacked `STRONG_RISK_ON` and `regime_confidence` (0–100).
- ⚠️ **Configurable Regime Policy**: The policy mapping regime states to signal strictness needed configurable overrides.

### E. Risk Engine & Portfolio Concentration (`risk_engine.py`)
- ⚠️ **Missing Portfolio-Level Limits**: Risk engine calculated single-stock position sizing, but lacked portfolio-level checks (`MAX_POSITION_PERCENT`, `MAX_OPEN_POSITIONS`, `MAX_SECTOR_POSITIONS`, `MAX_PORTFOLIO_RISK`). If 5 IT stocks trigger `BUY`, portfolio concentration risk was ignored.

### F. Prediction vs Reality & Calibration (`performance.py`)
- ⚠️ **Empirical Score Validation**: Missing tracking for BOOM Score vs Actual 5-Day Returns (+1D, +3D, +5D, +10D, +20D returns, MFE, MAE) to prove whether the score has empirical predictive value.
- ⚠️ **Agent Directional Accuracy**: Agent accuracy was tracked generically without comparing Bull vs Bear vs Judge predictions against actual price excursion outcomes.

### G. Strategy Lab & Backtesting (`backtest.py`)
- ⚠️ **Walk-Forward Testing & Overfitting Warnings**: Missing Train/Validation/Out-of-Sample split to detect strategy decay across market regimes.
- ⚠️ **Monte Carlo Robustness Test**: Missing trade sequence randomization to compute drawdown distribution and probability of ruin.

### H. Telegram Intelligence & Pre-BOOM Alerts (`telegram.py`)
- ⚠️ **Pre-BOOM Alerts**: Lacked `⚡ PRE-BOOM WATCH` alert type notifying users of approaching breakouts before confirmation.

### I. Frontend SaaS Interface (`dashboard.html`)
- ⚠️ **Blocked Signals Section**: Dashboard displayed latest verdicts, but did not feature a dedicated **"Top Blocked Opportunities"** panel showing why high-scoring stocks were rejected (e.g. poor R:R or regime block).
- ⚠️ **"Why This Score?" Evidence Explorer**: Missing expandable drawer breaking down all 10 score components with source timestamps.

---

## 3. Remediations & Upgrade Strategy

1. **Refactor `screening.py`**: Add Late Breakout Detector (`BREAKOUT — TOO EXTENDED`) and output `EARLY BOOM` with breakout distance and invalidation level.
2. **Refactor `scoring.py`**: Implement 10-component Master MarketPulse Score (100 pts) with full JSON component breakdown.
3. **Refactor `sector_engine.py`**: Add 1D/5D/20D/60D Relative Strength matrix and 0-100 RS Score.
4. **Refactor `market_regime.py`**: Add `STRONG_RISK_ON`, Regime Confidence (0-100), and configurable Regime Policy.
5. **Refactor `risk_engine.py`**: Implement Portfolio Concentration Guard (`MAX_SECTOR_POSITIONS`, `MAX_OPEN_POSITIONS`, `MAX_PORTFOLIO_RISK`).
6. **Refactor `backtest.py`**: Add Walk-Forward testing (Train/Validation/Out-of-Sample) and Monte Carlo Robustness simulation.
7. **Refactor `performance.py`**: Add Prediction vs Reality matrix (BOOM Score vs 5D return, MFE/MAE).
8. **Update `telegram.py`**: Add `PRE-BOOM WATCH` and `BREAKOUT CONFIRMED` alert types.
9. **Upgrade `dashboard.html`**: Add Top Blocked Opportunities panel, Evidence Explorer, Live BOOM Scanner filters, and Strategy Lab 2.0.
