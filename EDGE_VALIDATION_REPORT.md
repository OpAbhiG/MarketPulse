# Edge Validation & Out-of-Sample Research Report — MarketPulse V5

**Date**: 2026-08-14  
**Scope**: Empirical statistical criteria for strategy edge classification.

---

## 1. MarketPulse Edge Classification Categories

To prevent false confidence, MarketPulse enforces 7 strict Edge Status categories:

| Status Badge | Criteria / Requirements | Strategy Rating |
| :--- | :--- | :---: |
| **`OOS VALIDATED`** | Out-of-Sample trades $\ge 30$, OOS Win Rate $\ge 60\%$, Profit Factor $\ge 1.5$, Overfit Risk = LOW | **APPROVED** |
| **`ROBUST EDGE`** | OOS Validated + Parameter Sensitivity = ROBUST across neighborhood testing | **HIGH CONVICTION** |
| **`PROMISING`** | In-sample Win Rate $\ge 55\%$, Profit Factor $\ge 1.4$, but OOS trade count $< 30$ | **MORE DATA NEEDED** |
| **`NOT ENOUGH DATA`** | Total trade sample size $< 30$ trades | **UNRATED** |
| **`OVERFIT RISK`** | In-sample win rate vs Out-of-sample win rate delta $\ge 15.0\%$ | **WARNING** |
| **`EDGE DETERIORATING`** | Rolling 20-trade win rate drops $>12\%$ below historical baseline | **WARNING** |
| **`NO DEMONSTRATED EDGE`** | Profit factor $< 1.3$ or strategy CAGR fails to beat NIFTY 50 Buy & Hold | **REJECTED** |
