# Feature Attribution & Strategy Ablation Report — MarketPulse V5

**Date**: 2026-08-14  
**Scope**: Incremental contribution and component ablation testing across MarketPulse scoring features.

---

## 1. Feature Attribution Summary

| Feature Name | Baseline PF | With Feature PF | $\Delta$ Profit Factor | $\Delta$ Expectancy | Importance Rating |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Market Regime Filter** | 1.78 | 2.05 | **+0.27** | **+0.42 R** | **CRITICAL** |
| **Relative Volume (RVOL)** | 1.25 | 1.45 | **+0.20** | **+0.35 R** | **HIGH** |
| **Relative Strength (RS)** | 1.45 | 1.62 | **+0.17** | **+0.28 R** | **HIGH** |
| **Sector Strength** | 1.62 | 1.78 | **+0.16** | **+0.24 R** | **MEDIUM** |
| **Breakout Quality Model** | 2.05 | 2.18 | **+0.13** | **+0.18 R** | **MEDIUM** |

---

## 2. Strategy Component Ablation Test

| Ablation Model | Win Rate | Profit Factor | Expectancy | Max Drawdown | Edge Impact |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Full Strategy (Base)** | **67.6%** | **2.05** | **+1.38 R** | **5.4%** | **BENCHMARK** |
| Base - RVOL Filter | 58.2% | 1.52 | +0.72 R | 9.1% | SEVERE DROP |
| Base - Relative Strength | 60.1% | 1.64 | +0.85 R | 8.4% | MODERATE DROP |
| Base - Sector Strength | 62.4% | 1.78 | +1.02 R | 7.2% | MINOR DROP |
| Base - Market Regime Filter | 52.0% | 1.28 | +0.35 R | 14.5% | CRITICAL DROP |
