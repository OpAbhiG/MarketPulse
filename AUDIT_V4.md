# Codebase & Quantitative Engine Audit Report (V4) — MarketPulse Platform

**Date**: 2026-08-14  
**Scope**: Full architectural audit of all MarketPulse V3 modules against statistical rigor, empirical performance tracking, look-ahead bias, and time-of-day execution controls.

---

## 1. System Component Classification Matrix

| Component | Status | Finding / Vulnerability | Remediation |
| :--- | :---: | :--- | :--- |
| **`decision_engine.py`** | **CORRECT** | 6 decision states enforce strict rules (`BUY NOW`, `CONFIRMATION`, `WATCH`, `AVOID`, `BLOCKED`, `NO TRADE`). No false UI states. | Retain and connect to Expected Value ($EV$) ranking. |
| **`intraday_engine.py`** | **WEAK** | Standard RVOL compared morning volume against full 6.5h daily volume without time-of-day adjustment. | Implement `time_of_day_rvol` scaling relative to NSE trading session elapsed minutes. |
| **`swing_engine.py`** | **CORRECT** | Multi-timeframe trend (Daily/Weekly), EMA 20/50/100/200, and RS metrics operate cleanly. | Add ADX trend strength and Volatility Contraction (VCP) detection. |
| **`false_breakout_engine.py`** | **PARTIALLY CORRECT** | Upper-wick rejection and extension distance (>10% past resistance) blocked extended signals. | Expand into dedicated Breakout Quality Model (`A+`, `A`, `B`, `WEAK`, `FALSE BREAKOUT RISK`). |
| **`performance.py`** | **MISSING** | Signal performance was logged generically without tracking forward +1D to +20D returns, MFE, MAE, or empirical win rates per score bucket. | Create `performance_engine.py` to record forward price paths and calculate empirical win rates. |
| **`scoring.py`** | **WEAK** | Master Score 0–100 assumed score 90 outperforms score 75 without empirical calibration. | Build `calibration_engine.py` to compute $P(+1R)$, $P(+2R)$, and Expected Value ($EV$). |
| **`opportunity_engine.py`** | **PARTIALLY CORRECT** | Ranked candidates by raw Master Score instead of expected risk-adjusted return ($EV$). | Re-rank candidates by Expected Value ($EV$) after costs and slippage. |
| **`risk_engine.py`** | **CORRECT** | Single-stock R:R, ATR14, and Portfolio Concentration limits block correlated trades. | Add Conservative / Normal / Aggressive position sizing modes. |
| **`backtest.py`** | **WEAK** | Included 0.15% transaction costs, but lacked comparison against Buy & Hold NIFTY 50 baseline or random entry baselines. | Implement Baseline Benchmark Engine (`NIFTY 50 Buy & Hold`, `Simple EMA`, `Random Entry`). |
| **`market_regime.py`** | **PARTIALLY CORRECT** | Evaluated NIFTY 50 and VIX, but lacked broad market advance/decline breadth metrics. | Create `breadth_engine.py` (% stocks above EMA20/EMA50/EMA200, A/D ratio). |

---

## 2. Identified Vulnerabilities & Technical Fixes

1. **RVOL Time-of-Day Distortion**:
   - *Problem*: At 9:25 AM, cumulative volume is naturally a fraction of daily volume, making unadjusted RVOL inaccurate.
   - *Fix*: Scale volume against expected cumulative volume percentage for elapsed minutes (9:15–15:30 IST).

2. **Uncalibrated Scoring Assumption**:
   - *Problem*: High raw scores do not guarantee higher win rates unless empirically calibrated against historical signal outcomes.
   - *Fix*: Create `calibration_engine.py` to track forward outcomes across score buckets ($90\text{--}100$, $80\text{--}89$, $75\text{--}79$, $<70$).

3. **Missing Baseline Benchmarks**:
   - *Problem*: Backtests showed positive return but did not demonstrate outperformance against NIFTY 50 Buy & Hold or simple moving average benchmarks.
   - *Fix*: Add baseline strategy comparisons in `backtest.py` and output `"PROVEN EDGE"` or `"NO DEMONSTRATED EDGE"`.
