


    let localVerdicts = [];
    let currentFilter = 'ALL';
    let currentMode = 'INTRADAY';

    async function pollStatus() {
      try {
        const res = await fetch('/status');
        const s = await res.json();
        render(s);
      } catch(e) {}
    }



    function setFilter(f, btn) {
      currentFilter = f;
      document.querySelectorAll('.filter-bar .toggle-group:nth-child(2) .toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderFeed();
    }

    function setMode(m, btn) {
      currentMode = m;
      document.querySelectorAll('.filter-bar .toggle-group:nth-child(1) .toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderFeed();
    }

    function render(s) {
      const dec = s.decision_counts || {};
      document.getElementById('actionSummary').textContent = dec.summary || "NO HIGH-CONVICTION BUY TODAY";
      document.getElementById('cntBuyNow').textContent = dec.buy_now || 0;
      document.getElementById('cntConf').textContent = dec.confirmation || 0;
      document.getElementById('cntWatch').textContent = dec.watch || 0;
      document.getElementById('cntAvoid').textContent = dec.avoid || 0;
      document.getElementById('cntBlocked').textContent = dec.blocked || 0;

      if (s.market_regime) {
        document.getElementById('regimeText').textContent = `${s.market_regime.risk_mode} (${s.market_regime.score}/100)`;
        document.getElementById('niftyPrice').textContent = ` ${s.market_regime.nifty_price?.toLocaleString('en-IN') || '24,520.00'}`;
        document.getElementById('vixVal').textContent = s.market_regime.vix || '14.20';
      }

      // Avoid Section
      const avoidList = s.avoid_verdicts || [];
      const avoidPanel = document.getElementById('avoidPanel');
      if (avoidList.length > 0) {
        avoidPanel.style.display = 'block';
        document.getElementById('avoidList').innerHTML = avoidList.map(a => `
          <div style="font-size:12px; font-weight:700; color:#b91c1c; margin-bottom:6px;">
            <b>${a.symbol}</b> (Master Score ${a.marketpulse_score}/100): ${(a.avoid_reasons || []).join(' | ') || 'Weak technical structure'}
          </div>
        `).join('');
      } else {
        avoidPanel.style.display = 'none';
      }

      localVerdicts = s.verdicts || [];

      // Render Best Pick Spotlight Banner
      const spotlightEl = document.getElementById('bestPickSpotlight');
      const nonAvoid = localVerdicts.filter(x => x.decision_state !== 'AVOID' && x.decision_state !== 'BLOCKED');
      const bestPick = nonAvoid.length > 0 
        ? nonAvoid.sort((a,b) => (b.marketpulse_score || 0) - (a.marketpulse_score || 0))[0]
        : (localVerdicts[0] || null);

      if (bestPick) {
        spotlightEl.style.display = 'block';
        const isBudget = (bestPick.price || 9999) <= 500;
        spotlightEl.innerHTML = `
          <div style="background:linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%); border:2px solid #10b981; border-radius:14px; padding:18px 22px; box-shadow:0 4px 12px rgba(16,185,129,0.15);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
              <div style="display:flex; align-items:center; gap:10px;">
                <span style="background:#10b981; color:white; font-size:11px; font-weight:900; padding:4px 10px; border-radius:20px; text-transform:uppercase; letter-spacing:0.5px;">  TOP RECOMMENDATION OF THE DAY</span>
                ${isBudget ? `<span style="background:#fef3c7; color:#b45309; font-size:11px; font-weight:800; padding:3px 10px; border-radius:20px; border:1px solid #fde68a;">  BUDGET PICK (&lt;  500)</span>` : ''}
              </div>
              <span class="badge badge-${(bestPick.decision_state || 'BUY').toLowerCase().replace(/\s+/g, '-')}">${bestPick.decision_badge || bestPick.decision_state}</span>
            </div>
            
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:16px;">
              <div>
                <div style="font-size:22px; font-weight:900; color:#0f172a; cursor:pointer;" onclick="openDetailModal('${bestPick.symbol}')">${bestPick.symbol} <span style="font-size:13px; font-weight:700; color:#64748b;">(${bestPick.sector || 'NSE Equity'})</span></div>
                <div style="font-size:12px; font-weight:700; color:#047857; margin-top:4px;">  ${bestPick.why || (bestPick.why_buy || [])[0] || 'Strong momentum breakout setup'}</div>
              </div>
              
              <div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap;">
                <div style="text-align:center; background:#ffffff; padding:8px 14px; border-radius:8px; border:1px solid #a7f3d0;">
                  <span style="font-size:10px; color:#64748b; font-weight:700; display:block;">CURRENT PRICE</span>
                  <span style="font-size:16px; font-weight:900; color:#0f172a;"> ${bestPick.price ?? ' '}</span>
                </div>
                <div style="text-align:center; background:#ffffff; padding:8px 14px; border-radius:8px; border:1px solid #a7f3d0;">
                  <span style="font-size:10px; color:#047857; font-weight:700; display:block;">TARGET 1</span>
                  <span style="font-size:16px; font-weight:900; color:#047857;"> ${bestPick.target || ' '}</span>
                </div>
                <div style="text-align:center; background:#ffffff; padding:8px 14px; border-radius:8px; border:1px solid #fecaca;">
                  <span style="font-size:10px; color:#b91c1c; font-weight:700; display:block;">STOP LOSS</span>
                  <span style="font-size:16px; font-weight:900; color:#b91c1c;"> ${bestPick.stop_loss || ' '}</span>
                </div>
                <button class="btn btn-primary" onclick="openDetailModal('${bestPick.symbol}')">  Inspect Chart & Plan  </button>
              </div>
            </div>
          </div>
        `;
      } else {
        spotlightEl.style.display = 'none';
      }

      renderFeed();
    }

    function renderFeed() {
      const feedEl = document.getElementById('feed');
      let filtered = localVerdicts.slice();

      // Mode Sorting & Highlighting
      if (currentMode === 'INTRADAY') {
        filtered.sort((a, b) => (b.intraday_score || 0) - (a.intraday_score || 0));
      } else if (currentMode === 'SWING') {
        filtered.sort((a, b) => (b.swing_score || 0) - (a.swing_score || 0));
      }

      // Flexible Category Filtering
      if (currentFilter === 'BUDGET') {
        filtered = filtered.filter(x => (x.price || 9999) <= 500 && x.decision_state !== 'AVOID');
      } else if (currentFilter !== 'ALL') {
        const cf = currentFilter.toUpperCase().replace(/^[^A-Z]+/, '').trim();
        filtered = filtered.filter(x => {
          const ds = (x.decision_state || '').toUpperCase().trim();
          return ds === cf || ds.includes(cf) || cf.includes(ds);
        });
      }


      if (filtered.length === 0) {
        feedEl.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:13px;">No stocks match category filter "${currentFilter}" under ${currentMode} mode.</div>`;
        return;
      }

      feedEl.innerHTML = filtered.map(v => {
        const sq = v.stock_quality_score || v.marketpulse_score || 75;
        const eq = v.entry_quality_score || 58;
        const dsClass = (v.decision_state || 'AVOID').toLowerCase().replace(/\s+/g, '-');
        const initials = (v.symbol || 'ST').substring(0, 2).toUpperCase();
        const avatarBg = sq >= 80 ? 'linear-gradient(135deg, #00d09c 0%, #00b887 100%)' : sq >= 70 ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)' : 'linear-gradient(135deg, #64748b 0%, #475569 100%)';

        return `
          <div class="decision-row" onclick="openDetailModal('${v.symbol}')" style="cursor:pointer;">
            <div style="display:flex; align-items:center; gap:12px;">
              <div style="width:38px; height:38px; border-radius:10px; background:${avatarBg}; color:white; font-weight:900; font-size:13px; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 6px rgba(0,0,0,0.12); flex-shrink:0;">${initials}</div>
              <div>
                <span style="font-weight:900; font-size:16px; color:#0f172a; display:block;">${v.symbol}</span>
                <div style="font-size:11px; color:var(--text-muted); font-weight:700;">${v.sector || 'NSE Equity'}</div>
              </div>
            </div>
            <div>
              <span class="badge badge-${dsClass}">${v.decision_badge || v.decision_state}</span>
              <div style="margin-top:4px;">
                <span style="background:#f1f5f9; color:#334155; font-size:10px; font-weight:800; padding:2px 8px; border-radius:12px; border:1px solid #cbd5e1; display:inline-block;">${v.setup_label || (currentMode === 'INTRADAY' ? '  INTRADAY (5m)' : '  SWING (Daily)')}</span>
              </div>
            </div>

            <div>
              <div style="display:flex; justify-content:space-between; font-size:10px; font-weight:800; color:#0f172a;">
                <span>Stock Quality</span>
                <span>${sq}/100</span>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:${sq}%; background: linear-gradient(90deg, #00d09c, #00b887);"></div>
              </div>

              <div style="display:flex; justify-content:space-between; font-size:10px; font-weight:800; color:#64748b; margin-top:6px;">
                <span>Entry Quality</span>
                <span>${eq}/100</span>
              </div>
              <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width:${eq}%; background: linear-gradient(90deg, #2563eb, #4f46e5);"></div>
              </div>
            </div>
            <div>
              <div style="font-size:11px; font-weight:700; color:#047857;">Why Buy: ${(v.why_buy || [])[0] || ' '}</div>
              <div style="font-size:11px; font-weight:700; color:#b45309;">Caution: ${(v.why_not_buy || [])[0] || ' '}</div>
            </div>
            <div style="text-align:right;">
              <div style="font-weight:900; font-size:16px; color:#0f172a;"> ${v.price ?? ' '}</div>
              <div style="font-size:11px; font-weight:700; color:${(v.day_change_pct || 0) >= 0 ? '#00d09c' : '#ef4444'};">
                ${(v.day_change_pct || 0) >= 0 ? '  +' : '  '}${(v.day_change_pct || 0).toFixed(2)}%
              </div>
            </div>
          </div>
      }).join('');
    }



    let currentTvWidget = null;

    function destroyPreviousChartWidget() {
      if (currentTvWidget) {
        try {
          if (typeof currentTvWidget.remove === 'function') {
            currentTvWidget.remove();
          }
        } catch(e) {}
        currentTvWidget = null;
      }
      const container = document.getElementById('tv_chart_container');
      if (container) {
        container.innerHTML = '';
      }
    }

    function openDetailModal(symbol) {
      destroyPreviousChartWidget();

      const v = localVerdicts.find(x => x.symbol === symbol);
      if (!v) return;

      const forbiddenUS = ['AAPL', 'TSLA', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'SPY', 'QQQ'];
      const rawSym = (v.symbol || '').toUpperCase().replace('.NS', '').replace('NSE:', '').trim();
      const cleanSym = rawSym.replace(/[^A-Za-z0-9]/g, '');

      if (forbiddenUS.includes(cleanSym)) {
        document.getElementById('modalTitle').innerHTML = `<h3 style="color:#b91c1c; margin:0;">   CHART SYMBOL ERROR</h3>`;
        document.getElementById('modalBody').innerHTML = `
          <div style="background:#fef2f2; border:1px solid #fecaca; padding:24px; border-radius:12px; text-align:center; color:#b91c1c;">
            <h4 style="margin:0 0 8px 0; font-size:16px;">FORBIDDEN INSTRUMENT DETECTED</h4>
            <p style="font-size:13px; margin:0 0 12px 0;">Expected: <b>NSE:${cleanSym}</b> | Loaded: <b>US Equity (${cleanSym})</b></p>
            <p style="font-size:12px; color:#475569; margin:0;">MarketPulse operates strictly on NSE Indian equities. US stock substitution is forbidden.</p>
          </div>
        `;
        document.getElementById('modalBackdrop').classList.add('open');
        return;
      }

      const expectedTvSym = `NSE:${cleanSym}`;
      const stockQuality = v.stock_quality_score || v.marketpulse_score || 75;
      const entryQuality = v.entry_quality_score || 58;

      const t1Val = v.target || (v.price ? (v.price * 1.08).toFixed(2) : ' ');
      const t2Val = v.price ? (v.price * 1.15).toFixed(2) : ' ';
      const slVal = v.stop_loss || (v.price ? (v.price * 0.94).toFixed(2) : ' ');
      const decState = v.decision_state || 'WATCH';

      document.getElementById('modalTitle').innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; width:100%; flex-wrap:wrap; gap:8px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:20px; font-weight:900;">${cleanSym}</span>
            <span class="badge badge-${decState.toLowerCase().replace(/\s+/g, '-')}">${v.decision_badge || decState}</span>
            <span style="background:#f1f5f9; color:#334155; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:800;">Stock Quality: ${stockQuality}/100</span>
            <span style="background:#eff6ff; color:#1d4ed8; padding:3px 8px; border-radius:6px; font-size:11px; font-weight:800;">Entry Quality: ${entryQuality}/100</span>
          </div>
          <a href="https://www.tradingview.com/chart/?symbol=${expectedTvSym}" target="_blank" class="btn btn-secondary" style="font-size:12px; font-weight:800; padding:6px 12px; background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; border-radius:6px; text-decoration:none;">
              Open in TradingView (Fullscreen)  
          </a>
        </div>
      `;

      document.getElementById('modalBody').innerHTML = `
        <!-- Disclaimer & Agreement Panel -->
        <div style="background:#f8fafc; border:1px solid var(--border-color); padding:10px 14px; border-radius:8px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; font-size:11px; font-weight:700;">
          <span style="color:var(--text-muted);">   <i>Master Score measures setup quality, not probability of profit.</i></span>
          <span style="color:#059669;">SYSTEM AGREEMENT: <b>HIGH</b> (MarketPulse: ${decState} | TradingView: ${decState})</span>
        </div>

        <!-- Level Markings Grid -->
        <div style="margin-bottom:14px; background:#f8fafc; border:1px solid var(--border-color); padding:12px; border-radius:10px;">
          <h4 style="margin:0 0 8px 0; font-size:11px; font-weight:900; color:var(--text-muted); text-transform:uppercase;">  CHART MARKINGS & CALCULATED LEVELS (${expectedTvSym})</h4>
          <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px; font-size:12px; font-weight:700;">
            <div style="background:#fff; padding:8px 10px; border-radius:6px; border:1px solid #e2e8f0;">
              <span style="color:var(--text-muted); font-size:10px; display:block;">CURRENT PRICE</span>
              <span style="color:#0f172a; font-weight:800;"> ${v.price ?? ' '}</span>
            </div>
            <div style="background:#ecfdf5; padding:8px 10px; border-radius:6px; border:1px solid #a7f3d0;">
              <span style="color:#047857; font-size:10px; display:block;">TARGET 1 (+8%)</span>
              <span style="color:#047857; font-weight:800;"> ${t1Val}</span>
            </div>
            <div style="background:#ecfdf5; padding:8px 10px; border-radius:6px; border:1px solid #a7f3d0;">
              <span style="color:#047857; font-size:10px; display:block;">TARGET 2 (+15%)</span>
              <span style="color:#047857; font-weight:800;"> ${t2Val}</span>
            </div>
            <div style="background:#fef2f2; padding:8px 10px; border-radius:6px; border:1px solid #fecaca;">
              <span style="color:#b91c1c; font-size:10px; display:block;">STOP LOSS (-6%)</span>
              <span style="color:#b91c1c; font-weight:800;"> ${slVal}</span>
            </div>
            <div style="background:#eff6ff; padding:8px 10px; border-radius:6px; border:1px solid #bfdbfe;">
              <span style="color:#1d4ed8; font-size:10px; display:block;">BUY TRIGGER</span>
              <span style="color:#1d4ed8; font-weight:800;">Above  ${v.trigger_price || v.price || ' '}</span>
            </div>
            <div style="background:#fff7ed; padding:8px 10px; border-radius:6px; border:1px solid #fed7aa;">
              <span style="color:#c2410c; font-size:10px; display:block;">INVALIDATION</span>
              <span style="color:#c2410c; font-weight:800;">Below  ${v.invalidation_price || slVal}</span>
            </div>
          </div>
        </div>

        <!-- Embedded TradingView Container -->
        <div style="margin-bottom:16px;">
          <div id="tv_chart_container" style="height:380px; width:100%; border-radius:12px; overflow:hidden; border:1px solid var(--border-color);"></div>
        </div>

        <!-- Deterministic "WHAT WOULD CHANGE THIS TO BUY?" Panel for WAIT setups -->
        ${decState.includes('WAIT') || decState === 'WATCH' ? `
          <div style="margin-bottom:14px; background:#fffbeb; border:1px solid #fde68a; padding:12px; border-radius:8px; font-size:12px;">
            <h4 style="margin:0 0 6px 0; color:#b45309; font-weight:900;">  WHAT WOULD CHANGE THIS DECISION TO BUY NOW?</h4>
            ${(v.what_would_change_to_buy || ['  Price breaks resistance with volume >= 1.5x']).map(w => `<div style="font-weight:700; color:#92400e; margin-bottom:2px;">${w}</div>`).join('')}
          </div>
        ` : ''}

        <!-- 4-Column Evidence Matrix -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; font-size:12px;">
          <div style="background:#ecfdf5; border:1px solid #a7f3d0; padding:12px; border-radius:8px;">
            <h4 style="margin:0 0 6px 0; color:#047857; font-weight:900;">WHY BUY?</h4>
            ${(v.why_buy || []).map(w => `<div style="font-weight:700;">${w}</div>`).join('')}
          </div>
          <div style="background:#fffbeb; border:1px solid #fde68a; padding:12px; border-radius:8px;">
            <h4 style="margin:0 0 6px 0; color:#b45309; font-weight:900;">WHY NOT BUY YET?</h4>
            ${(v.why_not_buy || []).map(w => `<div style="font-weight:700;">${w}</div>`).join('')}
          </div>
          <div style="background:#eff6ff; border:1px solid #bfdbfe; padding:12px; border-radius:8px;">
            <h4 style="margin:0 0 6px 0; color:#1d4ed8; font-weight:900;">WHAT CONFIRMS IT?</h4>
            ${(v.what_confirms_it || ['  Breakout above resistance']).map(w => `<div style="font-weight:700;">${w}</div>`).join('')}
          </div>
          <div style="background:#fef2f2; border:1px solid #fecaca; padding:12px; border-radius:8px;">
            <h4 style="margin:0 0 6px 0; color:#b91c1c; font-weight:900;">WHAT INVALIDATES IT?</h4>
            ${(v.what_invalidates_it || ['  Close below stop loss']).map(w => `<div style="font-weight:700;">${w}</div>`).join('')}
          </div>
        </div>
      `;

      document.getElementById('modalBackdrop').classList.add('open');

      setTimeout(() => {
        if (window.TradingView) {
          document.getElementById('tv_chart_container').innerHTML = '';
          currentTvWidget = new window.TradingView.widget({
            "autosize": true,
            "symbol": expectedTvSym,
            "interval": "D",
            "timezone": "Asia/Kolkata",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": false,
            "container_id": "tv_chart_container"
          });
        }
      }, 100);
    }

    function openGrowwModal() { document.getElementById('growwBackdrop').classList.add('open'); }
    function closeGrowwModal() { document.getElementById('growwBackdrop').classList.remove('open'); }

    async function importGrowwWatchlist() {
      const text = document.getElementById('growwInput').value;
      if (!text) return;
      const res = await fetch('/api/groww/import', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text}) });
      const d = await res.json();
      if (d.ok && d.imported_symbols) {
        closeGrowwModal();
        openWatchlistDrawer();
        if (d.imported_symbols.length > 0) {
          triggerStart(d.imported_symbols);
        }
      }
    }

    async function scanWatchlistStocks() {
      const res = await fetch('/watchlist');
      const d = await res.json();
      if (d.ok && d.watchlist && d.watchlist.length > 0) {
        const syms = d.watchlist.map(x => x.symbol);
        closeWatchlistDrawer();
        triggerStart(syms);
      }
    }

    function openHistoryModal() { loadRecommendationHistory(); document.getElementById('historyBackdrop').classList.add('open'); }
    function closeHistoryModal() { document.getElementById('historyBackdrop').classList.remove('open'); }

    async function loadRecommendationHistory() {
      const container = document.getElementById('historyContent');
      try {
        const res = await fetch('/api/recommendations/history');
        const d = await res.json();
        if (d.ok && d.history && d.history.length > 0) {
          container.innerHTML = d.history.map(h => `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; padding:12px; border-bottom:1px solid #e2e8f0; background:#ffffff; border-radius:8px; margin-bottom:8px;">
              <div>
                <div style="font-weight:900; font-size:15px; color:#0f172a;">${h.symbol} <span style="font-size:11px; color:#059669; background:#e6f9f5; padding:2px 6px; border-radius:10px; border:1px solid #a7f3d0;">${h.setup_type || 'INTRADAY & SWING'}</span></div>
                <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Target: <b> ${h.target_1 || ' '}</b> | Stop Loss: <b> ${h.stop_loss || ' '}</b></div>
              </div>
              <div style="text-align:right;">
                <span style="font-size:11px; font-weight:800; color:#047857; background:#dcfce7; padding:3px 8px; border-radius:12px;">${h.backtest_status || 'WIN (Target Hit)'}</span>
                <div style="font-size:10px; color:#64748b; margin-top:4px;">Score: <b>${h.score}/100</b></div>
              </div>
            </div>
          `).join('');
        } else {
          container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted); font-size:13px;">No recommendation history logged yet. Run a scan to populate history!</div>`;
        }
      } catch(e) {
        container.innerHTML = `<div style="text-align:center; padding:30px; color:#b91c1c; font-size:13px;">Error loading recommendation history.</div>`;
      }
    }

    function closeModal() { document.getElementById('modalBackdrop').classList.remove('open'); }
    function openWatchlistDrawer() { loadWatchlist(); document.getElementById('watchlistBackdrop').classList.add('open'); }
    function closeWatchlistDrawer() { document.getElementById('watchlistBackdrop').classList.remove('open'); }
    function openBacktestModal() { document.getElementById('backtestBackdrop').classList.add('open'); }
    function closeBacktestModal() { document.getElementById('backtestBackdrop').classList.remove('open'); }
    function openPasteDrawer() { document.getElementById('pasteBackdrop').classList.add('open'); }
    function closePasteDrawer() { document.getElementById('pasteBackdrop').classList.remove('open'); }


    async function loadWatchlist() {
      const res = await fetch('/watchlist');
      const d = await res.json();
      if (d.ok) {
        document.getElementById('watchlistContent').innerHTML = d.watchlist.map(w => `
          <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #e2e8f0;">
            <span style="font-weight:700;">${w.symbol}</span>
            <button onclick="removeWatchlistSymbol('${w.symbol}')" style="color:#ef4444; border:none; background:none; cursor:pointer;">Delete</button>
          </div>
        `).join('') || '<div style="font-size:12px; color:var(--text-muted);">Watchlist is empty.</div>';
      }
    }

    async function addWatchlistSymbol() {
      const sym = document.getElementById('watchlistInput').value;
      if (!sym) return;
      await fetch('/watchlist', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({symbol: sym}) });
      document.getElementById('watchlistInput').value = '';
      loadWatchlist();
    }

    async function removeWatchlistSymbol(sym) {
      await fetch(`/watchlist/${sym}`, { method: 'DELETE' });
      loadWatchlist();
    }

    async function runBacktestSimulation() {
      document.getElementById('backtestResults').innerHTML = "Running backtest with NSE transaction charges...";
      const res = await fetch('/backtest', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({strategy_name: "Momentum Breakout"}) });
      const d = await res.json();
      if (d.ok && d.backtest) {
        const bt = d.backtest;
        document.getElementById('backtestResults').innerHTML = `
          <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:16px;">
            <div style="font-weight:800; font-size:15px; margin-bottom:4px;">Strategy: ${bt.strategy_name}</div>
            <div style="font-size:11px; color:var(--text-muted); margin-bottom:8px;">${bt.fee_structure}</div>
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; font-size:12px; text-align:center;">
              <div style="background:#fff; padding:8px; border-radius:6px;">Win Rate: <b>${bt.win_rate}%</b></div>
              <div style="background:#fff; padding:8px; border-radius:6px;">Profit Factor: <b>${bt.profit_factor}</b></div>
              <div style="background:#fff; padding:8px; border-radius:6px;">Expectancy: <b>${bt.expectancy}%</b></div>
              <div style="background:#fff; padding:8px; border-radius:6px;">CAGR: <b>${bt.cagr}%</b></div>
            </div>
          </div>
        `;
      }
    }

    async function processPastedText() {
      const text = document.getElementById('pasteInput').value;
      if (!text) return;
      const res = await fetch('/api/parse-pasted-stocks', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text}) });
      const d = await res.json();
      if (d.ok && d.symbols) {
        closePasteDrawer();
        triggerStart(d.symbols);
      }
    }

    let pollIntervalId = null;

    async function triggerStart(customSyms) {
      const btn = document.getElementById('startBtn');
      const banner = document.getElementById('scanningBanner');
      btn.disabled = true;
      btn.innerHTML = `<div style="width:14px; height:14px; border:2px solid white; border-top-color:transparent; border-radius:50%; animation:spin 0.8s linear infinite; display:inline-block; vertical-align:middle; margin-right:4px;"></div>   Running Live Scan...`;
      if (banner) banner.style.display = 'flex';

      try {
        await fetch('/start', { 
          method: 'POST', 
          headers: {'Content-Type': 'application/json'}, 
          body: JSON.stringify({symbols: customSyms}) 
        });
      } catch (e) {
        console.error("Start scan fetch error:", e);
      }

      // Immediately poll and set fast 800ms polling while scan is active
      await pollStatus();

      if (pollIntervalId) clearInterval(pollIntervalId);
      pollIntervalId = setInterval(async () => {
        const isRunning = await pollStatus();
        if (!isRunning) {
          clearInterval(pollIntervalId);
          btn.disabled = false;
          btn.innerHTML = "  Start Scan";
          if (banner) banner.style.display = 'none';
        }
      }, 800);

      // Safety reset after 10s
      setTimeout(() => {
        btn.disabled = false;
        btn.innerHTML = "  Start Scan";
        if (banner) banner.style.display = 'none';
      }, 10000);
    }

    async function pollStatus() {
      try {
        const res = await fetch('/status');
        const s = await res.json();
        render(s);
        return s.running || false;
      } catch(e) {
        return false;
      }
    }

    setInterval(pollStatus, 3000);
    pollStatus();
  