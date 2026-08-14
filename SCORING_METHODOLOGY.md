# Scoring Methodology — MarketPulse Quantitative Scoring System

**Document Version**: 3.0  
**Scope**: Exact mathematical formulas, weights, thresholds, and normalization rules for MarketPulse Master Score (0–100).

---

## 1. Master Score Component Breakdown (Total = 100 Points)

MarketPulse calculates a deterministic **Master Score (0–100)** across 10 independent component weights:

$$\text{Master Score} = \sum_{i=1}^{10} C_i$$

| Component | Weight | Max Score | Condition / Threshold |
| :--- | :---: | :---: | :--- |
| **Technical Trend** | 20% | 20 pts | Price > EMA20, EMA20 > EMA50, Price > SMA200 |
| **Relative Volume (RVOL)** | 15% | 15 pts | $\text{RVOL} \ge 1.5x$ average 20-day volume |
| **Breakout Quality** | 15% | 15 pts | 52-week position $\ge 80\%$, not extended |
| **Trend Alignment** | 10% | 10 pts | Moving average alignment across timeframes |
| **Relative Strength (RS)** | 10% | 10 pts | Stock 20D Return > Sector 20D Return |
| **Sector Strength** | 10% | 10 pts | Sector 20D return $> 1.0\%$ |
| **Market Regime** | 5% | 5 pts | Risk Mode is `STRONG_RISK_ON` or `RISK_ON` |
| **Liquidity Score** | 5% | 5 pts | Average daily volume $\ge 50,000$ shares |
| **Risk/Reward Ratio** | 5% | 5 pts | $\text{R:R Ratio} \ge 1.5$ |
| **Data Quality Score** | 5% | 5 pts | Evidence data completeness $\ge 75\%$ |

---

## 2. Decision State Machine Rules

| Decision State | Badge | Master Score | Judge Verdict | R:R | Data Quality | Extension Guard |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **BUY NOW** | 🟢 | $\ge 80$ | BUY | $\ge 1.5$ | $\ge 75\%$ | Not Extended ($<10\%$) |
| **BUY ON CONFIRMATION** | 🟡 | $\ge 75$ | WATCH / BUY | $\ge 1.5$ | $\ge 75\%$ | Trigger price specified |
| **WATCH** | 🔵 | $65\text{--}74$ | WATCH | Any | $\ge 60\%$ | Setup monitoring |
| **AVOID** | 🔴 | $<65$ | AVOID | $<1.5$ | Any | Weak technicals / Extended |
| **BLOCKED** | 🟠 | $\ge 75$ | BUY | Any | Any | Portfolio concentration limit |
| **NO TRADE** | ⚪ | Default | — | — | — | No candidate qualifies |
