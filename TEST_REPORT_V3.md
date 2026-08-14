# Test Verification Report (V3) — MarketPulse Platform

**Date**: 2026-08-14  
**Status**: ALL 15 TESTS PASSED

---

## Test Execution Summary

```text
python -m unittest discover -s tests -p "test_*.py"
...............
----------------------------------------------------------------------
Ran 15 tests in 0.805s

OK
```

---

## Detailed Test Case Results

1. `test_buy_now_decision`: Verified 🟢 BUY NOW state machine assignment.
2. `test_avoid_decision`: Verified 🔴 AVOID state machine assignment and explicit avoidance rationale.
3. `test_no_forced_top_pick`: Verified that with only AVOID candidates, top_pick is `None` and summary is `"NO HIGH-CONVICTION BUY TODAY"`.
4. `test_summarize_decisions`: Verified decision count summary aggregation.
5. `test_intraday_engine`: Verified Intraday Score /100 calculation and 5m setup classification.
6. `test_swing_engine`: Verified Swing Score /100 calculation and Daily/Weekly setup classification.
7. `test_false_breakout_extension_guard`: Verified extension distance calculations and late breakout guard (>10% past resistance).
8. `test_opportunity_engine`: Verified Master Opportunity ranking.
9. `test_portfolio_concentration_guard`: Verified portfolio concentration limit blocks.
10. `test_scoring_master_score`: Verified 10-component score breakdown.
11. `test_backtest_walk_forward`: Verified Walk-Forward splits and Monte Carlo 95th percentile drawdown calculations.
12. `test_telegram_deduplication`: Verified message hash deduplication.
13. `test_verifier_grounding`: Verified numeric grounding verification.
14. `test_database_persistence`: Verified SQLite database schema and CRUD operations.
15. `test_market_regime_evaluation`: Verified NIFTY 50 and VIX regime classification.
