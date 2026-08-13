# MarketPulse — Local Indian Stock Agent Dashboard

A local Flask dashboard that runs a named multi-agent stock-analysis panel, stores an audit trail in SQLite, and can send qualified BUY signals to Telegram. **No orders are placed.**

## 1. Install

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill only the settings you want.

## 2. LLM options

Preferred auto-detection order:

1. `claude_code` — if `claude` is on PATH. The app invokes `claude -p ... --output-format json --model haiku|sonnet` with stdin disconnected. This uses the logged-in Claude subscription rather than an API key.
2. `anthropic` — set `ANTHROPIC_API_KEY`.
3. `openai` — set `OPENAI_API_KEY`.
4. deterministic fallback — always available, with no key and no network.

Force one with `LLM_PROVIDER=claude_code`, `anthropic`, or `openai`.

## 3. Telegram

Create a bot with `@BotFather`, obtain the bot token, obtain your chat ID (for example through `@userinfobot`), then put these in `.env`:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

The token is never rendered in the UI or application logs. The app sends one message per fired BUY plus one daily summary when Telegram is configured.

## 4. Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** and click **Start agents**. Use **Demo** first. Demo is fully offline and uses the bundled evidence JSON files. Use **Live** during NSE market hours (Mon–Fri, 09:15–15:30 IST) for yfinance data.

## 5. Data model

Each stock is normalized into one evidence bundle with price, 52-week range, technicals, analyst information, news, and `data_gaps`. Missing values are `null` and named in `data_gaps`.

This portable yfinance feed intentionally does **not** expose raw valuation ratios such as P/E or ROE in the normalized bundle; those fields are therefore not silently invented.

## 6. Safety / grounding

- BUY fires only at `confidence >= CONFIDENCE_THRESHOLD` (default 7).
- Deterministic BUY requires `net >= 25` and leadership from 52-week position or RVOL.
- The LLM is explicitly instructed to use only the evidence bundle.
- A small verifier checks numeric claims in LLM reasoning against numbers present in the evidence. If it fails, the stock falls back to deterministic scoring for that evaluation.
- No broker API is called and no order is placed.
- Telegram errors do not crash the run.
- Missing live fields do not crash the run.

## 7. Editing the universe

Edit `universe.json`. Keep NSE symbols as `.NS` tickers. The dashboard screens each large/mid/small bucket by day change and keeps `SHORTLIST_PER_BUCKET` (default 4).

## 8. Files

- `app.py` — Flask server, background state machine, SQLite audit, Telegram
- `scoring.py` — deterministic scoring and judge
- `llm.py` — Claude Code / Anthropic / OpenAI adapter and grounding verifier
- `data_sources.py` — demo loader, yfinance adapter, evidence normalization
- `dashboard.html` — self-contained UI
- `universe.json` — editable universe
- `demo_data/` — real-stock-shaped offline evidence bundles
- `audit.sqlite3` — created automatically after first start
