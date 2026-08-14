# Chart Integrity, Symbol Validation & Decision UX Report — MarketPulse V6

**Document Version**: 6.0  
**Date**: 2026-08-14  
**Status**: VERIFIED & FULLY INTEGRATED

---

## 1. Root Cause Analysis of AAPL / BEL Mismatch

### Root Cause
When initializing the embedded TradingView widget in `dashboard.html`, the passed symbol string previously contained raw suffixes or uncleaned formatting (e.g. `COALINDIA.NS` or `NSE:BEL.NS`). When the TradingView JavaScript widget failed to resolve invalid symbols like `NSE:COALINDIA.NS`, TradingView's client-side fallback mechanism automatically defaulted to its default chart instrument (`NASDAQ:AAPL`).

### Resolution & Fix
1. **Strict Symbol Sanitization**: Stripped `.NS` suffixes, spaces, and non-alphanumeric characters in `chart_validator.py` and `dashboard.html` (`(v.symbol || '').replace('.NS', '').replace('NSE:', '').trim()`), guaranteeing clean format `NSE:<CLEAN_SYMBOL>` (e.g., `NSE:BEL`, `NSE:TRENT`, `NSE:POLYCAB`).
2. **Forbidden Instrument Enforcement**: Explicitly blocked US stock symbols (`AAPL`, `TSLA`, `MSFT`, `AMZN`, `GOOGL`, etc.) from being rendered or substituted in NSE Indian equity mode.
3. **Widget Destruction Lifecycle**: Added `destroyPreviousChartWidget()` prior to rendering any stock modal, calling `currentTvWidget.remove()` and clearing container HTML to prevent stale widget instances across sequential stock views (`BEL` → `TRENT` → `POLYCAB` → `BEL`).
4. **Mismatch Error Banner**: If a symbol mismatch occurs, the widget container displays a visible `⚠️ CHART SYMBOL ERROR` banner (`Expected: NSE:BEL | Loaded: US Equity`) instead of displaying a fallback chart.

---

## 2. Decision UX & Quality Score Separations

### V6 Decision Badges
- `🟢 BUY NOW`: High-conviction entry ready (Score $\ge 80$, RVOL $\ge 1.5\text{x}$, R:R $\ge 1.5$, Validated).
- `🟡 WAIT — CONFIRMATION REQUIRED`: Setup attractive (Score $\ge 75$), waiting for price trigger or volume expansion.
- `🔵 WATCH`: Setup candidate (Score $65\text{--}74$).
- `🟠 BLOCKED`: High quality setup blocked by risk/portfolio concentration gates.
- `🔴 AVOID`: Weak technical structure, low RVOL, bad R:R, or extended breakout.
- `⚪ NO TRADE`: Default neutral state.

### Stock Quality vs Entry Quality Separation
- **Stock Quality (0–100)**: Measures fundamental business quality, overall technical trend, relative strength, and sector momentum.
- **Entry Quality (0–100)**: Measures immediate trade entry readiness (RVOL expansion, price trigger proximity, fresh breakout vs extended status).

### Deterministic Panels
- **"WHAT WOULD CHANGE THIS TO BUY?"**: Lists exact deterministic triggers needed to upgrade a `WAIT` decision to `BUY NOW`.
- **4-Column Evidence Matrix**: `WHY BUY?`, `WHY NOT BUY?`, `WHAT CONFIRMS IT?`, `WHAT INVALIDATES IT?`.
- **TradingView Agreement Panel**: `MARKETPULSE DECISION: WAIT | TRADINGVIEW TECHNICAL STATUS: WAIT | SYSTEM AGREEMENT: HIGH`.
- **Score Interpretation Notice**: *"Master Score measures setup quality, not probability of profit."*
- **Top Opportunity Label**: Displays `TOP OPPORTUNITY TO WATCH` when `BUY NOW` count is 0.

---

## 3. Automated Test Verification

Executed full regression test suite (`python -m unittest discover -s tests -p "test_*.py"`):

```text
Ran 64 tests in 3.885s

OK
```

All 64 tests passing cleanly across symbol mapping, stale widget destruction, forbidden US stock prevention, decision badge consistency, and immutable analysis snapshots.
