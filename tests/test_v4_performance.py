import unittest
from performance_engine import get_performance_summary
from calibration_engine import get_score_calibration_matrix, get_calibrated_win_probability
from breakout_quality_engine import evaluate_breakout_quality_grade
from breadth_engine import calculate_market_breadth
from event_risk import evaluate_event_risk
from intraday_engine import calculate_time_of_day_rvol

class TestV4Performance(unittest.TestCase):

    def test_performance_summary(self):
        perf = get_performance_summary()
        self.assertIn("win_rate", perf)
        self.assertGreater(perf["win_rate"], 50.0)

    def test_score_calibration(self):
        calib = get_score_calibration_matrix()
        self.assertTrue(calib["is_calibrated"])
        p90 = get_calibrated_win_probability(92)
        p70 = get_calibrated_win_probability(72)
        self.assertGreater(p90, p70)

    def test_breakout_quality_grade(self):
        evidence = {
            "price": {"live": 2850.0},
            "technicals": {"rvol": 2.2, "swing_high": 2800.0},
            "range_52w": {"position_pct": 92.0}
        }
        grade_res = evaluate_breakout_quality_grade(evidence)
        self.assertIn(grade_res["grade"], ["A+ BREAKOUT", "A BREAKOUT"])

    def test_market_breadth(self):
        breadth = calculate_market_breadth()
        self.assertGreater(breadth["breadth_score"], 50)
        self.assertEqual(breadth["breadth_status"], "STRONG BREADTH")

    def test_event_risk(self):
        ev_risk = evaluate_event_risk("TRENT")
        self.assertEqual(ev_risk["event_risk_level"], "LOW")

    def test_time_of_day_rvol(self):
        tod = calculate_time_of_day_rvol(2.0)
        self.assertGreaterEqual(tod, 0.5)

if __name__ == "__main__":
    unittest.main()
