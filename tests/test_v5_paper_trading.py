import unittest
from paper_trading import place_paper_trade, get_paper_trading_summary
from feature_attribution import calculate_feature_attributions
from ablation import run_strategy_ablation
from backtest import evaluate_parameter_sensitivity, run_strategy_backtest

class TestV5PaperTrading(unittest.TestCase):

    def test_place_paper_trade(self):
        verdict_buy = {
            "symbol": "TRENT",
            "decision_state": "BUY NOW",
            "price": 2850.0,
            "risk_params": {"stop_loss": 2680.0, "target_1": 3050.0, "target_2": 3200.0},
            "boom_type": "CONFIRMED BREAKOUT"
        }
        sig_id = place_paper_trade(verdict_buy)
        self.assertIsNotNone(sig_id)
        self.assertTrue(sig_id.startswith("sig_"))

    def test_paper_trading_summary(self):
        summary = get_paper_trading_summary()
        self.assertIn("capital", summary)
        self.assertIn("win_rate", summary)
        self.assertTrue(summary["shadow_mode_active"])

    def test_feature_attributions(self):
        attr = calculate_feature_attributions()
        self.assertIn("features", attr)
        self.assertGreater(len(attr["features"]), 3)
        self.assertEqual(attr["final_pf"], 2.18)

    def test_strategy_ablation(self):
        abl = run_strategy_ablation()
        self.assertIn("benchmark", abl)
        self.assertEqual(abl["most_critical_feature"], "Market Regime Filter")

    def test_parameter_sensitivity(self):
        sens = evaluate_parameter_sensitivity()
        self.assertEqual(sens["stability"], "ROBUST")

    def test_edge_status_output(self):
        res = run_strategy_backtest()
        self.assertIn("edge_status", res)
        self.assertIn("survivorship_bias_warning", res)

if __name__ == "__main__":
    unittest.main()
