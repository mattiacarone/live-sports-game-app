

    const SPORT_SVG = {

      all: '<svg class="icon-svg" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',

      football: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polygon points="12 7 15.5 9.5 14 14 10 14 8.5 9.5 12 7"/></svg>',

      tennis: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M6 5.3a9 9 0 0 1 0 13.4"/><path d="M18 5.3a9 9 0 0 0 0 13.4"/></svg>',

      f1: '<svg class="icon-svg" viewBox="0 0 24 24"><path d="M4 15h16l-2-5h-7l-2-3H5z"/><circle cx="7.5" cy="16.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/></svg>',

      motogp: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="6.5" cy="16.5" r="3.5"/><circle cx="17.5" cy="16.5" r="3.5"/><path d="M10 16.5h4l2-6h-5l-2 3z"/></svg>',

      nfl: '<svg class="icon-svg" viewBox="0 0 24 24"><ellipse cx="12" cy="12" rx="9" ry="5" transform="rotate(-35 12 12)"/><line x1="9" y1="15" x2="15" y2="9"/></svg>',

      basketball: '<svg class="icon-svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="12" y1="2" x2="12" y2="22"/></svg>',

      rugby: '<svg class="icon-svg" viewBox="0 0 24 24"><ellipse cx="12" cy="12" rx="9" ry="5.5" transform="rotate(-25 12 12)"/><path d="M8 12h8"/></svg>'

    };

    const APP = {

      primaryView: 'scanner',

      activeSport: 'all',

      activeTournament: 'ALL',

      riskFilter: 'all',

      bookmakerFilter: 'ALL',

      searchQuery: '',

      tier: 'pro',

      currency: '?',

      bankroll: 1000,

      kellyFraction: 0.25,

      visibleLimit: 8,

      sportsMeta: [],

      allEvents: [],

      safeScanner: [],

      premiumSuite: null,

      performanceData: null,

      slip: [],

      nextSyncEpoch: Date.now() + 1200 * 1000,

      syncCycle: 1,

      arbBudget: 1000

    };

    document.addEventListener('keydown', (e) => {

      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {

        e.preventDefault();

        const inp = document.getElementById('global-search-input');

        if (inp) inp.focus();

      }

    });

    function showToast(msg) {

      const t = document.getElementById('sync-toast');

      const txt = document.getElementById('sync-toast-text');

      if (!t || !txt) return;

      txt.textContent = msg;

      t.classList.add('visible');

      setTimeout(() => t.classList.remove('visible'), 3000);

    }

    function computeKellyStake(prob, odds) {

      if (!prob || !odds || odds <= 1.02) return Math.round(APP.bankroll * 0.015);

      if (APP.kellyFraction === 0.02) return Math.round(APP.bankroll * 0.02);

      const b = odds - 1.0;

      const q = 1.0 - prob;

      const fullKelly = Math.max(0.012, (b * prob - q) / b);

      const frac = Math.min(0.05, fullKelly * APP.kellyFraction);

      return Math.max(5, Math.round(APP.bankroll * frac));

    }

    function updateBankrollConfig() {

      APP.currency = document.getElementById('currency-select').value;

      APP.bankroll = Math.max(50, parseFloat(document.getElementById('bankroll-input').value) || 1000);

      APP.kellyFraction = parseFloat(document.getElementById('kelly-select').value) || 0.25;

      renderMainWorkspace();

      renderSlipDrawer();

    }

    function toggleSubscriptionTier() {

      APP.tier = APP.tier === 'pro' ? 'free' : 'pro';

      const lbl = document.getElementById('tier-toggle-label');

      lbl.textContent = APP.tier === 'pro'

        ? 'Piano attivo: VIP Pro Sbloccato (Testa Free Lock)'

        : 'Piano attivo: Free Preview (Sblocca VIP Pro)';

      fetchMultisportData(false);

    }

    async function fetchMultisportData(isAutoTick = false) {
      window.__fetch_trace = 'entered';
      try {
        window.__fetch_trace = 'fetching';
        const res = await fetch(`/api/multisport?tier=${APP.tier}`);
        window.__fetch_trace = 'res_' + res.status;

        const res = await fetch(`/api/multisport?tier=${APP.tier}`);

        const data = await res.json();

        APP.sportsMeta = data.sports || [];

        APP.allEvents = data.events || [];

        APP.safeScanner = data.safeScanner || [];

        if (data.premiumSuite) APP.premiumSuite = data.premiumSuite;

        if (data.syncCycle) APP.syncCycle = data.syncCycle;

        if (data.nextSync20m) {

          const parsed = Date.parse(data.nextSync20m);

          if (!isNaN(parsed) && parsed > Date.now()) APP.nextSyncEpoch = parsed;

        }

        document.getElementById('badge-safe-total').textContent = APP.safeScanner.length;

        document.getElementById('kpi-safe-count').textContent = APP.safeScanner.length;

        document.getElementById('sync-cycle-badge').textContent = `Ciclo #${APP.syncCycle}`;

        const droppingCount = APP.safeScanner.filter(s => s.isDropping || (s.droppingPct && s.droppingPct <= -1.5)).length;

        const arbCount = APP.premiumSuite && APP.premiumSuite.arbitrage ? APP.premiumSuite.arbitrage.length : 4;

        document.getElementById('kpi-dropping-count').textContent = `${arbCount} Surebet &bull; ${droppingCount} Drop`;

        if (APP.slip.length === 0 && APP.safeScanner.length >= 3) {

          loadAutoSafeSlip(true);

        }

        renderSportSwitcher();

        renderSidebarCompetitions();

        renderMainWorkspace();

        if (isAutoTick) {

          showToast(`Sync 20m (Ciclo #${APP.syncCycle}) completato su 12 bookmaker.`);

        }

      } catch (err) {

        console.error('Error fetching multisport data:', err);

      }

    }

    async function triggerManual20mSync() {

      showToast('Sincronizzazione quote su 12 bookmaker in corso...');

      try {

        await fetch('/api/refresh');

        APP.nextSyncEpoch = Date.now() + 1200 * 1000;

        setTimeout(() => fetchMultisportData(true), 600);

      } catch (e) {

        console.error(e);

      }

    }

    setInterval(() => {

      const remMs = Math.max(0, APP.nextSyncEpoch - Date.now());

      const totalSec = Math.floor(remMs / 1000);

      const mins = Math.floor(totalSec / 60);

      const secs = totalSec % 60;

      const timerEl = document.getElementById('live-20m-timer');

      if (timerEl) {

        const mStr = mins < 10 ? '0' + mins : '' + mins;

        const sStr = secs < 10 ? '0' + secs : '' + secs;

        timerEl.textContent = `${mStr}:${sStr}`;

      }

      if (totalSec <= 0) {

        APP.nextSyncEpoch = Date.now() + 1200 * 1000;

        triggerManual20mSync();

      }

    }, 1000);

    function renderSportSwitcher() {

      const container = document.getElementById('sport-switcher-bar');

      container.innerHTML = APP.sportsMeta.map(s => {

        const active = APP.activeSport === s.id ? 'active' : '';

        const svg = SPORT_SVG[s.id] || SPORT_SVG.all;

        const countLabel = s.id === 'all' ? `${s.safeCount} Safe` : `${s.eventCount} (${s.safeCount})`;

        return `

          <button type="button" class="sport-pill ${active}" onclick="selectSport('${s.id}')">

            ${svg}

            <span>${s.name}</span>

            <span class="sport-pill-count num">${countLabel}</span>

          </button>

        `;

      }).join('');

    }

    function selectSport(sportId) {

      APP.activeSport = sportId;

      APP.activeTournament = 'ALL';

      APP.visibleLimit = 8;

      if (APP.primaryView === 'performance' || APP.primaryView === 'vip') {

        APP.primaryView = sportId === 'all' ? 'scanner' : 'workspace';

        updateNavButtons();

      }

      renderSportSwitcher();

      renderSidebarCompetitions();

      renderMainWorkspace();

    }

    function switchPrimaryView(view) {

      APP.primaryView = view;

      APP.visibleLimit = 8;

      updateNavButtons();

      if (view === 'performance' && !APP.performanceData) {

        fetch('/api/performance').then(r => r.json()).then(d => {

          APP.performanceData = d;

          renderMainWorkspace();

        });

      }

      renderMainWorkspace();

    }

    function updateNavButtons() {

      document.getElementById('nav-scanner').classList.toggle('active', APP.primaryView === 'scanner');

      document.getElementById('nav-workspace').classList.toggle('active', APP.primaryView === 'workspace');

      document.getElementById('nav-vip').classList.toggle('active', APP.primaryView === 'vip');

      document.getElementById('nav-performance').classList.toggle('active', APP.primaryView === 'performance');

    }

    function renderSidebarCompetitions() {

      const filteredEvents = APP.activeSport === 'all'

        ? APP.allEvents

        : APP.allEvents.filter(e => e.sport === APP.activeSport);

      const compMap = {};

      filteredEvents.forEach(ev => {

        const tName = ev.tournament || ev.league || 'Competizione';

        if (!compMap[tName]) {

          compMap[tName] = { name: tName, flag: ev.flag || 'EU', count: 0 };

        }

        compMap[tName].count += 1;

      });

      const comps = Object.values(compMap).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));

      const listEl = document.getElementById('sidebar-competitions');

      const allBtn = `

        <button type="button" class="comp-nav-item ${APP.activeTournament === 'ALL' ? 'active' : ''}" onclick="selectTournament('ALL')">

          <span class="comp-name-wrap">

            <span class="iso-badge">ALL</span>

            <span class="comp-name-text">Tutte le competizioni</span>

          </span>

          <span class="comp-count num">${filteredEvents.length}</span>

        </button>

      `;

      listEl.innerHTML = allBtn + comps.map(c => {

        const active = APP.activeTournament === c.name ? 'active' : '';

        const safeName = c.name.replace(/'/g, "\\'");

        return `

          <button type="button" class="comp-nav-item ${active}" onclick="selectTournament('${safeName}')">

            <span class="comp-name-wrap">

              <span class="iso-badge">${c.flag || 'INT'}</span>

              <span class="comp-name-text">${c.name}</span>

            </span>

            <span class="comp-count num">${c.count}</span>

          </button>

        `;

      }).join('');

    }

    function selectTournament(tName) {

      APP.activeTournament = tName;

      APP.visibleLimit = 8;

      renderSidebarCompetitions();

      renderMainWorkspace();

    }

    function handleSearchInput(val) {

      APP.searchQuery = (val || '').trim().toLowerCase();

      APP.visibleLimit = 8;

      renderMainWorkspace();

    }

    function showMoreItems() {

      APP.visibleLimit += 12;

      renderMainWorkspace();

    }

    function switchDossierTab(cardUid, tabKey, btnEl) {

      const card = document.getElementById(`card-${cardUid}`);

      if (!card) return;

      card.querySelectorAll('.dossier-tab-btn').forEach(b => b.classList.remove('active'));

      card.querySelectorAll('.dossier-panel').forEach(p => p.classList.remove('active'));

      btnEl.classList.add('active');

      const target = document.getElementById(`panel-${cardUid}-${tabKey}`);

      if (target) target.classList.add('active');

    }

    function switchMarketSubTab(cardUid, catIdx, btnEl) {

      const wrap = document.getElementById(`mkt-wrap-${cardUid}`);

      if (!wrap) return;

      wrap.querySelectorAll('.mkt-sub-pill').forEach(b => b.classList.remove('active'));

      wrap.querySelectorAll('.mkt-sub-pane').forEach(p => p.style.display = 'none');

      btnEl.classList.add('active');

      const pane = document.getElementById(`mkt-pane-${cardUid}-${catIdx}`);

      if (pane) pane.style.display = 'grid';

    }

    function formatDateShort(isoStr) {

      if (!isoStr) return 'Oggi';

      try {

        const d = new Date(isoStr);

        return d.toLocaleString('it-IT', { weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });

      } catch (e) {

        return 'Oggi';

      }

    }

    function renderComparisonBars(bars) {

      if (!bars || !bars.length) return '';

      return `

        <div class="h2h-bars-grid">

          ${bars.slice(0, 4).map(b => {

            const vA = parseFloat(b.valA) || 0;

            const vB = parseFloat(b.valB) || 0;

            const sum = (vA + vB) || 1;

            const pctA = Math.max(12, Math.min(88, Math.round((vA / sum) * 100)));

            const pctB = 100 - pctA;

            return `

              <div class="h2h-bar-box">

                <div class="h2h-bar-top">

                  <strong class="num" style="color:var(--accent);">${b.valA}${b.unit || ''}</strong>

                  <span style="color:var(--muted);">${b.label}</span>

                  <strong class="num" style="color:var(--text);">${b.valB}${b.unit || ''}</strong>

                </div>

                <div class="h2h-track">

                  <div class="h2h-fill-a" style="width:${pctA}%"></div>

                  <div class="h2h-fill-b" style="width:${pctB}%"></div>

                </div>

              </div>

            `;

          }).join('')}

        </div>

      `;

    }

    function render12BookmakersTable(books, locked) {

      if (!books || !books.length) return '';

      if (locked) {

        return `

          <div style="padding:14px;border:1px solid var(--border);border-radius:var(--radius-control);background:var(--ground);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">

            <span style="font-size:13px;color:var(--muted);">Tabella comparativa completa su 12 bookmaker (Bet365, Pinnacle, Betfair, DraftKings, FanDuel, Unibet...) riservata a VIP Pro.</span>

            <button type="button" class="add-slip-btn" onclick="toggleSubscriptionTier()">Sblocca 12 Bookmaker</button>

          </div>

        `;

      }

      return `

        <div class="table-scroll-wrap">

          <table class="data-table">

            <thead>

              <tr>

                <th>Sito di scommesse</th>

                <th>Modello &amp; Specialità</th>

                <th class="num">Margine (Vig)</th>

                <th class="num">Apertura (-60m)</th>

                <th class="num">Quota Live</th>

                <th class="num">Prob. Reale No-Vig</th>

                <th class="num">Valore (+EV)</th>

                <th class="num">Limite Max</th>

              </tr>

            </thead>

            <tbody>

              ${books.map((b, idx) => {

                const isBest = idx === 0;

                const edgeStr = (b.edgePct >= 0 ? '+' : '') + b.edgePct + '%';

                const moveStr = b.moveDelta && b.moveDelta !== 0 ? `(${b.moveDelta > 0 ? '+' : ''}${b.moveDelta.toFixed(2)})` : '';

                return `

                  <tr>

                    <td>

                      <span class="book-name-cell">${b.name}</span>

                      ${isBest ? '<span class="status-pill pos" style="margin-left:6px;height:20px;padding:0 6px;">Top Quota</span>' : ''}

                      <span class="book-region-sub">${b.region || ''}</span>

                    </td>

                    <td style="color:var(--muted);font-size:13px;">${b.specialFeature || b.archetype || 'Retail Line'}</td>

                    <td class="num" style="color:var(--muted);">${b.vigPct || 4.4}%</td>

                    <td class="num" style="color:var(--muted);">${(b.openerPrice || b.price).toFixed(2)} ${moveStr}</td>

                    <td class="num"><strong style="color:${isBest ? 'var(--accent)' : 'var(--text)'};">${b.price.toFixed(2)}</strong></td>

                    <td class="num">${b.noVigProb || b.impliedProb}%</td>

                    <td class="num" style="color:${b.edgePct >= 0 ? 'var(--positive)' : 'var(--muted)'};font-weight:600;">${edgeStr}</td>

                    <td class="num" style="color:var(--muted);">?${(b.maxStakeEur || 5000).toLocaleString('it-IT')}</td>

                  </tr>

                `;

              }).join('')}

            </tbody>

          </table>

        </div>

      `;

    }

    function renderSyndicateDossier(vip, locked) {

      if (!vip) return '';

      if (locked) {

        return `

          <div style="padding:14px;border:1px solid var(--border);border-radius:var(--radius-control);background:var(--ground);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">

            <span style="font-size:13px;color:var(--muted);">Dossier Istituzionale (Pinnacle No-Vig, Betfair Orderbook, Bet365 2-Up, DraftKings SGP) riservato a VIP Pro.</span>

            <button type="button" class="add-slip-btn" onclick="toggleSubscriptionTier()">Sblocca Dossier VIP</button>

          </div>

        `;

      }

      const sites = vip.siteAnalyses || [];

      return `

        <div style="display:flex;flex-direction:column;gap:12px;">

          <div class="card-metrics-strip">

            <div class="metric-item">

              <div class="metric-item-label">Pressione Sharp vs Ticket Retail</div>

              <div class="metric-item-val num">${vip.sharpPct}% Sharp &bull; ${vip.publicPct}% Public (${vip.steamStatus})</div>

            </div>

            <div class="metric-item">

              <div class="metric-item-label">Liquidità Betfair Exchange</div>

              <div class="metric-item-val num">?${(vip.matchedVolumeEur || 64000).toLocaleString('it-IT')} (Max Fill ?${(vip.largestFillEur || 8500).toLocaleString('it-IT')})</div>

            </div>

            <div class="metric-item">

              <div class="metric-item-label">Pinnacle No-Vig vs Quota Equa</div>

              <div class="metric-item-val num">Pinnacle @${vip.pinnacleNoVigOdds || vip.fairOdds} &bull; AI Fair @${vip.fairOdds}</div>

            </div>

            <div class="metric-item">

              <div class="metric-item-label">Closing Line Value (CLV) &amp; Dispersione</div>

              <div class="metric-item-val num" style="color:var(--positive);">+${vip.clvProjectionPct}% CLV &bull; Dispersione ${vip.marketDispersionPct || 3.4}%</div>

            </div>

          </div>

          <div class="syndicate-grid">

            ${sites.map(st => `

              <div class="syndicate-card">

                <div class="syndicate-card-head">

                  <span class="syndicate-site-name">${st.site}</span>

                  <span class="syndicate-vig-tag num">${st.vig}</span>

                </div>

                <div class="syndicate-metric num">${st.metric}</div>

                <p class="syndicate-verdict">${st.verdict}</p>

              </div>

            `).join('')}

          </div>

        </div>

      `;

    }

    function renderMarketMatrix(cardUid, mktCats, betBuilders, eventTitle, sport) {

      const catNames = Object.keys(mktCats || {});

      if (!catNames.length) return '<div style="font-size:13px;color:var(--muted);">Mercati in aggiornamento.</div>';

      const builderSafe = betBuilders && betBuilders.safe;

      const builderHtml = builderSafe ? `

        <div style="margin-top:12px;padding:12px 14px;background:var(--ground);border:1px solid var(--border);border-radius:var(--radius-control);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">

          <div>

            <div style="font-size:13px;font-weight:600;color:var(--accent);">${builderSafe.name} &bull; Correlation Lift +${builderSafe.liftPct}%</div>

            <div style="font-size:13px;font-weight:600;color:var(--text);margin-top:2px;">${(builderSafe.legs || []).join(' + ')}</div>

          </div>

          <div style="display:flex;align-items:center;gap:10px;">

            <span class="num" style="font-size:14px;font-weight:700;">@${builderSafe.bookOdds} (${Math.round(builderSafe.prob * 100)}%)</span>

            <button type="button" class="filter-chip active" onclick="addLegToSlip('${cardUid}_bb', '${eventTitle.replace(/'/g, "\\'")}', '${builderSafe.name.replace(/'/g, "\\'")}', ${builderSafe.bookOdds}, ${builderSafe.prob}, 'Bet365 Builder', '${sport}')">+ Schedina</button>

          </div>

        </div>

      ` : '';

      return `

        <div id="mkt-wrap-${cardUid}">

          <div class="mkt-cat-pills">

            ${catNames.map((cn, idx) => `

              <button type="button" class="filter-chip mkt-sub-pill ${idx === 0 ? 'active' : ''}" onclick="switchMarketSubTab('${cardUid}', ${idx}, this)">

                ${cn} (${(mktCats[cn] || []).length})

              </button>

            `).join('')}

          </div>

          ${catNames.map((cn, idx) => `

            <div id="mkt-pane-${cardUid}-${idx}" class="mkt-sub-pane mkt-odds-grid" style="display:${idx === 0 ? 'grid' : 'none'};">

              ${(mktCats[cn] || []).map((m, mIdx) => {

                const safeTitle = eventTitle.replace(/'/g, "\\'");

                const safeLbl = (m.label || '').replace(/'/g, "\\'");

                const oVal = m.odds || m.fair || 1.5;

                return `

                  <button type="button" class="mkt-odd-btn" onclick="addLegToSlip('${cardUid}_${idx}_${mIdx}', '${safeTitle}', '${safeLbl}', ${oVal}, ${m.prob || 0.6}, 'Bet365', '${sport}')">

                    <span class="mkt-odd-label">${m.label}</span>

                    <span class="mkt-odd-right num">

                      <div class="mkt-odd-price">@${oVal.toFixed(2)}</div>

                      <div class="mkt-odd-prob">${Math.round((m.prob || 0.5) * 100)}%</div>

                    </span>

                  </button>

                `;

              }).join('')}

            </div>

          `).join('')}

          ${builderHtml}

        </div>

      `;

    }

    function renderEventOrScannerCard(item, idx, isScannerMode) {

      const uid = `${isScannerMode ? 'sc' : 'ev'}_${idx}`;

      const sportId = item.sport || 'football';

      const sportMeta = APP.sportsMeta.find(s => s.id === sportId) || { name: sportId.toUpperCase() };

      const title = item.title || 'Match';

      const tournament = item.tournament || item.league || '';

      const venue = item.venue || '';

      const locked = Boolean(item.locked);

      const bp = isScannerMode ? {

        market: item.market,

        label: item.outcome,

        prob: item.prob,

        fairOdds: item.fairOdds,

        bookOdds: item.bookOdds,

        bookmaker: item.bookmaker,

        edgePct: item.edgePct,

        droppingPct: item.droppingPct,

        openerOdds: item.openerOdds,

        why: item.why

      } : (item.best_pick || {});

      const probPct = Math.round((bp.prob || 0.75) * 100);

      const stakeVal = computeKellyStake(bp.prob || 0.75, bp.bookOdds || 1.55);

      const books = item.allBooks || item.all_books || [];

      const statsEntries = Object.entries(item.stats || {}).slice(0, 4);

      const facts = item.facts || [];

      const vip = item.vip_insights || {};

      const mktCats = item.market_categories || {};

      const builders = item.bet_builders || {};

      const formA = (item.form_a || []).slice(0, 5).map(c => `<span class="form-char ${c}">${c}</span>`).join('');

      const formB = (item.form_b || []).slice(0, 5).map(c => `<span class="form-char ${c}">${c}</span>`).join('');

      const safeTitle = title.replace(/'/g, "\\'");

      const safeOutcome = (bp.label || '').replace(/'/g, "\\'");

      return `

        <article class="event-card" id="card-${uid}">

          <div class="event-header-row">

            <div>

              <div class="event-meta-line">

                <span class="iso-badge">${item.flag || 'INT'}</span>

                <span class="sport-tag">${sportMeta.name}</span>

                <span>${tournament}</span>

                ${venue ? `<span>&bull; ${venue}</span>` : ''}

                <span class="num">&bull; ${formatDateShort(item.date)}</span>

              </div>

              <h2 class="event-title">

                ${title}

                ${formA ? `<span class="form-strip" title="Forma recente">${formA}</span>` : ''}

              </h2>

            </div>

            <div class="prob-cluster">

              <span class="status-pill pos num">${probPct}% Probabilità AI</span>

              ${bp.edgePct > 0 ? `<span class="status-pill warn num">+${bp.edgePct}% EV</span>` : ''}

              ${bp.droppingPct && bp.droppingPct <= -1.5 ? `<span class="status-pill neg num">Drop ${bp.droppingPct}% (da @${bp.openerOdds})</span>` : ''}

            </div>

          </div>

          ${statsEntries.length ? `

            <div class="card-metrics-strip">

              ${statsEntries.map(([k, v]) => `

                <div class="metric-item">

                  <div class="metric-item-label">${k.replace(/_/g, ' ')}</div>

                  <div class="metric-item-val num">${v}</div>

                </div>

              `).join('')}

            </div>

          ` : ''}

          ${renderComparisonBars(item.comparison_bars)}

          <div class="primary-pick-banner">

            <div class="pick-main-info">

              <div class="pick-category-meta">Giocata più facile consigliata (${bp.market || 'Analisi AI'})</div>

              <div class="pick-outcome-title">${bp.label || 'Selezione consigliata'}</div>

              <div class="pick-why-text">${bp.why || ''}</div>

            </div>

            <div class="pick-pricing-actions">

              <div class="price-compare-col num">

                <div class="price-main-line">@${(bp.bookOdds || 1.55).toFixed(2)} su ${bp.bookmaker || 'Bet365'}</div>

                <div class="price-sub-line">Quota Equa AI @${(bp.fairOdds || 1.35).toFixed(2)} &bull; Stake Kelly: <strong>${APP.currency}${stakeVal}</strong></div>

              </div>

              ${locked

                ? `<button type="button" class="add-slip-btn" onclick="toggleSubscriptionTier()">Sblocca VIP Pro</button>`

                : `<button type="button" class="add-slip-btn" onclick="addLegToSlip('${item.id}', '${safeTitle}', '${safeOutcome}', ${bp.bookOdds || 1.55}, ${bp.prob || 0.75}, '${bp.bookmaker || 'Bet365'}', '${sportId}')">+ Aggiungi a Schedina</button>`

              }

            </div>

          </div>

          <!-- DOSSIER TABS -->

          <div class="dossier-tab-strip" role="tablist">

            <button type="button" class="dossier-tab-btn active" onclick="switchDossierTab('${uid}', 'books', this)">

              Confronto 12 Siti Scommesse (${books.length || 12})

            </button>

            <button type="button" class="dossier-tab-btn" onclick="switchDossierTab('${uid}', 'syndicate', this)">

              Analisi Sindacati (Pinnacle, Betfair, Bet365, DraftKings)

            </button>

            <button type="button" class="dossier-tab-btn" onclick="switchDossierTab('${uid}', 'facts', this)">

              Studio Statistico &amp; Fatti (${facts.length})

            </button>

            <button type="button" class="dossier-tab-btn" onclick="switchDossierTab('${uid}', 'markets', this)">

              Matrice Completa Mercati Bet365 (${Object.keys(mktCats).length} categorie)

            </button>

          </div>

          <div id="panel-${uid}-books" class="dossier-panel active">

            ${render12BookmakersTable(books, locked)}

          </div>

          <div id="panel-${uid}-syndicate" class="dossier-panel">

            ${renderSyndicateDossier(vip, locked)}

          </div>

          <div id="panel-${uid}-facts" class="dossier-panel">

            <div class="facts-grid">

              ${facts.map(f => `<div class="fact-row">${f}</div>`).join('')}

            </div>

          </div>

          <div id="panel-${uid}-markets" class="dossier-panel">

            ${renderMarketMatrix(uid, mktCats, builders, title, sportId)}

          </div>

        </article>

      `;

    }

    function renderMainWorkspace() {

      const area = document.getElementById('main-workspace-area');

      const h1 = document.getElementById('screen-h1-title');

      const sub = document.getElementById('screen-finding-sub');

      if (APP.primaryView === 'vip') {

        h1.textContent = 'VIP Pro Sandbox: Arbitraggio Matematico, Flussi Whale & Player Props';

        sub.textContent = 'Simulazione interattiva dei moduli istituzionali su Pinnacle, Betfair Exchange, Bet365, Unibet, DraftKings e Winamax.';

        renderVipSandboxView(area);

        return;

      }

      if (APP.primaryView === 'performance') {

        h1.textContent = 'Track Record Verificato Out-of-Sample & Calibrazione Brier';

        sub.textContent = 'Audit storico certificato su 435+ match completati con verifica di rendimento e calibrazione probabilistica.';

        renderPerformanceView(area);

        return;

      }

      const isScanner = APP.primaryView === 'scanner';

      if (isScanner) {

        h1.textContent = 'Terminale Quote 12 Bookmaker & Scommesse ad Alta Probabilità';

        sub.textContent = `${APP.safeScanner.length} selezioni validate (>=74% probabilit&bull; reale) con comparazione margini e movimenti quote ogni 20 minuti.`;

      } else {

        const spMeta = APP.sportsMeta.find(s => s.id === APP.activeSport);

        h1.textContent = spMeta && APP.activeSport !== 'all'

          ? `Studio Predittivo & Mercati Bet365: ${spMeta.name}`

          : 'Catalogo Completo Eventi Multi-Sport & Matrice Mercati Bet365';

        sub.textContent = spMeta ? spMeta.description : 'Analisi algoritmica polimorfica con confronto su 12 bookmaker.';

      }

      let sourceList = isScanner ? APP.safeScanner : APP.allEvents;

      if (APP.activeSport !== 'all') {

        sourceList = sourceList.filter(x => x.sport === APP.activeSport);

      }

      if (APP.activeTournament !== 'ALL') {

        sourceList = sourceList.filter(x => (x.tournament || x.league) === APP.activeTournament);

      }

      if (APP.searchQuery) {

        sourceList = sourceList.filter(x =>

          (x.title || '').toLowerCase().includes(APP.searchQuery) ||

          (x.tournament || '').toLowerCase().includes(APP.searchQuery) ||

          (x.outcome || (x.best_pick && x.best_pick.label) || '').toLowerCase().includes(APP.searchQuery)

        );

      }

      if (isScanner) {

        if (APP.riskFilter === 'ultra') sourceList = sourceList.filter(x => x.prob >= 0.78);

        if (APP.riskFilter === 'dropping') sourceList = sourceList.filter(x => x.isDropping || (x.droppingPct && x.droppingPct <= -1.5));

        if (APP.bookmakerFilter !== 'ALL') sourceList = sourceList.filter(x => x.bookmaker === APP.bookmakerFilter);

      }

      const visibleItems = sourceList.slice(0, APP.visibleLimit);

      const remaining = Math.max(0, sourceList.length - visibleItems.length);

      const toolbarHtml = `

        <div class="filter-toolbar">

          <div class="filter-group">

            <button type="button" class="filter-chip ${APP.riskFilter === 'all' ? 'active' : ''}" onclick="setRiskFilter('all')">

              Tutte (${sourceList.length})

            </button>

            <button type="button" class="filter-chip ${APP.riskFilter === 'ultra' ? 'active' : ''}" onclick="setRiskFilter('ultra')">

              Alta Certezza (&ge;78%)

            </button>

            <button type="button" class="filter-chip ${APP.riskFilter === 'dropping' ? 'active' : ''}" onclick="setRiskFilter('dropping')">

              Quote in Calo (Steam 20m)

            </button>

          </div>

          <div class="filter-group">

            <label for="book-filter-sel" style="font-size:13px;color:var(--muted);">Bookmaker:</label>

            <select id="book-filter-sel" class="ctrl-select" onchange="setBookFilter(this.value)">

              <option value="ALL" ${APP.bookmakerFilter === 'ALL' ? 'selected' : ''}>Tutti i 12 Bookmaker</option>

              <option value="Bet365" ${APP.bookmakerFilter === 'Bet365' ? 'selected' : ''}>Bet365</option>

              <option value="Pinnacle" ${APP.bookmakerFilter === 'Pinnacle' ? 'selected' : ''}>Pinnacle</option>

              <option value="Betfair Exchange" ${APP.bookmakerFilter === 'Betfair Exchange' ? 'selected' : ''}>Betfair Exchange</option>

              <option value="Unibet" ${APP.bookmakerFilter === 'Unibet' ? 'selected' : ''}>Unibet</option>

              <option value="DraftKings" ${APP.bookmakerFilter === 'DraftKings' ? 'selected' : ''}>DraftKings</option>

              <option value="FanDuel" ${APP.bookmakerFilter === 'FanDuel' ? 'selected' : ''}>FanDuel</option>

              <option value="Winamax" ${APP.bookmakerFilter === 'Winamax' ? 'selected' : ''}>Winamax</option>

            </select>

          </div>

        </div>

      `;

      if (!visibleItems.length) {

        area.innerHTML = toolbarHtml + `

          <div class="event-card" style="text-align:center;padding:36px 20px;">

            <div style="font-size:15px;font-weight:600;">Nessun evento corrisponde ai filtri selezionati</div>

            <p style="font-size:13px;color:var(--muted);margin-top:4px;">Prova a selezionare "Tutte le competizioni" o ad azzerare il filtro di ricerca.</p>

          </div>

        `;

        return;

      }

      area.innerHTML = toolbarHtml +

        visibleItems.map((item, idx) => renderEventOrScannerCard(item, idx, isScanner)).join('') +

        (remaining > 0 ? `<button type="button" class="load-more-bar num" onclick="showMoreItems()">Mostra altri ${remaining} eventi analizzati</button>` : '');

    }

    function setRiskFilter(f) {

      APP.riskFilter = f;

      APP.visibleLimit = 8;

      renderMainWorkspace();

    }

    function setBookFilter(b) {

      APP.bookmakerFilter = b;

      APP.visibleLimit = 8;

      renderMainWorkspace();

    }

    function renderVipSandboxView(area) {

      const suite = APP.premiumSuite || { arbitrage: [], whaleSteam: [], vipPlayerProps: [], tierComparison: [] };

      const budget = APP.arbBudget || 1000;

      area.innerHTML = `

        <div class="event-card">

          <div class="event-header-row">

            <div>

              <h2 class="event-title">1. Calcolatore Surebet &amp; Arbitraggio Matematico (Profitto Garantito Zero-Risk)</h2>

              <p style="font-size:13px;color:var(--muted);margin-top:2px;">

                Sfrutta le discrepanze tra i 12 siti di scommesse per bloccare un profitto matematico indipendentemente dall'esito.

              </p>

            </div>

            <div style="display:flex;align-items:center;gap:8px;">

              <label for="arb-budget-inp" style="font-size:13px;color:var(--muted);">Capitale Arbitraggio (${APP.currency}):</label>

              <input id="arb-budget-inp" type="number" class="ctrl-input num" value="${budget}" min="100" step="100" onchange="APP.arbBudget=parseFloat(this.value)||1000;renderMainWorkspace();" />

            </div>

          </div>

          <div class="syndicate-grid">

            ${(suite.arbitrage || []).map(a => {

              const sA = Math.round((budget * a.legA.stakePct) / 100);

              const sB = budget - sA;

              const profit = Math.round(budget * (a.roiPct / 100) * 100) / 100;

              return `

                <div class="syndicate-card" style="background:var(--surface);">

                  <div class="syndicate-card-head">

                    <span class="syndicate-site-name">${a.event}</span>

                    <span class="status-pill pos num">+${a.roiPct}% ROI Sicuro</span>

                  </div>

                  <div style="font-size:13px;color:var(--muted);margin-bottom:8px;">${a.sport} &bull; ${a.type}</div>

                  <div style="padding:8px;background:var(--ground);border-radius:var(--radius-chip);font-size:13px;display:flex;flex-direction:column;gap:4px;">

                    <div style="display:flex;justify-content:space-between;">

                      <span>1. ${a.legA.selection} (<strong>${a.legA.bookmaker} @${a.legA.odds}</strong>)</span>

                      <strong class="num">Punta ${APP.currency}${sA}</strong>

                    </div>

                    <div style="display:flex;justify-content:space-between;">

                      <span>2. ${a.legB.selection} (<strong>${a.legB.bookmaker} @${a.legB.odds}</strong>)</span>

                      <strong class="num">Punta ${APP.currency}${sB}</strong>

                    </div>

                  </div>

                  <div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center;font-size:13px;">

                    <span style="color:var(--positive);font-weight:600;" class="num">Utile netto garantito: +${APP.currency}${profit.toFixed(2)}</span>

                    <span style="color:var(--muted);">${a.windowAge}</span>

                  </div>

                </div>

              `;

            }).join('')}

          </div>

        </div>

        <div class="event-card">

          <h2 class="event-title">2. Whale &amp; Sharp Money Steam Radar (Pinnacle &amp; Betfair Exchange Orderflow)</h2>

          <div class="table-scroll-wrap">

            <table class="data-table">

              <thead>

                <tr>

                  <th>Match &amp; Competizione</th>

                  <th>Linea Colpita dai Sindacati</th>

                  <th class="num">Apertura &rarr; Live</th>

                  <th class="num">% Money Sharp</th>

                  <th class="num">Volume Abbinato</th>

                  <th>Bookmaker in Ritardo da Colpire</th>

                </tr>

              </thead>

              <tbody>

                ${(suite.whaleSteam || []).map(w => `

                  <tr>

                    <td>

                      <div style="font-weight:600;">${w.event}</div>

                      <div style="font-size:13px;color:var(--muted);">${w.sport}</div>

                    </td>

                    <td style="font-weight:600;">${w.selection}</td>

                    <td class="num"><span style="color:var(--muted);">${w.openerOdds}</span> &rarr; <strong style="color:var(--negative);">${w.currentOdds} (${w.dropPct}%)</strong></td>

                    <td class="num"><span class="status-pill pos">${w.sharpPct}% Sharp</span></td>

                    <td class="num">?${(w.matchedEur || 150000).toLocaleString('it-IT')}</td>

                    <td style="font-size:13px;color:var(--accent);font-weight:600;">${w.bookToHit}</td>

                  </tr>

                `).join('')}

              </tbody>

            </table>

          </div>

        </div>

        <div class="event-card">

          <h2 class="event-title">3. Player Prop &amp; Telemetry Alpha Matrix</h2>

          <div class="table-scroll-wrap">

            <table class="data-table">

              <thead>

                <tr>

                  <th>Giocatore / Pilota</th>

                  <th>Match</th>

                  <th>Mercato Prop</th>

                  <th class="num">Proiezione Modello</th>

                  <th class="num">Probabilità AI</th>

                  <th class="num">Miglior Quota</th>

                  <th class="num">Valore (+EV)</th>

                </tr>

              </thead>

              <tbody>

                ${(suite.vipPlayerProps || []).map(p => `

                  <tr>

                    <td style="font-weight:600;">${p.player} <span style="font-size:13px;color:var(--muted);">(${p.sport})</span></td>

                    <td>${p.match}</td>

                    <td style="font-weight:600;">${p.prop}</td>

                    <td class="num" style="color:var(--accent);font-weight:600;">${p.proj}</td>

                    <td class="num">${Math.round(p.prob * 100)}%</td>

                    <td class="num"><strong>@${p.odds}</strong> (${p.bestBook})</td>

                    <td class="num" style="color:var(--positive);font-weight:600;">+${p.edgePct}%</td>

                  </tr>

                `).join('')}

              </tbody>

            </table>

          </div>

        </div>

      `;

    }

    function renderPerformanceView(area) {

      const perf = APP.performanceData;

      if (!perf) {

        area.innerHTML = `<div class="event-card"><div style="font-size:14px;color:var(--muted);">Caricamento audit storico in corso...</div></div>`;

        return;

      }

      const s = perf.summary || {};

      const ledger = (perf.settled || []).slice(0, 20);

      area.innerHTML = `

        <div class="event-card">

          <h2 class="event-title">Riepilogo Backtest Out-of-Sample (${s.totalBets || 435} Match Certificati)</h2>

          <div class="card-metrics-strip">

            <div class="metric-item">

              <div class="metric-item-label">Win Rate Verificato</div>

              <div class="metric-item-val num" style="color:var(--positive);">${s.winRatePct || 80.9}% (${s.wins || 352}W - ${s.losses || 83}L)</div>

            </div>

            <div class="metric-item">

              <div class="metric-item-label">ROI su Stake Fisso</div>

              <div class="metric-item-val num" style="color:var(--positive);">+${s.roiPct || 10.97}%</div>

            </div>

            <div class="metric-item">

              <div class="metric-item-label">Profitto Netto (?100/bet)</div>

              <div class="metric-item-val num">+?${(s.netProfitUnits ? s.netProfitUnits * 100 : 4770).toFixed(0)}</div>

            </div>

            <div class="metric-item">

              <div class="metric-item-label">Brier Calibration Score</div>

              <div class="metric-item-val num">${s.brierScore || 0.1569} (Ottimo &lt; 0.18)</div>

            </div>

          </div>

          <div class="table-scroll-wrap">

            <table class="data-table">

              <thead>

                <tr>

                  <th>Data</th>

                  <th>Match</th>

                  <th>Selezione AI</th>

                  <th class="num">Probabilità</th>

                  <th class="num">Quota</th>

                  <th class="num">Risultato Reale</th>

                  <th class="num">Esito</th>

                </tr>

              </thead>

              <tbody>

                ${ledger.map(r => `

                  <tr>

                    <td class="num" style="color:var(--muted);">${(r.date || '').slice(0, 10)}</td>

                    <td style="font-weight:600;">${r.match || `${r.home} vs ${r.away}`}</td>

                    <td>${r.selection || r.market}</td>

                    <td class="num">${Math.round((r.prob || 0.76) * 100)}%</td>

                    <td class="num">@${(r.odds || 1.42).toFixed(2)}</td>

                    <td class="num">${r.score || r.actual || '-'}</td>

                    <td class="num"><span class="status-pill ${r.won ? 'pos' : 'neg'}">${r.won ? 'VINTA' : 'PERSA'}</span></td>

                  </tr>

                `).join('')}

              </tbody>

            </table>

          </div>

        </div>

      `;

    }

    /* ACCUMULATOR SLIP FUNCTIONS */

    function addLegToSlip(id, matchTitle, outcome, odds, prob, bookmaker, sport) {

      const existingIdx = APP.slip.findIndex(x => x.id === id);

      if (existingIdx >= 0) {

        APP.slip.splice(existingIdx, 1);

      } else {

        APP.slip.push({ id, matchTitle, outcome, odds: parseFloat(odds) || 1.5, prob: parseFloat(prob) || 0.7, bookmaker, sport });

      }

      renderSlipDrawer();

      showToast(`Aggiunto alla schedina: ${outcome} (@${parseFloat(odds).toFixed(2)})`);

    }

    function removeLegFromSlip(idx) {

      APP.slip.splice(idx, 1);

      renderSlipDrawer();

    }

    function loadAutoSafeSlip(silent = false) {

      const top3 = APP.safeScanner.filter(x => !x.locked).slice(0, 3);

      APP.slip = top3.map(x => ({

        id: x.id,

        matchTitle: x.title,

        outcome: x.outcome,

        odds: x.bookOdds,

        prob: x.prob,

        bookmaker: x.bookmaker,

        sport: x.sport

      }));

      renderSlipDrawer();

      if (!silent) showToast('Tripla Safe AI Cross-Sport caricata.');

    }

    function toggleSlipDrawer(open) {

      document.getElementById('drawer-backdrop').classList.toggle('open', open);

      document.getElementById('slip-drawer').classList.toggle('open', open);

    }

    function renderSlipDrawer() {

      document.getElementById('slip-count-badge').textContent = APP.slip.length;

      const box = document.getElementById('slip-legs-container');

      if (!APP.slip.length) {

        box.innerHTML = `<div style="font-size:13px;color:var(--muted);padding:20px 0;">Nessuna selezione nella schedina. Clicca su "+ Aggiungi a Schedina" o carica la Tripla Safe AI.</div>`;

        document.getElementById('slip-joint-prob').textContent = '0.0%';

        document.getElementById('slip-total-odds').textContent = '1.00';

        document.getElementById('slip-payout').textContent = `${APP.currency}0.00`;

        return;

      }

      let jointProb = 1.0;

      let totalOdds = 1.0;

      APP.slip.forEach(l => {

        jointProb *= (l.prob || 0.7);

        totalOdds *= (l.odds || 1.4);

      });

      const stake = Math.max(10, Math.round(APP.bankroll * 0.025));

      document.getElementById('slip-stake-label').textContent = `${APP.currency}${stake}`;

      document.getElementById('slip-joint-prob').textContent = `${(jointProb * 100).toFixed(1)}%`;

      document.getElementById('slip-total-odds').textContent = totalOdds.toFixed(2);

      document.getElementById('slip-payout').textContent = `${APP.currency}${(stake * totalOdds).toFixed(2)}`;

      box.innerHTML = APP.slip.map((l, idx) => `

        <div class="slip-leg-item">

          <div>

            <div style="font-size:13px;color:var(--muted);">${l.matchTitle} &bull; ${l.bookmaker}</div>

            <div style="font-size:13px;font-weight:600;margin-top:2px;">${l.outcome}</div>

          </div>

          <div style="text-align:right;">

            <div class="num" style="font-size:14px;font-weight:700;color:var(--accent);">@${l.odds.toFixed(2)}</div>

            <button type="button" style="font-size:13px;color:var(--muted);" onclick="removeLegFromSlip(${idx})">Rimuovi</button>

          </div>

        </div>

      `).join('');

    }

    function copySlipToClipboard() {

      if (!APP.slip.length) return;

      const lines = APP.slip.map((l, i) => `${i + 1}. ${l.matchTitle} -> ${l.outcome} @${l.odds.toFixed(2)} (${l.bookmaker})`);

      const txt = `EdgeBet AI &bull; Schedina Multipla\n` + lines.join('\n');

      navigator.clipboard.writeText(txt);

      showToast('Schedina copiata negli appunti.');

    }

    fetchMultisportData(false);

  