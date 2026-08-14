# Edge Validation Methodology — MarketPulse V6

**Document Version**: 6.0  
**Scope**: Independent observer layer, statistical confidence intervals, and strategy kill-switch methodology.

---

## 1. Independent Evaluator Architecture

MarketPulse V6 decouples signal generation from signal performance evaluation:

```text
MARKET DATA → SIGNAL ENGINE → IMMUTABLE SIGNAL SNAPSHOT → INDEPENDENT EVALUATOR → FUTURE MARKET OUTCOME
```

- **Observer-Only Constraint**: The independent evaluator (`independent_evaluator.py`) does NOT modify scores, decisions, or risk rules.
- **Immutable Snapshots**: Every signal saves a point-in-time record to SQLite `signal_snapshots`.
- **Signal Replay**: Enables historical verification of `WHAT MARKETPULSE KNEW AT SIGNAL TIME` vs `WHAT ACTUALLY HAPPENED`.

---

## 2. Statistical Sample Size Classification

| Sample Size Range | Classification Rating | Confidence Assessment |
| :---: | :--- | :--- |
| **$< 30$** | **EARLY EVIDENCE** | Unrated / Insufficient data |
| **$30\text{--}99$** | **LIMITED EVIDENCE** | Research Status / 95% CI wide |
| **$100\text{--}249$** | **MODERATE EVIDENCE** | Statistically significant |
| **$250+$** | **STRONG SAMPLE** | High empirical confidence |
