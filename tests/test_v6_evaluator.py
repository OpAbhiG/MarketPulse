import unittest
from independent_evaluator import evaluate_signal_outcomes_independently, _fallback_independent_evaluation
from signal_replay import replay_historical_signal, _fallback_replay
from statistics_engine import calculate_bootstrap_confidence_intervals
from strategy_health import evaluate_strategy_health
from drift_detector import detect_market_data_drift
from database import save_signal_snapshot, get_connection
from decision_engine import evaluate_trading_decision

class TestV6IndependentEvaluator(unittest.TestCase):

    def test_save_signal_snapshot(self):
        snap = {
            "signal_id": "sig_test_123",
            "symbol": "TRENT",
            "mode": "SWING",
            "strategy": "Momentum Breakout",
            "decision_state": "BUY NOW",
            "entry_price": 2850.0,
            "trigger_price": 2850.0,
            "stop_loss": 2680.0,
            "target_1": 3050.0,
            "target_2": 3200.0,
            "master_score": 88,
            "rvol": 2.2,
            "rs_score": 91,
            "sector": "Retail",
            "market_regime": "NORMAL",
            "breadth_score": 74,
            "data_quality_score": 100
        }
        save_signal_snapshot(snap)
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM signal_snapshots WHERE signal_id = 'sig_test_123'")
        row = c.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["symbol"], "TRENT")

    def test_independent_evaluator(self):
        eval_res = evaluate_signal_outcomes_independently()
        self.assertIn("independent_win_rate", eval_res)
        self.assertIn("total_signals_evaluated", eval_res)
        self.assertGreater(eval_res["total_signals_evaluated"], 0)

    def test_evaluator_fallback(self):
        fb = _fallback_independent_evaluation()
        self.assertIn("independent_win_rate", fb)
        self.assertEqual(fb["total_signals_evaluated"], 28)

    def test_signal_replay(self):
        replay_res = replay_historical_signal("sig_test_123")
        self.assertIn("what_marketpulse_knew", replay_res)
        self.assertIn("what_actually_happened", replay_res)
        self.assertEqual(replay_res["symbol"], "TRENT")

    def test_signal_replay_fallback(self):
        fb = _fallback_replay("non_existent_sig")
        self.assertEqual(fb["symbol"], "TRENT")
        self.assertIn("what_marketpulse_knew", fb)

    def test_statistics_bootstrap_confidence_intervals(self):
        stats = calculate_bootstrap_confidence_intervals(sample_count=42, win_rate_base=66.7)
        self.assertEqual(stats["sample_rating"], "LIMITED EVIDENCE")
        self.assertIn("formatted", stats["win_rate_95_ci"])

    def test_statistics_sample_size_ratings(self):
        stats_early = calculate_bootstrap_confidence_intervals(sample_count=15)
        self.assertEqual(stats_early["sample_rating"], "EARLY EVIDENCE")

        stats_mod = calculate_bootstrap_confidence_intervals(sample_count=150)
        self.assertEqual(stats_mod["sample_rating"], "MODERATE EVIDENCE")

        stats_strong = calculate_bootstrap_confidence_intervals(sample_count=300)
        self.assertEqual(stats_strong["sample_rating"], "STRONG SAMPLE")

    def test_strategy_health_healthy(self):
        health = evaluate_strategy_health(rolling_expectancy=1.45, recent_win_rate=65.0)
        self.assertEqual(health["health_state"], "HEALTHY")
        self.assertTrue(health["is_active"])

    def test_strategy_health_watch_state(self):
        health = evaluate_strategy_health(rolling_expectancy=0.35, recent_win_rate=51.0)
        self.assertEqual(health["health_state"], "WATCH")
        self.assertTrue(health["is_active"])

    def test_strategy_health_paused_kill_switch(self):
        health = evaluate_strategy_health(rolling_expectancy=-0.25, recent_win_rate=42.0)
        self.assertEqual(health["health_state"], "PAUSED")
        self.assertFalse(health["is_active"])
        self.assertIn("DO NOT EXECUTE", health["action_required"])

    def test_drift_detector_normal(self):
        drift = detect_market_data_drift(curr_atr=2.2, curr_vix=14.0)
        self.assertFalse(drift["drift_detected"])
        self.assertEqual(drift["drift_status"], "STABLE MARKET ENVIRONMENT")

    def test_drift_detector_warning(self):
        drift = detect_market_data_drift(curr_atr=4.5, curr_vix=25.0)
        self.assertTrue(drift["drift_detected"])
        self.assertEqual(drift["drift_status"], "DATA/REGIME DRIFT WARNING")

    def test_snapshot_db_query(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM signal_snapshots")
        cnt = c.fetchone()[0]
        conn.close()
        self.assertGreaterEqual(cnt, 1)

    def test_evaluator_returns_formatting(self):
        eval_res = evaluate_signal_outcomes_independently(limit=5)
        self.assertIn("profit_factor", eval_res)
        self.assertIn("expectancy_r", eval_res)

    def test_signal_replay_structure(self):
        rep = replay_historical_signal("sig_test_123")
        knew = rep["what_marketpulse_knew"]
        self.assertIn("master_score", knew)
        self.assertIn("market_regime", knew)

    def test_statistics_ci_bounds(self):
        stats = calculate_bootstrap_confidence_intervals(sample_count=100, win_rate_base=60.0)
        ci = stats["win_rate_95_ci"]
        self.assertLess(ci["lower"], 60.0)
        self.assertGreater(ci["upper"], 60.0)

    def test_drift_recommendation(self):
        drift_norm = detect_market_data_drift(curr_atr=2.0, curr_vix=13.0)
        self.assertEqual(drift_norm["recommendation"], "ENVIRONMENT NORMAL")

    def test_snapshot_version_default(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT strategy_version FROM signal_snapshots LIMIT 1")
        ver = c.fetchone()[0]
        conn.close()
        self.assertEqual(ver, "v6.0")

if __name__ == "__main__":
    unittest.main()
