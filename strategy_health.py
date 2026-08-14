def evaluate_strategy_health(strategy_name="Momentum Breakout", rolling_expectancy=1.38, recent_win_rate=65.0):
    """
    Strategy Health Kill-Switch:
    States: HEALTHY, WATCH, PAUSED, RETIRED.
    If PAUSED, blocks new BUY signals from that strategy.
    """
    if rolling_expectancy < 0.0 or recent_win_rate < 45.0:
        health_state = "PAUSED"
        reason = "Persistent negative expectancy / win rate drop in recent observations"
        is_active = False
    elif rolling_expectancy < 0.5 or recent_win_rate < 52.0:
        health_state = "WATCH"
        reason = "Recent win rate drop below baseline — strategy under surveillance"
        is_active = True
    else:
        health_state = "HEALTHY"
        reason = "Strategy expectancy and win rate satisfy robust edge thresholds"
        is_active = True

    return {
        "strategy_name": strategy_name,
        "health_state": health_state,
        "is_active": is_active,
        "rolling_expectancy": rolling_expectancy,
        "recent_win_rate": recent_win_rate,
        "reason": reason,
        "action_required": "DO NOT EXECUTE NEW BUY ALERTS" if not is_active else "CONTINUE MONITORED EXECUTION"
    }
