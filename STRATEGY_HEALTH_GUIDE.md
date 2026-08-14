# Strategy Health & Kill-Switch Guide — MarketPulse V6

**Document Version**: 6.0  
**Scope**: Operational logic for Strategy Health state transitions and automatic BUY signal blocking.

---

## 1. Strategy Health States

| Health State | Criteria | Strategy Action |
| :---: | :--- | :--- |
| **`HEALTHY`** | Rolling expectancy $> 0.5 R$, Win Rate $\ge 55\%$ | Normal Alert Execution |
| **`WATCH`** | Rolling expectancy $0.0 R\text{--}0.5 R$, Win Rate $50\text{--}54\%$ | Monitored Execution / Surveillance |
| **`PAUSED`** | Rolling expectancy $< 0.0 R$, Win Rate $< 45\%$ | **AUTOMATIC KILL-SWITCH ACTIVE** (BUY signals blocked) |
| **`RETIRED`** | Strategy persistently negative across multiple market cycles | Strategy Deactivated |
