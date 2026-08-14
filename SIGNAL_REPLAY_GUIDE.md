# Signal Replay & Hindsight Protection Guide — MarketPulse V6

**Document Version**: 6.0  
**Scope**: Instructions for operating the Signal Replay Engine.

---

## 1. Signal Replay Principles

The Signal Replay Engine (`signal_replay.py`) prevents hindsight bias by separating historical signal evidence from subsequent market returns.

### Point-in-Time Signal Data
- Symbol & Timestamp
- Entry Price, Trigger, Stop Loss, Target 1, Target 2
- Master Score, RVOL, RS, Sector Strength, Market Regime, Breadth Score

### Subsequent Market Returns (Observer Layer)
- +1D, +5D, +20D returns
- Maximum Favorable Excursion (MFE)
- Maximum Adverse Excursion (MAE)
- Exit Reason & Net P&L

---

## 2. Signal Replay REST API Endpoint

```bash
GET /api/signal-replay/<signal_id>
```
