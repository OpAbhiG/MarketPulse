# Paper Trading & Live Shadow Mode Guide — MarketPulse V5

**Document Version**: 5.0  
**Scope**: Instructions and technical execution lifecycle for MarketPulse Paper Trading Engine and Live Shadow Mode.

---

## 1. Overview & Shadow Mode Execution

MarketPulse Paper Trading Engine executes on top of the **exact same production signal pipeline** (`market data` → `screening` → `scoring` → `decision` → `risk` → `paper trade`).

- **Shadow Mode**: During live market hours (9:15–15:30 IST), MarketPulse logs orders to the SQLite `paper_trades` table without connecting to broker APIs.
- **Paper Capital Default**: ₹50,000 capital, ₹1,000 risk per trade.
- **Order Lifecycle States**:
  - `OPEN`: Signal triggered, entry logged.
  - `TARGET1`: Target 1 hit (+8% return).
  - `TARGET2`: Target 2 hit (+15% return).
  - `STOP`: Stop loss hit (-6% return).
  - `INVALIDATED`: Trade structure invalidated prior to entry.
  - `EXPIRED`: Time stop reached (10 trading days).
  - `CLOSED`: Exit logged and Net P&L recorded.

---

## 2. Paper Trading Performance REST API Endpoint

Retrieve real-time paper trading performance:
```bash
GET /api/paper-trading
```

Output:
```json
{
  "ok": true,
  "paper_summary": {
    "capital": 50000.0,
    "risk_per_trade": 1000.0,
    "total_signals": 18,
    "open_trades": 3,
    "closed_trades": 15,
    "win_rate": 66.7,
    "profit_factor": 2.12,
    "expectancy_r": 1.42,
    "net_pnl": 4250.0,
    "current_drawdown_pct": 2.8,
    "shadow_mode_active": true
  }
}
```
