# Codebase & Decision Logic Audit Report (V3) — MarketPulse Platform

**Date**: 2026-08-14  
**Scope**: Deep audit of scoring, decision logic, UI state contradictions, ranking, backtesting, and Telegram alerting.

---

## 1. Executive Summary

While MarketPulse V2 introduced Intraday and Swing engines, a critical audit revealed that naive top-pick selection (`max(verdicts, key=score)`) resulted in UI contradictions where a stock with score 68/100 or a `BLOCKED` status was displayed as `TOP PICK` even when `BUY SIGNALS = 0`. MarketPulse V3 introduces a strict 6-state decision engine (`decision_engine.py`), an Action Center header, distinct AI Opportunity Categories, explicit "Stocks to Avoid" rejection rationale, and realistic transaction costs in Strategy Lab 2.0.

---

## 2. Key Audit Findings & Contradiction Fixes

### A. UI Decision State Contradictions (Critical Fix)
- ❌ **Problem**: `app.py` previously picked `top_pick` using `max(verdicts, key=lambda x: x.get("marketpulse_score", 0))` regardless of whether the signal was `validated`, `BLOCKED`, or had a low score. This produced misleading UI states (e.g. `TOP PICK = VOLTAS` with `Score 68/100` and `BUY SIGNALS = 0`).
- ✅ **Fix**: Implement `decision_engine.py` to enforce strict decision state machine:
  1. `🟢 BUY NOW`: Master Score $\ge 80$, Judge = BUY, Confidence $\ge 7$, R:R $\ge 1.5$, Data Quality $\ge 75$, Liquidity passes, Regime permits, Not extended, Entry confirmed.
  2. `🟡 BUY ON CONFIRMATION`: Setup score $\ge 75$, setup not fully confirmed yet, clear trigger price exists.
  3. `🔵 WATCH`: Setup score $65\text{--}74$, interesting setup, insufficient confirmation.
  4. `🔴 AVOID`: Master score $<65$, weak technicals, low RVOL, bad R:R, bad regime, extended breakout ($>10\%$), false breakout risk.
  5. `🟠 BLOCKED`: Setup score $\ge 75$ but risk/validation gate (e.g. portfolio concentration) prevents trading.
  6. `⚪ NO TRADE`: Default state when no candidate meets minimum criteria.
- **Rule**: If `BUY NOW` count = 0, `top_pick` MUST be `None`, displaying `"NO HIGH-CONVICTION BUY TODAY"`.

### B. Action Center Header & Mode Switch
- ❌ **Problem**: Header lacked real-time decision stats, data freshness age, and explicit Intraday vs Swing mode toggles.
- ✅ **Fix**: Add **MarketPulse Action Center** header with Market Regime status, NIFTY 50, India VIX, Data status (`LIVE` / `DELAYED` / `STALE`), Last scan timestamp, Today's Decision Breakdown (`BUY NOW`, `BUY ON CONFIRMATION`, `WATCH`, `AVOID`, `BLOCKED`), and `[ INTRADAY ]` vs `[ SWING ]` mode toggles.

### C. 🔴 STOCKS TO AVOID Section
- ❌ **Problem**: Rejected stocks were shown generically as `AVOID` without highlighting the exact failure reasons.
- ✅ **Fix**: Create a dedicated **🔴 STOCKS TO AVOID** panel displaying explicit bulleted rejection reasons (❌ Low RVOL, ❌ Weak RS, ❌ Below EMA20, ❌ Poor R:R, ❌ Market regime, ❌ Extended breakout, ❌ False breakout risk).

### D. "Why Buy?" vs "Why Not Buy?" Breakdown
- ❌ **Problem**: Cards lacked explicit trigger and invalidation prices for unconfirmed setups.
- ✅ **Fix**: Every stock card now displays `WHY BUY?`, `WHY NOT BUY?`, `TRIGGER` (BUY ONLY ABOVE ₹XXXX), and `INVALIDATION` (Below ₹XXXX).

### E. Realistic Backtest Cost Model
- ❌ **Problem**: Historical backtests assumed zero transaction costs and zero slippage.
- ✅ **Fix**: Include realistic NSE transaction costs (Brokerage, STT, Exchange charges, GST, SEBI charges, Stamp duty, Slippage) in `backtest.py`.

---

## 3. Implementation Plan Overview

1. Create `decision_engine.py`: 6-state decision machine & decision counts.
2. Update `scoring.py`: Integrate decision engine payload.
3. Update `app.py`: Update `/opportunities` and `/status` endpoints.
4. Update `dashboard.html`: Action Center, Mode switch, Decision cards, Stocks to Avoid section.
5. Update `backtest.py`: Transaction cost model.
6. Create documentation: `SCORING_METHODOLOGY.md`, `TRADING_DECISION_GUIDE.md`, `IMPLEMENTATION_REPORT_V3.md`, `TEST_REPORT_V3.md`, `CHANGELOG_V5.md`, `README.md`.
7. Execute unit tests and push to GitHub.
