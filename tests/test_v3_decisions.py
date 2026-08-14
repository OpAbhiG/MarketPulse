import unittest
from decision_engine import evaluate_trading_decision, summarize_decisions
from opportunity_engine import rank_market_opportunities

class TestV3Decisions(unittest.TestCase):

    def setUp(self):
        self.evidence = {
            "symbol": "TRENT",
            "technicals": {"rvol": 2.2, "trend": "up", "swing_high": 2800.0, "swing_low": 2600.0}
        }
        self.verdict_buy_now = {
            "symbol": "TRENT",
            "marketpulse_score": 88,
            "verdict": "BUY",
            "confidence": 8,
            "validated": True,
            "validation_status": "VALIDATED",
            "is_too_extended": False,
            "extension_status": "FRESH BREAKOUT",
            "rr_ratio": 2.2,
            "data_quality_score": 95,
            "boom_type": "CONFIRMED BREAKOUT",
            "price": 2850.0,
            "technicals": {"rvol": 2.2, "trend": "up", "swing_high": 2800.0, "swing_low": 2600.0}
        }
        dec_buy = evaluate_trading_decision(self.evidence, self.verdict_buy_now)
        self.verdict_buy_now.update(dec_buy)

        self.verdict_avoid = {
            "symbol": "POLYCAB",
            "marketpulse_score": 60,
            "verdict": "AVOID",
            "confidence": 4,
            "validated": False,
            "validation_status": "REJECTED",
            "is_too_extended": True,
            "extension_status": "SEVERELY EXTENDED",
            "rr_ratio": 1.1,
            "data_quality_score": 80,
            "boom_type": "NORMAL",
            "price": 8900.0,
            "technicals": {"rvol": 0.7, "trend": "down", "swing_high": 8500.0, "swing_low": 8200.0}
        }
        dec_avoid = evaluate_trading_decision(self.evidence, self.verdict_avoid)
        self.verdict_avoid.update(dec_avoid)

    def test_buy_now_decision(self):
        res = evaluate_trading_decision(self.evidence, self.verdict_buy_now)
        self.assertEqual(res["decision_state"], "BUY NOW")
        self.assertEqual(res["decision_badge"], "🟢 BUY NOW")

    def test_avoid_decision(self):
        res = evaluate_trading_decision(self.evidence, self.verdict_avoid)
        self.assertEqual(res["decision_state"], "AVOID")
        self.assertEqual(res["decision_badge"], "🔴 AVOID")
        self.assertTrue(len(res["avoid_reasons"]) > 0)

    def test_no_forced_top_pick(self):
        opps = rank_market_opportunities([self.verdict_avoid])
        self.assertIsNone(opps["top_intraday"])
        self.assertIsNone(opps["top_swing"])
        self.assertEqual(opps["opportunities_summary"], "NO HIGH-CONVICTION BUY TODAY")

    def test_summarize_decisions(self):
        counts = summarize_decisions([self.verdict_buy_now, self.verdict_avoid])
        self.assertEqual(counts["buy_now"], 1)
        self.assertEqual(counts["avoid"], 1)

if __name__ == "__main__":
    unittest.main()
