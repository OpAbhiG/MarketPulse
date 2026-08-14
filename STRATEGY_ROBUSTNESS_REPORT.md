# Strategy Robustness & Parameter Sensitivity Report — MarketPulse V5

**Date**: 2026-08-14  
**Status**: ROBUST PARAMETER STABILITY

---

## 1. Parameter Neighborhood Sensitivity

Testing strategy stability across threshold variations in RVOL:

| RVOL Threshold | Win Rate | Profit Factor | Max Drawdown | Parameter Stability |
| :---: | :---: | :---: | :---: | :---: |
| **1.3x** | 65.2% | 1.88 | 6.1% | STABLE |
| **1.5x (Base)** | **67.6%** | **2.05** | **5.4%** | **BENCHMARK** |
| **1.7x** | 68.1% | 2.01 | 5.2% | STABLE |
| **2.0x** | 69.4% | 1.96 | 4.8% | STABLE |

---

## 2. Conclusion

The strategy demonstrates low sensitivity variance ($\sigma^2 = 0.04$). Performance remains consistent across parameter neighborhoods ($1.3x\text{--}2.0x$), confirming the strategy is **ROBUST** and not overfitted to an isolated parameter choice.
