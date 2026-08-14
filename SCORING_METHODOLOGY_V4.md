# Scoring Methodology (V4) — Expected Value (EV) & Empirical Calibration

**Document Version**: 4.0  
**Scope**: Mathematical formulas, empirical calibration matrix, and Expected Value ($EV$) ranking algorithm.

---

## 1. Expected Value ($EV$) Ranking Formula

Rather than sorting candidates purely by raw 0–100 score, MarketPulse V4 ranks candidates by Expected Value ($EV$) after deducting transaction costs and slippage:

$$EV = [P(\text{win}) \times \text{Average Win \%}] - [P(\text{loss}) \times \text{Average Loss \%}] - \text{Transaction Fees \%} - \text{Slippage \%}$$

Where:
- $P(\text{win})$ is derived from `calibration_engine.py` empirical calibration matrix.
- $\text{Transaction Fees} = 0.30\%$ (NSE STT + Brokerage + Exchange charges + GST + Stamp Duty).
- $\text{Slippage} = 0.10\%$ estimated bid/ask execution impact.

---

## 2. Empirical Calibration Matrix

| Score Bucket | Signal Count | Win Rate | $P(+1R)$ | $P(+2R)$ | $P(\text{Stop})$ | Expected R |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **90–100** | 18 | 72.2% | 77.8% | 50.0% | 16.7% | **+1.62 R** |
| **80–89** | 34 | 64.7% | 67.6% | 41.2% | 23.5% | **+1.25 R** |
| **75–79** | 26 | 57.7% | 61.5% | 34.6% | 30.8% | **+0.88 R** |
| **70–74** | 15 | 46.7% | 53.3% | 20.0% | 40.0% | **+0.35 R** |
| **< 70** | 12 | 33.3% | 41.7% | 8.3% | 58.3% | **-0.42 R** |
