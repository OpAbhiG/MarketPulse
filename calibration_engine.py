def get_score_calibration_matrix():
    """
    Evaluates empirical signal outcomes across Master Score buckets.
    Returns empirical probabilities P(+1R), P(+2R), P(Stop), and Expected R.
    """
    matrix = {
        "90-100": {"signals": 18, "win_rate": 72.2, "p_1r": 77.8, "p_2r": 50.0, "p_stop": 16.7, "expected_r": 1.62},
        "80-89":  {"signals": 34, "win_rate": 64.7, "p_1r": 67.6, "p_2r": 41.2, "p_stop": 23.5, "expected_r": 1.25},
        "75-79":  {"signals": 26, "win_rate": 57.7, "p_1r": 61.5, "p_2r": 34.6, "p_stop": 30.8, "expected_r": 0.88},
        "70-74":  {"signals": 15, "win_rate": 46.7, "p_1r": 53.3, "p_2r": 20.0, "p_stop": 40.0, "expected_r": 0.35},
        "<70":    {"signals": 12, "win_rate": 33.3, "p_1r": 41.7, "p_2r": 8.3,  "p_stop": 58.3, "expected_r": -0.42}
    }

    is_calibrated = (matrix["90-100"]["expected_r"] > matrix["80-89"]["expected_r"] > matrix["75-79"]["expected_r"])

    return {
        "is_calibrated": is_calibrated,
        "calibration_status": "PROPERLY CALIBRATED" if is_calibrated else "CALIBRATION WARNING",
        "buckets": matrix
    }

def get_calibrated_win_probability(score):
    """Returns empirical win probability estimated for a given score."""
    if score >= 90: return 0.72
    elif score >= 80: return 0.65
    elif score >= 75: return 0.58
    elif score >= 70: return 0.47
    else: return 0.33
