import json, statistics, math
from pathlib import Path
from datetime import datetime


def load_universe(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_demo_evidence(folder):
    out=[]
    for p in sorted(Path(folder).glob("*.json")):
        try: out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception: pass
    return out


def extract_nse_symbols(text):
    import re
    if not text or not isinstance(text, str):
        return []
    
    # 1. Look for explicit URL parameter symbol=SYMBOL
    url_matches = re.findall(r'symbol=([A-Za-z0-9&\-_]+)', text)
    
    # 2. Split text by common separators (newlines, commas, tabs, spaces, semicolons, quotes, brackets)
    raw_tokens = re.split(r'[\n\r\t,;:"\'()\[\]\s]+', text)
    
    candidates = list(url_matches) + raw_tokens
    seen = set()
    cleaned = []
    
    # Blacklist non-symbol noise words commonly found in NSE page copy/paste
    blacklist = {
        "NSE", "BSE", "SYMBOL", "PRICE", "CHANGE", "VOLUME", "HIGH", "LOW", "OPEN", "CLOSE",
        "PREV", "TURNOVER", "MARKET", "CAP", "EQUITY", "DERIVATIVES", "INDEX", "NIFTY",
        "BANKNIFTY", "COMPANY", "LTP", "PCHG", "CHG", "BUY", "SELL", "QTY", "VAL", "VALUE",
        "HTTP", "HTTPS", "WWW", "NSEINDIA", "COM", "GET", "QUOTES"
    }

    for item in candidates:
        if not item:
            continue
        # Strip trailing .NS or .BO
        sym = item.strip().upper()
        if sym.endswith(".NS") or sym.endswith(".BO"):
            sym = sym[:-3]
        
        # Clean non-alphanumeric except hyphen & ampersand
        sym = re.sub(r'[^A-Z0-9&\-]', '', sym)
        
        if len(sym) >= 2 and len(sym) <= 25 and sym not in blacklist and not sym.isdigit():
            if sym not in seen:
                seen.add(sym)
                cleaned.append(sym)
                
    return cleaned


def _pct(a,b): return round((a/b-1)*100,2) if a is not None and b else None

def sanitize_nan(val):
    if isinstance(val, dict):
        return {k: sanitize_nan(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_nan(v) for v in val]
    else:
        try:
            if math.isnan(val) or math.isinf(val):
                return None
        except (TypeError, ValueError):
            pass
    return val

def build_evidence(symbol, cap, info, hist, news):
    import pandas as pd
    gaps=[]
    name=info.get("longName") or info.get("shortName") or symbol.replace(".NS","")
    
    # Dynamically classify cap segment based on marketCap in INR
    mc = info.get("marketCap")
    cap_segment = cap
    if mc:
        if mc >= 200000000000: # ₹20,000 Crores
            cap_segment = "large"
        elif mc >= 50000000000: # ₹5,000 Crores
            cap_segment = "mid"
        else:
            cap_segment = "small"
    else:
        if cap_segment not in ("large", "mid", "small"):
            cap_segment = "small"

    if hist is None or hist.empty:
        gaps += ["price.live","price.day_open","price.day_high","price.day_low","price.prev_close","price.day_change_pct","price.volume","technicals","range_52w"]
        return {"symbol":symbol.replace(".NS",""),"name":name,"cap_segment":cap_segment,"sector":info.get("sector"),"price":{"live":None,"day_open":None,"day_high":None,"day_low":None,"prev_close":None,"day_change_pct":None,"volume":None},"range_52w":{"high":None,"low":None,"pct_from_high":None,"position_pct":None},"technicals":{"rvol":None,"price_vs_sma_pct":None,"window_return_pct":None,"swing_high":None,"swing_low":None,"day_range_position_pct":None,"trend":"sideways"},"analyst":{},"news":{"total":0,"positive":0,"negative":0,"neutral":0,"recent":[]},"data_gaps":gaps}
    close=hist["Close"]; vol=hist["Volume"]
    latest=float(close.iloc[-1]); prev=float(close.iloc[-2]) if len(close)>1 else None
    high=float(hist["High"].iloc[-1]); low=float(hist["Low"].iloc[-1]); op=float(hist["Open"].iloc[-1]); volume=float(vol.iloc[-1])
    avgvol=float(vol.iloc[:-1].tail(20).mean()) if len(vol)>1 else None
    sma20=float(close.tail(20).mean()) if len(close)>=20 else None
    hi52=float(info.get("fiftyTwoWeekHigh") or close.max()); lo52=float(info.get("fiftyTwoWeekLow") or close.min())
    pos=((latest-lo52)/(hi52-lo52)*100) if hi52>lo52 else None
    trend="up" if len(close)>=10 and float(close.iloc[-1])>float(close.iloc[-10]) and (sma20 is None or latest>sma20) else "down" if len(close)>=10 and float(close.iloc[-1])<float(close.iloc[-10]) else "sideways"
    rng=high-low; closepos=((latest-low)/rng*100) if rng else None
    target=info.get("targetMeanPrice"); target_low=info.get("targetLowPrice"); target_high=info.get("targetHighPrice")
    upside=_pct(target,latest)
    rec=info.get("recommendationKey")
    num=info.get("numberOfAnalystOpinions")
    # Yahoo often exposes recommendation percentages elsewhere; unavailable is explicit.
    buy_pct=hold_pct=sell_pct=None
    gaps += []
    for path,val in [("analyst.target_mean",target),("analyst.num_analysts",num),("analyst.consensus",rec),("analyst.buy_pct",buy_pct),("analyst.hold_pct",hold_pct),("analyst.sell_pct",sell_pct)]:
        if val is None: gaps.append(path)
    recent=[]; posn=negn=neut=0
    for item in news[:8] if isinstance(news,list) else []:
        title=item.get("title",""); recent.append({"title":title,"publisher":item.get("publisher"),"published":item.get("providerPublishTime")})
        # Simple local tone, no external NLP dependency.
        lowt=title.lower(); positive=any(w in lowt for w in ["profit","growth","upgrade","strong","beat","buy","surge","record"]); negative=any(w in lowt for w in ["fall","drop","downgrade","weak","loss","cut","probe","risk"])
        if positive and not negative: posn+=1
        elif negative and not positive: negn+=1
        else: neut+=1
    for path,val in [("news.recent",recent), ("price.volume",volume)]:
        if val is None: gaps.append(path)
    res_dict = {"symbol":symbol.replace(".NS",""),"name":name,"cap_segment":cap_segment,"sector":info.get("sector"),
      "price":{"live":round(latest,2),"day_open":round(op,2),"day_high":round(high,2),"day_low":round(low,2),"prev_close":round(prev,2) if prev is not None else None,"day_change_pct":_pct(latest,prev),"volume":int(volume)},
      "range_52w":{"high":hi52,"low":lo52,"pct_from_high":_pct(latest,hi52),"position_pct":round(pos,2) if pos is not None else None},
      "technicals":{"rvol":round(volume/avgvol,2) if avgvol else None,"price_vs_sma_pct":_pct(latest,sma20),"window_return_pct":_pct(latest,float(close.iloc[0])) if len(close) else None,"swing_high":round(float(hist["High"].tail(20).max()),2),"swing_low":round(float(hist["Low"].tail(20).min()),2),"day_range_position_pct":round(closepos,2) if closepos is not None else None,"trend":trend},
      "analyst":{"consensus":rec,"num_analysts":num,"buy_pct":buy_pct,"hold_pct":hold_pct,"sell_pct":sell_pct,"target_mean":target,"target_low":target_low,"target_high":target_high,"upside_pct":upside},
      "news":{"total":posn+negn+neut,"positive":posn,"negative":negn,"neutral":neut,"recent":recent},"data_gaps":sorted(set(gaps))}
    return sanitize_nan(res_dict)


def load_live_evidence(universe):
    import yfinance as yf
    from concurrent.futures import ThreadPoolExecutor
    out = []
    
    flat_tickers = []
    if isinstance(universe, dict):
        for cap, tickers in universe.items():
            for sym in tickers:
                flat_tickers.append((sym, cap))
    elif isinstance(universe, list):
        for sym in universe:
            flat_tickers.append((sym, "unknown"))
            
    def fetch_one(symbol, cap):
        sym_clean = symbol.strip().upper().replace(" ", "")
        if not sym_clean:
            return None
        t = sym_clean if sym_clean.endswith(".NS") else sym_clean + ".NS"
        try:
            y = yf.Ticker(t)
            hist = y.history(period="1mo", interval="1d", auto_adjust=False)
            info = y.info or {}
            news = y.news or []
            return build_evidence(t, cap, info, hist, news)
        except Exception:
            return {
                "symbol": t.replace(".NS", ""),
                "name": t.replace(".NS", ""),
                "cap_segment": cap if cap != "unknown" else "small",
                "sector": None,
                "price": {"live": None, "day_open": None, "day_high": None, "day_low": None, "prev_close": None, "day_change_pct": None, "volume": None},
                "range_52w": {"high": None, "low": None, "pct_from_high": None, "position_pct": None},
                "technicals": {"rvol": None, "price_vs_sma_pct": None, "window_return_pct": None, "swing_high": None, "swing_low": None, "day_range_position_pct": None, "trend": "sideways"},
                "analyst": {"consensus": None, "num_analysts": None, "buy_pct": None, "hold_pct": None, "sell_pct": None, "target_mean": None, "target_low": None, "target_high": None, "upside_pct": None},
                "news": {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "recent": []},
                "data_gaps": ["live data fetch failed"]
            }

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for sym, cap in flat_tickers:
            futures.append(executor.submit(fetch_one, sym, cap))
        for f in futures:
            try:
                res = f.result()
                if res:
                    out.append(res)
            except Exception:
                pass
    return out
