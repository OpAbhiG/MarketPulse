# Test Verification Report (V2) — MarketPulse Platform

**Date**: 2026-08-14  
**Status**: ALL 11 TESTS PASSED

---

## Test Execution Summary

```text
python -m unittest discover -s tests -p "test_*.py"
...........
----------------------------------------------------------------------
Ran 11 tests in 2.147s

OK
```

---

## Detailed Test Case Results

1. `test_intraday_engine`: Verified Intraday Score /100 calculation and setup classification (`CONFIRMED INTRADAY`, `BREAKOUT WATCH`).
2. `test_swing_engine`: Verified Swing Score /100 calculation and setup classification (`CONFIRMED SWING`, `SWING MOMENTUM`).
3. `test_false_breakout_extension_guard`: Verified extension distance calculations. Confirmed that price $>10\%$ past resistance flags `SEVERELY EXTENDED` and returns `is_too_extended = True`.
4. `test_opportunity_engine`: Verified Master Opportunity Ranking and No-Forced-Signal Policy.
5. `test_portfolio_concentration_guard`: Verified that 3 active positions in the same sector trigger `BUY BLOCKED` with reason `"Portfolio concentration risk"`.
6. `test_scoring_master_score`: Verified 10-component score breakdown sums up to 100 points.
7. `test_backtest_walk_forward`: Verified Walk-Forward splits and Monte Carlo 95th percentile drawdown calculations.
8. `test_telegram_deduplication`: Verified message hash deduplication.
9. `test_verifier_grounding`: Verified numeric grounding verification.
10. `test_database_persistence`: Verified SQLite database schema and CRUD operations.
11. `test_market_regime_evaluation`: Verified NIFTY 50 and VIX regime classification.
