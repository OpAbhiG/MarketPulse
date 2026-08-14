import unittest
from intraday_engine import calculate_intraday_score
from swing_engine import calculate_swing_score
from false_breakout_engine import evaluate_breakout_extension_and_validity
from opportunity_engine import rank_market_opportunities
from risk_engine import calculate_risk_parameters
import scoring

class TestV2Engines(unittest.TestCase):

    def setUp(self):
        self.evidence = {
            "symbol": "TRENT",
            "name": "Trent Limited",
            "cap_segment": "large",
            "sector": "FMCG",
            "price": {"live": 2850.0, "day_change_pct": 3.2, "day_open": 2800.0, "day_high": 2880.0, "day_low": 2790.0},
            "technicals": {
                "rvol": 2.2,
                "trend": "up",
                "price_vs_sma_pct": 4.5,
                "day_range_position_pct": 85.0,
                "swing_high": 2750.0,
                "swing_low": 2600.0,
                "atr14": 45.0,
                "vwap": 2830.0,
                "ema9": 2840.0,
                "ema20": 2810.0,
                "ema50": 2750.0
            },
            "range_52w": {"position_pct": 92.0},
            "analyst": {"upside_pct": 18.5, "target_mean": 3200.0},
            "news": {"positive": 3, "negative": 0, "total": 3}
        }
        self.market_regime = {"risk_mode": "RISK_ON", "trend": "BULLISH", "score": 82}
        self.sector_data = {"name": "FMCG", "return_20d": 4.2, "is_outperforming": True}

    def test_intraday_engine(self):
        res = calculate_intraday_score(self.evidence, self.market_regime, self.sector_data)
        self.assertIn("score", res)
        self.assertGreaterEqual(res["score"], 70)
        self.assertIn(res["classification"], ["CONFIRMED INTRADAY", "BREAKOUT WATCH", "MOMENTUM SETUP"])

    def test_swing_engine(self):
        res = calculate_swing_score(self.evidence, self.market_regime, self.sector_data)
        self.assertIn("score", res)
        self.assertGreaterEqual(res["score"], 70)
        self.assertIn(res["classification"], ["CONFIRMED SWING", "SWING MOMENTUM"])

    def test_false_breakout_extension_guard(self):
        ext_normal = evaluate_breakout_extension_and_validity(self.evidence)
        self.assertFalse(ext_normal["is_too_extended"])

        # Test overextended price
        extended_evidence = dict(self.evidence)
        extended_evidence["price"] = {"live": 3200.0, "day_change_pct": 8.0}
        ext_extended = evaluate_breakout_extension_and_validity(extended_evidence)
        self.assertTrue(ext_extended["is_too_extended"])
        self.assertEqual(ext_extended["extension_status"], "SEVERELY EXTENDED")

    def test_opportunity_engine(self):
        eval1 = scoring.deterministic_evaluate(self.evidence, self.market_regime, self.sector_data)
        opps = rank_market_opportunities([eval1])
        self.assertTrue(opps["has_opportunity"])
        self.assertIsNotNone(opps["top_intraday"])
        self.assertIsNotNone(opps["top_swing"])

    def test_portfolio_concentration_guard(self):
        # 2 existing FMCG positions
        active_pos = [{"sector": "FMCG"}, {"sector": "FMCG"}]
        risk_res = calculate_risk_parameters(self.evidence, active_positions=active_pos)
        self.assertTrue(risk_res["portfolio_concentration"]["is_blocked"])
        self.assertIn("Portfolio concentration risk", risk_res["portfolio_concentration"]["reason"])

if __name__ == "__main__":
    unittest.main()
