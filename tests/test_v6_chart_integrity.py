import unittest
from chart_validator import validate_nse_symbol, validate_chart_data_match, create_analysis_snapshot
from decision_engine import evaluate_trading_decision, summarize_decisions

class TestV6ChartIntegrityAndDecisionUX(unittest.TestCase):

    def test_1_bel_symbol_mapping(self):
        valid, clean, tv_sym, err = validate_nse_symbol("BEL")
        self.assertTrue(valid)
        self.assertEqual(clean, "BEL")
        self.assertEqual(tv_sym, "NSE:BEL")

    def test_2_trent_symbol_mapping(self):
        valid, clean, tv_sym, err = validate_nse_symbol("TRENT.NS")
        self.assertTrue(valid)
        self.assertEqual(clean, "TRENT")
        self.assertEqual(tv_sym, "NSE:TRENT")

    def test_3_polycab_symbol_mapping(self):
        valid, clean, tv_sym, err = validate_nse_symbol("NSE:POLYCAB")
        self.assertTrue(valid)
        self.assertEqual(clean, "POLYCAB")
        self.assertEqual(tv_sym, "NSE:POLYCAB")

    def test_4_stale_widget_prevention_lifecycle(self):
        # Simulate sequence: BEL -> TRENT -> POLYCAB -> BEL
        syms = ["BEL", "TRENT", "POLYCAB", "BEL"]
        results = []
        for s in syms:
            v, c, tv, _ = validate_nse_symbol(s)
            results.append((c, tv))
        self.assertEqual(results[0], ("BEL", "NSE:BEL"))
        self.assertEqual(results[1], ("TRENT", "NSE:TRENT"))
        self.assertEqual(results[2], ("POLYCAB", "NSE:POLYCAB"))
        self.assertEqual(results[3], ("BEL", "NSE:BEL"))

    def test_5_aapl_forbidden_in_nse_mode(self):
        valid, clean, tv_sym, err = validate_nse_symbol("AAPL")
        self.assertFalse(valid)
        self.assertIn("FORBIDDEN INSTRUMENT", err)

    def test_6_wrong_chart_symbol_produces_error(self):
        match_res = validate_chart_data_match("BEL", "NASDAQ:AAPL", 410.0)
        self.assertFalse(match_res["valid"])
        self.assertEqual(match_res["status"], "CHART SYMBOL ERROR")
        self.assertIn("Symbol mismatch", match_res["error"])

    def test_7_buy_on_confirmation_never_displays_buy_now(self):
        evidence = {}
        payload = {
            "symbol": "BEL",
            "marketpulse_score": 76,
            "verdict": "WATCH",
            "confidence": 7,
            "validated": True,
            "price": 410.0,
            "technicals": {"rvol": 0.43, "trend": "up", "swing_high": 412.5},
            "rr_ratio": 1.6,
            "boom_type": "BOOM MOMENTUM"
        }
        res = evaluate_trading_decision(evidence, payload)
        self.assertNotEqual(res["decision_state"], "BUY NOW")
        self.assertIn("WAIT", res["decision_state"])

    def test_8_score_76_does_not_become_buy_now(self):
        evidence = {}
        payload = {
            "symbol": "TRENT",
            "marketpulse_score": 76,
            "verdict": "BUY",
            "confidence": 6,
            "validated": True,
            "price": 2850.0,
            "technicals": {"rvol": 1.2, "trend": "up"},
            "rr_ratio": 1.4
        }
        res = evaluate_trading_decision(evidence, payload)
        self.assertNotEqual(res["decision_state"], "BUY NOW")

    def test_9_buy_now_count_0_never_produces_top_pick(self):
        verdicts = [
            {"symbol": "BEL", "decision_state": "WAIT — CONFIRMATION REQUIRED"},
            {"symbol": "RELIANCE", "decision_state": "AVOID"}
        ]
        summary = summarize_decisions(verdicts)
        self.assertEqual(summary["buy_now"], 0)
        self.assertEqual(summary["top_label"], "TOP OPPORTUNITY TO WATCH")
        self.assertNotEqual(summary.get("top_label"), "TOP PICK")

    def test_10_wait_displays_trigger_and_missing_confirmation(self):
        evidence = {}
        payload = {
            "symbol": "BEL",
            "marketpulse_score": 76,
            "price": 410.15,
            "technicals": {"rvol": 0.43, "swing_high": 412.50}
        }
        res = evaluate_trading_decision(evidence, payload)
        self.assertIn("₹412.50", res["trigger_price"])
        self.assertGreater(len(res["what_would_change_to_buy"]), 0)

    def test_11_avoid_displays_reasons(self):
        evidence = {}
        payload = {
            "symbol": "RELIANCE",
            "marketpulse_score": 55,
            "price": 2450.0,
            "technicals": {"rvol": 0.5, "trend": "sideways"}
        }
        res = evaluate_trading_decision(evidence, payload)
        self.assertEqual(res["decision_state"], "AVOID")
        self.assertGreater(len(res["avoid_reasons"]), 0)

    def test_12_blocked_distinguishes_risk_blocking(self):
        evidence = {}
        payload = {
            "symbol": "POLYCAB",
            "marketpulse_score": 85,
            "validated": False,
            "validation_status": "BUY BLOCKED",
            "validation_reason": "Portfolio limit reached (5/5 active positions)",
            "price": 6200.0
        }
        res = evaluate_trading_decision(evidence, payload)
        self.assertEqual(res["decision_state"], "BLOCKED")
        self.assertIn("RISK GATE BLOCKED", res["action"])

    def test_13_analysis_snapshot_integrity(self):
        payload = {
            "symbol": "TRENT",
            "price": 2850.0,
            "marketpulse_score": 82,
            "stock_quality_score": 82,
            "entry_quality_score": 75,
            "decision_state": "BUY NOW",
            "decision_badge": "🟢 BUY NOW",
            "technicals": {"rvol": 2.1, "relative_strength": 88}
        }
        snap = create_analysis_snapshot(payload)
        self.assertEqual(snap["symbol"], "TRENT")
        self.assertEqual(snap["stock_quality_score"], 82)
        self.assertEqual(snap["entry_quality_score"], 75)
        self.assertIn("snap_", snap["snapshot_id"])

if __name__ == "__main__":
    unittest.main()
