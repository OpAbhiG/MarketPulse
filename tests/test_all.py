import unittest
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scoring import calculate_data_quality, deterministic_evaluate
from risk_engine import calculate_risk_parameters
from signal_validator import validate_signal
from verifier import verify_llm_grounding
from backtest import run_strategy_backtest

class TestMarketPulse(unittest.TestCase):

    def setUp(self):
        self.evidence = {
            "symbol": "TRENT",
            "name": "Trent Limited",
            "cap_segment": "mid",
            "sector": "FMCG",
            "price": {"live": 3020.5, "day_open": 2980.0, "day_high": 3045.0, "day_low": 2975.0, "prev_close": 2950.0, "day_change_pct": 2.39, "volume": 1450000},
            "range_52w": {"high": 3100.0, "low": 1850.0, "pct_from_high": -2.56, "position_pct": 93.6},
            "technicals": {"rvol": 2.4, "price_vs_sma_pct": 4.2, "window_return_pct": 12.5, "swing_high": 3050.0, "swing_low": 2880.0, "day_range_position_pct": 86.5, "trend": "up"},
            "analyst": {"consensus": "buy", "num_analysts": 18, "target_mean": 3400.0, "upside_pct": 12.5},
            "news": {"total": 5, "positive": 4, "negative": 0, "neutral": 1, "recent": []},
            "data_gaps": []
        }

    def test_data_quality_score(self):
        dq = calculate_data_quality(self.evidence)
        self.assertEqual(dq, 100)

    def test_risk_engine(self):
        risk = calculate_risk_parameters(self.evidence, trading_capital=50000, max_risk_per_trade=1000)
        self.assertIsNotNone(risk["buy_zone"])
        self.assertGreater(risk["stop_loss"], 0)
        self.assertGreaterEqual(risk["rr_ratio"], 1.5)
        self.assertGreater(risk["calculator"]["quantity"], 0)

    def test_signal_validator(self):
        v = deterministic_evaluate(self.evidence)
        val = validate_signal(v, self.evidence)
        self.assertTrue(val["validated"])
        self.assertEqual(val["status"], "BUY")

    def test_signal_validator_blocking(self):
        bad_evidence = dict(self.evidence)
        bad_evidence["price"] = dict(self.evidence["price"])
        bad_evidence["price"]["volume"] = 100 # Fails liquidity
        v = deterministic_evaluate(bad_evidence)
        val = validate_signal(v, bad_evidence)
        self.assertFalse(val["validated"])
        self.assertEqual(val["status"], "BUY BLOCKED")

    def test_verifier_grounding(self):
        res_ok = verify_llm_grounding("Stock TRENT is trading at ₹3020.5 with RVOL 2.4", self.evidence)
        self.assertTrue(res_ok["verifier_ok"])

    def test_backtest_engine(self):
        bt = run_strategy_backtest(symbol_list=["TRENT.NS"])
        self.assertIsNotNone(bt["win_rate"])
        self.assertGreater(len(bt["trades"]), 0)

if __name__ == "__main__":
    unittest.main()
