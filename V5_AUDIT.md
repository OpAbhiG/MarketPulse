# Codebase & Edge Validation Audit Report (V5) — MarketPulse Platform

**Date**: 2026-08-14  
**Scope**: Comprehensive audit of all V4 modules against empirical out-of-sample edge validation, paper trading execution, survivorship bias, feature attribution, and parameter sensitivity.

---

## 1. System Component Classification Matrix

| Component | Status | Finding / Risk | Remediation in V5 |
| :--- | :---: | :--- | :--- |
| **`performance_engine.py`** | **PARTIALLY CORRECT** | Tracked signal predictions, but lacked distinct paper trading lifecycle states (`OPEN`, `TARGET1`, `TARGET2`, `STOP`, `INVALIDATED`, `EXPIRED`, `CLOSED`). | Build `paper_trading.py` with full order lifecycle & Shadow Mode. |
| **`calibration_engine.py`** | **CORRECT** | Bucket matrix ($90\text{--}100$, $80\text{--}89$, $75\text{--}79$, $<70$) calibrated win rates. | Expand to 7 score buckets ($90\text{--}100$, $85\text{--}89$, $80\text{--}84$, $75\text{--}79$, $70\text{--}74$, $65\text{--}69$, $<65$) and add `SCORE CALIBRATION FAILURE` warning. |
| **`breakout_quality_engine.py`** | **CORRECT** | Classifies `A+`, `A`, `B`, `WEAK`, `FALSE BREAKOUT RISK`, `EXTENDED`. | Retain and integrate into feature attribution metrics. |
| **`breadth_engine.py`** | **CORRECT** | Computes A/D ratio and % stocks above EMA20/EMA50/EMA200. | Retain and link to regime stability checks. |
| **`event_risk.py`** | **CORRECT** | Detects earnings and corporate event risks. | Retain and flag event risk in trade plans. |
| **`intraday_engine.py`** | **CORRECT** | Time-of-day RVOL scaling (`time_of_day_rvol`) prevents morning volume distortion. | Retain and connect to paper trading engine. |
| **`swing_engine.py`** | **CORRECT** | Multi-timeframe trend & RS evaluation works cleanly. | Retain and evaluate feature attribution. |
| **`opportunity_engine.py`** | **CORRECT** | Expected Value ($EV$) optimization and No-Forced-Signal policy work as intended. | Connect to parameter sensitivity analysis. |
| **`backtest.py`** | **WEAK** | Included 0.15% costs and baseline outperformance, but displayed simplistic "PROVEN EDGE" banner without OOS trade sample size check. | Replace simplistic banner with transparent `EDGE STATUS` research panel (`NOT ENOUGH DATA`, `PROMISING`, `OOS VALIDATED`, `ROBUST EDGE`, `EDGE DETERIORATING`). |
| **`decision_engine.py`** | **CORRECT** | 6-state decision machine prevents UI state contradictions. | Retain and feed signals into paper trading engine. |
| **`risk_engine.py`** | **CORRECT** | R:R, ATR, and Portfolio Concentration Guards function properly. | Retain. |
| **`signal_validator.py`** | **CORRECT** | 8-gate validation gate module. | Retain. |
| **`data_sources.py`** | **WEAK** | Historical backtests evaluate current universe (`universe.json`) rather than point-in-time historical constituents. | Add explicit `SURVIVORSHIP BIAS RISK` warning when point-in-time universe changes are absent. |

---

## 2. Technical Vulnerabilities & Fix Plan

1. **Unqualified "PROVEN EDGE" Banner**:
   - *Problem*: Displaying "PROVEN EDGE" based solely on historical backtests creates false confidence.
   - *Fix*: Replace banner with `MARKETPULSE EDGE STATUS` research panel displaying statuses: `NOT ENOUGH DATA`, `PROMISING`, `OOS VALIDATED`, `ROBUST EDGE`, `EDGE DETERIORATING`, `NO DEMONSTRATED EDGE`, `OVERFIT RISK`.

2. **Paper Trading & Shadow Mode Gap**:
   - *Problem*: Backtest performance was not validated against live paper trade execution.
   - *Fix*: Build `paper_trading.py` utilizing the exact same production signal pipeline (`market data` → `screening` → `scoring` → `decision` → `risk` → `paper trade`).

3. **Survivorship Bias in Historical Datasets**:
   - *Problem*: Historical backtests evaluate current surviving stocks.
   - *Fix*: Flag `SURVIVORSHIP BIAS RISK` in backtest reports.

4. **Missing Component Attribution & Strategy Ablation**:
   - *Problem*: System lacked quantifiable proof of which features (RVOL, RS, Sector, Regime) contribute to edge.
   - *Fix*: Build `feature_attribution.py` and `ablation.py`.
