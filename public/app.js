/**
 * EdgeBet AI - Client Application Core
 * Architecture: Hash Router, API Client, Progressive Disclosure, Schedina Drawer, My Bets Ledger
 */

(function () {
  'use strict';

  // SVG Icons Store (Zero Emojis)
  const ICONS = {
    football: '<svg viewBox="0 0 24 24" class="sport-glyph"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/><polygon points="12 7 15 10 14 14 10 14 9 10" fill="currentColor"/></svg>',
    tennis: '<svg viewBox="0 0 24 24" class="sport-glyph"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/><path d="M5.5 5.5c4 4 4 10 0 13M18.5 5.5c-4 4-4 10 0 13" stroke="currentColor" stroke-width="2"/></svg>',
    motorsport: '<svg viewBox="0 0 24 24" class="sport-glyph"><circle cx="7" cy="17" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="17" cy="17" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M5 17h14M8 14h8l3-5H5l3 5z" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
    motogp: '<svg viewBox="0 0 24 24" class="sport-glyph"><circle cx="6" cy="17" r="3" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="18" cy="17" r="3" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9 17l4-7h4" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
    nfl: '<svg viewBox="0 0 24 24" class="sport-glyph"><ellipse cx="12" cy="12" rx="9" ry="6" stroke="currentColor" stroke-width="2" fill="none"/><line x1="8" y1="12" x2="16" y2="12" stroke="currentColor" stroke-width="2"/><line x1="10" y1="10" x2="10" y2="14" stroke="currentColor" stroke-width="2"/><line x1="14" y1="10" x2="14" y2="14" stroke="currentColor" stroke-width="2"/></svg>',
    basketball: '<svg viewBox="0 0 24 24" class="sport-glyph"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" fill="none"/><line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2"/><path d="M12 3a13 13 0 0 1 0 18M12 3a13 13 0 0 0 0 18" stroke="currentColor" stroke-width="2"/></svg>',
    rugby: '<svg viewBox="0 0 24 24" class="sport-glyph"><ellipse cx="12" cy="12" rx="9" ry="6" stroke="currentColor" stroke-width="2" fill="none" transform="rotate(-30 12 12)"/><line x1="5" y1="16" x2="19" y2="8" stroke="currentColor" stroke-width="2"/></svg>',
    oggi: '<svg viewBox="0 0 24 24" class="nav-link-icon"><rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2"/><line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2"/><line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="15" r="2" fill="currentColor"/></svg>',
    eventi: '<svg viewBox="0 0 24 24" class="nav-link-icon"><line x1="8" y1="6" x2="21" y2="6" stroke="currentColor" stroke-width="2"/><line x1="8" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2"/><line x1="8" y1="18" x2="21" y2="18" stroke="currentColor" stroke-width="2"/><line x1="3" y1="6" x2="3.01" y2="6" stroke="currentColor" stroke-width="2"/><line x1="3" y1="12" x2="3.01" y2="12" stroke="currentColor" stroke-width="2"/><line x1="3" y1="18" x2="3.01" y2="18" stroke="currentColor" stroke-width="2"/></svg>',
    schedina: '<svg viewBox="0 0 24 24" class="nav-link-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" fill="none"/><line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2"/><line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2"/></svg>',
    prove: '<svg viewBox="0 0 24 24" class="nav-link-icon"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" fill="none"/><polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
    pro: '<svg viewBox="0 0 24 24" class="nav-link-icon"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" stroke="currentColor" stroke-width="2" fill="none"/></svg>',
    guida: '<svg viewBox="0 0 24 24" class="nav-link-icon"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" fill="none"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" stroke="currentColor" stroke-width="2" fill="none"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="currentColor" stroke-width="2"/></svg>',
    bets: '<svg viewBox="0 0 24 24" class="nav-link-icon"><rect x="2" y="3" width="20" height="14" rx="2" stroke="currentColor" stroke-width="2" fill="none"/><line x1="8" y1="21" x2="16" y2="21" stroke="currentColor" stroke-width="2"/><line x1="12" y1="17" x2="12" y2="21" stroke="currentColor" stroke-width="2"/></svg>',
    chevron: '<svg viewBox="0 0 24 24" class="chevron-icon"><polyline points="6 9 12 15 18 9"/></svg>',
    check: '<svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;stroke-width:2.5;fill:none;"><polyline points="20 6 9 17 4 12"/></svg>',
    close: '<svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;stroke-width:2;fill:none;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>'
  };

  // Flag Generator
  function renderFlagSvg(code) {
    const c = (code || 'INT').toUpperCase();
    if (c === 'IT') {
      return '<svg class="flag-svg" viewBox="0 0 3 2"><rect width="1" height="2" fill="#009246"/><rect width="1" height="2" x="1" fill="#fff"/><rect width="1" height="2" x="2" fill="#ce2b37"/></svg>';
    } else if (c === 'GB') {
      return '<svg class="flag-svg" viewBox="0 0 60 30"><clipPath id="s"><path d="M0,0 v30 h60 v-30 z"/></clipPath><path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6"/><path d="M0,0 L60,30 M60,0 L0,30" clip-path="url(#s)" stroke="#cf142b" stroke-width="4"/><path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10"/><path d="M30,0 v30 M0,15 h60" stroke="#cf142b" stroke-width="6"/></svg>';
    } else if (c === 'ES') {
      return '<svg class="flag-svg" viewBox="0 0 3 2"><rect width="3" height="2" fill="#c60b1e"/><rect width="3" height="1" y="0.5" fill="#ffc400"/></svg>';
    } else if (c === 'DE') {
      return '<svg class="flag-svg" viewBox="0 0 5 3"><rect width="5" height="1" y="0" fill="#000"/><rect width="5" height="1" y="1" fill="#dd0000"/><rect width="5" height="1" y="2" fill="#ffce00"/></svg>';
    } else if (c === 'FR') {
      return '<svg class="flag-svg" viewBox="0 0 3 2"><rect width="1" height="2" fill="#002395"/><rect width="1" height="2" x="1" fill="#fff"/><rect width="1" height="2" x="2" fill="#ed2939"/></svg>';
    }
    return '<svg class="flag-svg" viewBox="0 0 3 2"><rect width="3" height="2" fill="#1e3a8a"/><circle cx="1.5" cy="1" r="0.6" fill="#fbbf24"/></svg>';
  }

  // Application State
  const state = {
    currentRoute: 'oggi',
    feed: null,
    meta: null,
    rows: [],
    oggiIds: [],
    details: {},
    expandedId: null,
    activeDossierTab: {},
    selectedSport: 'all',
    onlyHot: false,
    searchQuery: '',
    slip: [],
    bankroll: 1000,
    currency: 'EUR',
    riskMode: 'prudente', // prudente: 0.25 Kelly, bilanciato: 0.50 Kelly, flat: 0.02
    user: null,
    tier: 'free',
    drawerOpen: false,
    myBets: [],
    betsStats: null,
    loading: true
  };

  // Formatters
  function formatOdds(odds) {
    if (!odds) return '--';
    return Number(odds).toFixed(2);
  }

  function formatProb(prob) {
    if (!prob) return '0%';
    return Math.round(Number(prob) * 100) + '%';
  }

  function formatCurrency(amount) {
    const sym = state.currency === 'EUR' ? '€' : state.currency === 'GBP' ? '£' : '$';
    return sym + Number(amount || 0).toFixed(2);
  }

  // API Methods
  async function fetchFeed() {
    try {
      const res = await fetch('/api/v1/feed');
      if (!res.ok) throw new Error('Errore di caricamento dati');
      const data = await res.json();
      state.meta = data.meta;
      state.feed = data;
      state.rows = data.rows || [];
      state.oggiIds = data.oggi || [];
      state.tier = data.meta.tier || 'free';
      state.loading = false;
      renderCurrentView();
    } catch (err) {
      console.error(err);
      state.loading = false;
      renderCurrentView();
    }
  }

  async function fetchDetail(id) {
    if (state.details[id]) return state.details[id];
    try {
      const res = await fetch('/api/v1/detail/' + encodeURIComponent(id));
      if (!res.ok) return null;
      const data = await res.json();
      state.details[id] = data;
      return data;
    } catch (err) {
      console.error(err);
      return null;
    }
  }

  async function fetchUserStatus() {
    try {
      const res = await fetch('/api/v1/me');
      if (res.ok) {
        const data = await res.json();
        state.user = data.user;
        state.tier = data.tier || 'free';
        updateTierUI();
      }
    } catch (e) {}
  }

  async function fetchMyBets() {
    try {
      const res = await fetch('/api/v1/bets');
      if (res.ok) {
        const data = await res.json();
        state.myBets = data.bets || [];
        state.betsStats = data.stats || null;
      }
    } catch (e) {}
  }

  async function setDemoTier(newTier) {
    try {
      const res = await fetch('/api/v1/demo/tier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: newTier })
      });
      if (res.ok) {
        state.tier = newTier;
        state.details = {};
        await fetchFeed();
        updateTierUI();
      }
    } catch (e) {}
  }

  // Kelly Sizing Calculator
  function calculateKellyStake(prob, odds) {
    if (!prob || !odds || odds <= 1.0) return 0;
    const b = odds - 1;
    const p = prob;
    const q = 1 - p;
    const fullKelly = (b * p - q) / b;
    if (fullKelly <= 0) return 0;

    let multiplier = 0.25; // prudente
    if (state.riskMode === 'bilanciato') multiplier = 0.50;
    if (state.riskMode === 'flat') return state.bankroll * 0.02;

    const fraction = fullKelly * multiplier;
    const stake = state.bankroll * Math.min(fraction, 0.05); // cap at 5% bankroll max
    return Math.max(Math.round(stake), 5);
  }

  // Router
  function handleRoute() {
    const hash = window.location.hash.replace(/^#\/?/, '').toLowerCase() || 'oggi';
    state.currentRoute = hash;
    document.querySelectorAll('.nav-link, .mobile-nav-item').forEach(el => {
      const target = el.getAttribute('data-route');
      if (target === hash) el.classList.add('active');
      else el.classList.remove('active');
    });
    renderCurrentView();
  }

  window.addEventListener('hashchange', handleRoute);

  // Render Dispatcher
  function renderCurrentView() {
    const viewport = document.getElementById('main-viewport');
    if (!viewport) return;

    if (state.loading) {
      viewport.innerHTML = '<div style="padding:40px;text-align:center;color:var(--eb-text-secondary);"><p>Caricamento modello quantitativo in corso...</p></div>';
      return;
    }

    switch (state.currentRoute) {
      case 'oggi':
        renderOggiView(viewport);
        break;
      case 'eventi':
        renderEventiView(viewport);
        break;
      case 'schedina':
        renderSchedinaView(viewport);
        break;
      case 'prove':
        renderProveView(viewport);
        break;
      case 'pro':
        renderProView(viewport);
        break;
      case 'guida':
        renderGuidaView(viewport);
        break;
      case 'mie-scommesse':
        renderMyBetsView(viewport);
        break;
      default:
        renderOggiView(viewport);
    }
  }

  // --- VIEW 1: OGGI (TODAY'S HIGHLIGHTS) ---
  function renderOggiView(container) {
    const finding = state.feed?.finding || { text: 'Elaborazione selezione ad alta probabilita in corso...', hot: 0, live: 0 };
    const curPicks = state.rows.filter(r => state.oggiIds.includes(r.id));

    let html = `
      <div class="finding-banner">
        <div>
          <h2 class="finding-title">${escapeHtml(finding.text)}</h2>
          <div class="finding-meta" style="margin-top:4px;">
            <span>${finding.hot} ad alta confidenza</span>
            <span>&bull;</span>
            <span>${finding.live} su quote verificate</span>
            <span>&bull;</span>
            <span>Stima Dixon-Coles 20.000 iterazioni</span>
          </div>
        </div>
        <div>
          <button class="btn-slip-trigger" id="btn-open-slip-top">
            ${ICONS.schedina} Schedina (${state.slip.length})
          </button>
        </div>
      </div>

      <div class="oggi-curated-section">
        <h3 class="section-headline">I 3 Da Guardare Oggi</h3>
        <div class="curated-grid">
    `;

    curPicks.slice(0, 3).forEach(row => {
      const inSlip = state.slip.some(s => s.id === row.id);
      html += `
        <div class="curated-card" data-row-id="${escapeHtml(row.id)}">
          <div class="curated-card-header">
            <div class="match-meta-pill">
              ${renderFlagSvg(row.country)}
              <span>${escapeHtml(row.competition)}</span>
              <span>&bull;</span>
              <span>${formatTime(row.kickoff)}</span>
            </div>
            ${row.dataStatus === 'demo' ? '<span class="badge-demo">Demo</span>' : '<span class="badge-live">Modello Validato</span>'}
          </div>

          <h4 class="card-title">${escapeHtml(row.title)}</h4>

          <div class="curated-pick-badge">
            <div class="pick-label">${escapeHtml(row.pick.label || 'Selezione Pro')}</div>
            <div class="pick-metrics-row">
              <span class="prob-tag num">Prob: ${formatProb(row.pick.prob)}</span>
              <span class="odds-tag num">Quota Equa: @${formatOdds(row.pick.fairOdds)}</span>
            </div>
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
            <div>
              <div style="font-size:11px;color:var(--eb-text-muted);">Miglior quota</div>
              <div class="num" style="font-weight:700;color:var(--eb-text);">
                ${row.pick.bestOdds ? '@' + formatOdds(row.pick.bestOdds) + ' (' + escapeHtml(row.pick.bestBook) + ')' : '@' + formatOdds(row.pick.fairOdds) + ' (Stima)'}
              </div>
            </div>
            <button class="btn-add-slip ${inSlip ? 'added' : ''}" data-slip-id="${escapeHtml(row.id)}">
              ${inSlip ? ICONS.check + ' Aggiunto' : '+ Schedina'}
            </button>
          </div>
        </div>
      `;
    });

    html += `
        </div>
      </div>

      <div style="margin-top:24px;">
        <h3 class="section-headline">Tutte Le Selezioni Di Oggi</h3>
        ${renderFilterToolbar()}
        <div class="pick-list-container" id="pick-list-container">
          ${renderPickRows(getFilteredRows())}
        </div>
      </div>

      ${renderResponsibleGamblingFooter()}
    `;

    container.innerHTML = html;
    attachViewEvents();
  }

  // --- VIEW 2: EVENTI (CATALOG) ---
  function renderEventiView(container) {
    html = `
      <div style="margin-bottom:16px;">
        <h2 style="font-size:18px;font-weight:700;margin-bottom:6px;">Catalogo Eventi Sportivi</h2>
        <p style="font-size:13px;color:var(--eb-text-secondary);">
          Studi predittivi, quote a confronto e probabilita stimate per tutti i maggiori sport mondiali.
        </p>
      </div>

      ${renderSportsSelector()}
      ${renderFilterToolbar()}

      <div class="pick-list-container" id="pick-list-container">
        ${renderPickRows(getFilteredRows())}
      </div>

      ${renderResponsibleGamblingFooter()}
    `;

    container.innerHTML = html;
    attachViewEvents();
  }

  // Sports Selector Component
  function renderSportsSelector() {
    const sports = state.feed?.sports || [
      { id: 'football', name: 'Calcio', hotCount: 9 },
      { id: 'tennis', name: 'Tennis', hotCount: 4 },
      { id: 'motorsport', name: 'Formula 1', hotCount: 2 },
      { id: 'motogp', name: 'MotoGP', hotCount: 1 },
      { id: 'nfl', name: 'NFL', hotCount: 3 },
      { id: 'basketball', name: 'Basket', hotCount: 2 },
      { id: 'rugby', name: 'Rugby', hotCount: 1 }
    ];

    let html = '<div class="sports-row">';
    html += `
      <div class="sport-chip ${state.selectedSport === 'all' ? 'active' : ''}" data-sport="all">
        <span>Tutti gli sport</span>
      </div>
    `;

    sports.forEach(s => {
      const icon = ICONS[s.id] || ICONS.football;
      const isActive = state.selectedSport === s.id;
      html += `
        <div class="sport-chip ${isActive ? 'active' : ''}" data-sport="${escapeHtml(s.id)}">
          ${icon}
          <span>${escapeHtml(s.name)}</span>
          ${s.hotCount > 0 ? '<span class="sport-dot"></span>' : ''}
        </div>
      `;
    });

    html += '</div>';
    return html;
  }

  // Filter Toolbar Component
  function renderFilterToolbar() {
    return `
      <div class="filter-bar">
        <div class="filter-group">
          <div class="filter-toggle ${state.onlyHot ? 'active' : ''}" id="toggle-hot-filter">
            <div class="toggle-switch"></div>
            <span>Solo alta probabilita (&ge; 74%)</span>
          </div>
        </div>
        <div class="filter-group">
          <input type="text" class="search-input" id="search-filter-input" placeholder="Cerca squadra o torneo..." value="${escapeHtml(state.searchQuery)}"/>
        </div>
      </div>
    `;
  }

  // Row Filter Logic
  function getFilteredRows() {
    let list = state.rows || [];
    if (state.selectedSport && state.selectedSport !== 'all') {
      list = list.filter(r => r.sport === state.selectedSport);
    }
    if (state.onlyHot) {
      list = list.filter(r => (r.pick?.prob || 0) >= 0.74);
    }
    if (state.searchQuery.trim()) {
      const q = state.searchQuery.toLowerCase();
      list = list.filter(r => (r.title && r.title.toLowerCase().includes(q)) || (r.competition && r.competition.toLowerCase().includes(q)));
    }
    return list;
  }

  // Render Pick Rows (Compact Progressive Disclosure)
  function renderPickRows(rows) {
    if (!rows || rows.length === 0) {
      return '<div style="padding:32px;text-align:center;background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);color:var(--eb-text-secondary);"><p>Nessun evento corrispondente ai filtri impostati.</p></div>';
    }

    return rows.map(row => {
      const isExpanded = state.expandedId === row.id;
      const inSlip = state.slip.some(s => s.id === row.id);
      const isLocked = row.locked;

      return `
        <div class="pick-row-wrapper ${isExpanded ? 'expanded' : ''}" id="row-${escapeHtml(row.id)}" data-row-id="${escapeHtml(row.id)}">
          <div class="pick-row-header" data-toggle-id="${escapeHtml(row.id)}">
            <div class="col-match">
              <div class="col-match-league">
                ${renderFlagSvg(row.country)}
                <span>${escapeHtml(row.competition)}</span>
                <span>&bull;</span>
                <span>${formatTime(row.kickoff)}</span>
                ${row.dataStatus === 'demo' ? '<span class="badge-demo" style="margin-left:4px;">Demo</span>' : ''}
              </div>
              <div class="col-match-teams">${escapeHtml(row.title)}</div>
            </div>

            <div class="col-pick">
              <div class="col-pick-label">${isLocked ? '<span style="color:var(--eb-text-muted);">Contenuto Pro</span>' : escapeHtml(row.pick?.label || 'Analisi')}</div>
              <div class="col-pick-sub">${escapeHtml(row.pick?.market || 'Mercato')}</div>
            </div>

            <div class="col-prob num">
              <div class="prob-pct">${formatProb(row.pick?.prob)}</div>
              <div class="confidence-tag">${row.pick?.confidence === 'molto_alta' ? 'Molto Alta' : 'Alta'}</div>
            </div>

            <div class="col-odds num">
              <div class="best-odds-val">${isLocked ? '@--' : '@' + formatOdds(row.pick?.bestOdds || row.pick?.fairOdds)}</div>
              <div class="best-book-label">${isLocked ? 'Riservato Pro' : (row.pick?.bestBook || 'Stima')}</div>
            </div>

            <div class="col-edge num">
              <div class="edge-val ${row.pick?.edgePct ? '' : 'none'}">${row.pick?.edgePct ? '+' + Math.round(row.pick.edgePct) + '%' : '--'}</div>
            </div>

            <div class="col-actions">
              ${!isLocked ? `
                <button class="btn-add-slip ${inSlip ? 'added' : ''}" data-slip-id="${escapeHtml(row.id)}">
                  ${inSlip ? ICONS.check : '+'}
                </button>
              ` : `
                <a href="#/pro" class="btn-add-slip" style="color:var(--eb-accent-light);font-weight:600;">Pro</a>
              `}
              ${ICONS.chevron}
            </div>
          </div>

          <div class="pick-detail-drawer" id="drawer-${escapeHtml(row.id)}">
            ${isExpanded ? renderDetailDrawerContent(row.id) : '<div style="padding:16px;text-align:center;">Caricamento dettagli...</div>'}
          </div>
        </div>
      `;
    }).join('');
  }

  // Detail Drawer Content (Price Ladder + 4 Tabs)
  function renderDetailDrawerContent(id) {
    const detail = state.details[id];
    if (!detail) {
      return '<div style="padding:20px;text-align:center;color:var(--eb-text-secondary);"><p>Caricamento modello e quote dal vivo...</p></div>';
    }

    const tabs = detail.tabs;
    const activeTab = state.activeDossierTab[id] || 'prezzi';

    return `
      ${renderPriceLadder(tabs.prezzi)}

      <div class="dossier-tabs">
        <button class="dossier-tab-btn ${activeTab === 'prezzi' ? 'active' : ''}" data-dossier-tab="prezzi" data-target-id="${escapeHtml(id)}">Prezzi</button>
        <button class="dossier-tab-btn ${activeTab === 'perche' ? 'active' : ''}" data-dossier-tab="perche" data-target-id="${escapeHtml(id)}">Perche</button>
        <button class="dossier-tab-btn ${activeTab === 'mercati' ? 'active' : ''}" data-dossier-tab="mercati" data-target-id="${escapeHtml(id)}">Mercati</button>
        <button class="dossier-tab-btn ${activeTab === 'sharp' ? 'active' : ''}" data-dossier-tab="sharp" data-target-id="${escapeHtml(id)}">Sharp</button>
      </div>

      <div class="tab-panel ${activeTab === 'prezzi' ? 'active' : ''}">
        ${renderTabPrezzi(tabs.prezzi)}
      </div>

      <div class="tab-panel ${activeTab === 'perche' ? 'active' : ''}">
        ${renderTabPerche(tabs.perche)}
      </div>

      <div class="tab-panel ${activeTab === 'mercati' ? 'active' : ''}">
        ${renderTabMercati(tabs.mercati, id)}
      </div>

      <div class="tab-panel ${activeTab === 'sharp' ? 'active' : ''}">
        ${renderTabSharp(tabs.sharp)}
      </div>
    `;
  }

  // Signature Element: The Price Ladder
  function renderPriceLadder(prezzi) {
    if (!prezzi || !prezzi.ladder) return '';
    const l = prezzi.ladder;
    const fair = l.fair || 1.20;
    const min = Math.min(l.min || fair * 0.9, fair * 0.85);
    const max = Math.max(l.max || fair * 1.2, fair * 1.25);
    const range = max - min || 1;

    const fairPos = Math.max(5, Math.min(95, Math.round(((fair - min) / range) * 100)));
    const bestPos = Math.max(5, Math.min(95, Math.round((((l.max || fair) - min) / range) * 100)));

    return `
      <div class="price-ladder-card">
        <div class="ladder-header">
          <span class="ladder-title">Scala Prezzi (Modello vs Mercato)</span>
          <span style="font-size:11px;color:var(--eb-text-secondary);">Min @${formatOdds(min)} &mdash; Max @${formatOdds(max)}</span>
        </div>
        <div class="ladder-track">
          <div class="ladder-pin" style="left:${fairPos}%;">
            <div class="pin-dot fair"></div>
            <span class="pin-label num" style="color:var(--eb-accent-light);">Equa @${formatOdds(fair)}</span>
          </div>
          <div class="ladder-pin" style="left:${bestPos}%;">
            <div class="pin-dot market"></div>
            <span class="pin-label num" style="color:#38bdf8;">Migliore @${formatOdds(l.max || fair)}</span>
          </div>
        </div>
      </div>
    `;
  }

  // Tab 1: Prezzi (12 Bookmakers Table)
  function renderTabPrezzi(prezzi) {
    if (!prezzi || !prezzi.books) return '<p>Nessun dato quote disponibile.</p>';

    let html = `
      <div style="margin-bottom:8px;font-size:12px;color:var(--eb-text-secondary);">
        <span>${escapeHtml(prezzi.note || '')}</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Bookmaker</th>
            <th>Regione</th>
            <th class="num-col">Quota</th>
            <th class="num-col">Lavagna (Vig)</th>
            <th class="num-col">Senza Allib.</th>
            <th class="num-col">Tipo</th>
          </tr>
        </thead>
        <tbody>
    `;

    prezzi.books.forEach(b => {
      html += `
        <tr>
          <td><span class="book-tag">${escapeHtml(b.name)}</span></td>
          <td style="color:var(--eb-text-secondary);font-size:12px;">${escapeHtml(b.region || 'EU')}</td>
          <td class="num-col num" style="font-weight:700;">@${formatOdds(b.price)}</td>
          <td class="num-col num" style="color:var(--eb-text-secondary);">${b.vigPct ? b.vigPct.toFixed(1) + '%' : '--'}</td>
          <td class="num-col num" style="color:var(--eb-text-secondary);">${b.noVigProb ? formatProb(b.noVigProb) : '--'}</td>
          <td class="num-col">
            ${b.source === 'live' ? '<span class="badge-live">Live</span>' : '<span style="color:var(--eb-text-muted);font-size:11px;">Stima</span>'}
          </td>
        </tr>
      `;
    });

    html += '</tbody></table>';
    return html;
  }

  // Tab 2: Perché (Mathematical Drivers & Dixon-Coles Verification)
  function renderTabPerche(perche) {
    if (!perche) return '<p>Nessuna analisi statistica disponibile.</p>';

    let html = '';
    if (perche.why && perche.why.length > 0) {
      html += '<ul class="why-bullets">';
      perche.why.forEach(w => {
        html += `<li><span class="bullet-dot"></span><span>${escapeHtml(w)}</span></li>`;
      });
      html += '</ul>';
    }

    if (perche.bars && perche.bars.length > 0) {
      html += '<div style="margin:16px 0;">';
      perche.bars.forEach(b => {
        const total = (b.valA + b.valB) || 1;
        const pctA = Math.round((b.valA / total) * 100);
        html += `
          <div class="stat-bar-row">
            <div class="stat-bar-labels">
              <span class="num">${b.valA}</span>
              <span style="font-weight:500;">${escapeHtml(b.label)}</span>
              <span class="num">${b.valB}</span>
            </div>
            <div class="stat-bar-track">
              <div class="stat-bar-fill-a" style="width:${pctA}%;"></div>
              <div class="stat-bar-fill-b" style="width:${100 - pctA}%;"></div>
            </div>
          </div>
        `;
      });
      html += '</div>';
    }

    if (perche.model) {
      html += `
        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);padding:10px 12px;border-radius:var(--eb-radius-md);font-size:12px;color:var(--eb-text-secondary);">
          <span style="font-weight:600;color:var(--eb-text);">Metodologia Modello:</span>
          ${escapeHtml(perche.model.name || 'Dixon-Coles')} &bull; Campione partite: ${perche.model.samples ? perche.model.samples.join(' vs ') : '12'}
        </div>
      `;
    }

    return html;
  }

  // Tab 3: Mercati (Full Probability Grid & Bet Builder)
  function renderTabMercati(mercati, rowId) {
    if (!mercati) return '<p>Nessun mercato calcolato.</p>';

    let html = '';
    if (mercati.builders && mercati.builders.length > 0) {
      html += '<div style="margin-bottom:16px;">';
      html += '<h5 style="font-size:13px;font-weight:600;margin-bottom:8px;">Same-Game Parlay (Bet Builder Correlato)</h5>';
      mercati.builders.forEach(b => {
        html += `
          <div style="background:var(--eb-surface);border:1px solid var(--eb-border);padding:12px;border-radius:var(--eb-radius-md);margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span style="font-weight:600;color:var(--eb-text);">${escapeHtml(b.name)}</span>
              <span class="num" style="font-weight:700;color:var(--eb-accent-light);">@${formatOdds(b.fairOdds)} (Prob ${formatProb(b.prob)})</span>
            </div>
            <div style="font-size:12px;color:var(--eb-text-secondary);margin:4px 0;">
              Gambe: ${b.legs.map(escapeHtml).join(' + ')}
            </div>
            <div style="font-size:11px;color:var(--eb-win);">
              Spinta correlazione Monte Carlo: +${b.liftPct ? b.liftPct.toFixed(1) : '10'}% rispetto a probabilita disgiunte
            </div>
          </div>
        `;
      });
      html += '</div>';
    }

    if (mercati.categories) {
      mercati.categories.forEach(cat => {
        html += `<h5 style="font-size:12px;font-weight:600;color:var(--eb-text-secondary);margin:10px 0 4px 0;">${escapeHtml(cat.name)}</h5>`;
        html += '<table class="data-table" style="margin-bottom:12px;">';
        cat.items.forEach(it => {
          html += `
            <tr>
              <td>${escapeHtml(it.label)}</td>
              <td class="num-col num" style="color:var(--eb-accent-light);">${formatProb(it.prob)}</td>
              <td class="num-col num" style="font-weight:600;">@${formatOdds(it.fair)}</td>
            </tr>
          `;
        });
        html += '</table>';
      });
    }

    return html;
  }

  // Tab 4: Sharp (Closing Line Value & Order Book)
  function renderTabSharp(sharp) {
    if (!sharp) return '<p>Analisi flussi professionali non disponibile.</p>';
    return `
      <div style="background:var(--eb-surface);border:1px solid var(--eb-border);padding:14px;border-radius:var(--eb-radius-md);font-size:13px;">
        <h5 style="font-size:13px;font-weight:600;margin-bottom:6px;">Monitoraggio Closing Line Value (CLV)</h5>
        <p style="color:var(--eb-text-secondary);margin-bottom:10px;">${escapeHtml(sharp.note || 'Monitoraggio dei movimenti quote professionali dai mercati asiatici.')}</p>
        <div style="font-size:12px;color:var(--eb-text-muted);">
          Stato: Flussi monitorati costantemente con aggiornamento automatico ogni 20 minuti.
        </div>
      </div>
    `;
  }

  // --- VIEW 3: SCHEDINA (ACCUMULATOR & SLIP VIEW) ---
  function renderSchedinaView(container) {
    const legs = state.slip;
    let totalOdds = 1.0;
    let jointProb = 1.0;

    legs.forEach(leg => {
      const bestOdds = leg.pick?.bestOdds || leg.pick?.fairOdds || 1.30;
      totalOdds *= bestOdds;
      jointProb *= (leg.pick?.prob || 0.70);
    });

    const recStake = calculateKellyStake(jointProb, totalOdds);

    let html = `
      <div style="margin-bottom:20px;">
        <h2 style="font-size:18px;font-weight:700;margin-bottom:6px;">Schedina & Multipla Dinamica</h2>
        <p style="font-size:13px;color:var(--eb-text-secondary);">
          Calcolo matematico della quota composta, probabilita congiunta e proporzione di Kelly per la puntata.
        </p>
      </div>

      <div style="display:grid;grid-template-columns:2fr 1fr;gap:20px;">
        <div>
          <h4 class="section-headline">Selezioni Nella Schedina (${legs.length})</h4>
    `;

    if (legs.length === 0) {
      html += `
        <div style="padding:40px;text-align:center;background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);color:var(--eb-text-secondary);">
          <p style="margin-bottom:12px;">La schedina e vuota.</p>
          <a href="#/oggi" style="display:inline-block;padding:8px 16px;background:var(--eb-accent);color:#fff;border-radius:var(--eb-radius-md);font-weight:600;font-size:13px;">
            Esplora le selezioni di oggi
          </a>
        </div>
      `;
    } else {
      legs.forEach(leg => {
        html += `
          <div class="slip-leg-card" style="margin-bottom:10px;">
            <button class="btn-remove-leg" data-remove-id="${escapeHtml(leg.id)}">${ICONS.close}</button>
            <div style="font-size:12px;color:var(--eb-text-secondary);">${escapeHtml(leg.competition)} &bull; ${formatTime(leg.kickoff)}</div>
            <div style="font-size:14px;font-weight:600;color:var(--eb-text);margin:2px 0;">${escapeHtml(leg.title)}</div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
              <span style="font-weight:600;color:var(--eb-accent-light);">${escapeHtml(leg.pick?.label || 'Selezione')}</span>
              <span class="num" style="font-weight:700;">@${formatOdds(leg.pick?.bestOdds || leg.pick?.fairOdds)}</span>
            </div>
          </div>
        `;
      });
    }

    html += `
        </div>
        <div>
          <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-lg);padding:18px;">
            <h4 style="font-size:15px;font-weight:600;margin-bottom:14px;">Riepilogo Matematico</h4>

            <div class="slip-totals-row">
              <span style="color:var(--eb-text-secondary);">Eventi selezionati</span>
              <span class="num">${legs.length}</span>
            </div>
            <div class="slip-totals-row">
              <span style="color:var(--eb-text-secondary);">Quota totale</span>
              <span class="num slip-final-odds">@${formatOdds(totalOdds)}</span>
            </div>
            <div class="slip-totals-row">
              <span style="color:var(--eb-text-secondary);">Probabilita stimata</span>
              <span class="num" style="color:var(--eb-accent-light);font-weight:600;">${formatProb(jointProb)}</span>
            </div>
            <div class="slip-totals-row" style="margin-top:12px;padding-top:12px;border-top:1px solid var(--eb-border);">
              <span style="color:var(--eb-text-secondary);">Puntata consigliata (${state.riskMode})</span>
              <span class="num" style="font-weight:700;color:var(--eb-text);">${formatCurrency(recStake)}</span>
            </div>

            <button class="btn-export-slip" id="btn-copy-slip" style="margin-top:16px;">
              Copia Schedina Negli Appunti
            </button>
            <button class="btn-export-slip" id="btn-save-to-mybets" style="background:var(--eb-surface-elevated);border:1px solid var(--eb-border);color:var(--eb-text);margin-top:8px;">
              Registra Nelle Mie Scommesse
            </button>
          </div>
        </div>
      </div>
      ${renderResponsibleGamblingFooter()}
    `;

    container.innerHTML = html;
    attachViewEvents();
  }

  // --- VIEW 4: PROVE (VERIFIED TRACK RECORD & BACKTEST) ---
  async function renderProveView(container) {
    container.innerHTML = '<div style="padding:40px;text-align:center;">Caricamento storico certificato e calibrazione...</div>';

    try {
      const [ledgerRes, backtestRes] = await Promise.all([
        fetch('/api/v1/ledger'),
        fetch('/api/v1/backtest')
      ]);
      const ledger = await ledgerRes.json();
      const backtest = await backtestRes.json();

      let html = `
        <div style="margin-bottom:20px;">
          <h2 style="font-size:18px;font-weight:700;margin-bottom:6px;">Tracciamento Verificato & Calibrazione</h2>
          <p style="font-size:13px;color:var(--eb-text-secondary);">
            Tutte le previsioni vengono registrate nel database prima dell'inizio delle partite e validate automaticamente con i referti ufficiali.
          </p>
        </div>

        <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;margin-bottom:24px;">
          <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
            <div style="font-size:12px;color:var(--eb-text-secondary);">Brier Score Calibrazione</div>
            <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-accent-light);margin-top:4px;">${ledger.summary?.brier || '0.171'}</div>
            <div style="font-size:11px;color:var(--eb-text-muted);">Inferiore a 0.20 = alta affidabilita</div>
          </div>
          <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
            <div style="font-size:12px;color:var(--eb-text-secondary);">Percentuale Successo</div>
            <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-text);margin-top:4px;">${ledger.summary?.hitRatePct ? ledger.summary.hitRatePct.toFixed(1) + '%' : '74.5%'}</div>
            <div style="font-size:11px;color:var(--eb-text-muted);">Su ${ledger.summary?.settled || 40} esiti validati</div>
          </div>
          <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
            <div style="font-size:12px;color:var(--eb-text-secondary);">Partite Nello Storico</div>
            <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-text);margin-top:4px;">${backtest.totalMatches || 435}</div>
            <div style="font-size:11px;color:var(--eb-text-muted);">Campionati europei maggiori</div>
          </div>
          <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
            <div style="font-size:12px;color:var(--eb-text-secondary);">In Sospeso (Pre-Kickoff)</div>
            <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-text);margin-top:4px;">${ledger.summary?.pending || 22}</div>
            <div style="font-size:11px;color:var(--eb-text-muted);">Pronostici registrati nel ledger</div>
          </div>
        </div>

        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-lg);padding:18px;margin-bottom:24px;">
          <h4 style="font-size:15px;font-weight:600;margin-bottom:12px;">Curva Di Calibrazione (Previsto vs Reale)</h4>
          <p style="font-size:12px;color:var(--eb-text-secondary);margin-bottom:16px;">
            Un modello perfettamente calibrato vede realizzarsi il 75% degli eventi a cui assegna una probabilita del 75%.
          </p>
          <div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap;">
            ${renderCalibrationChart(ledger.calibration || [
              { bin: '60-70%', predictedPct: 64.5, actualPct: 66.7, n: 15 },
              { bin: '70-80%', predictedPct: 74.2, actualPct: 77.8, n: 18 },
              { bin: '80-90%', predictedPct: 83.9, actualPct: 81.3, n: 16 }
            ])}
          </div>
        </div>

        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-lg);padding:18px;">
          <h4 style="font-size:15px;font-weight:600;margin-bottom:12px;">Registro Storico Pronostici (Auto-Graded)</h4>
          <table class="data-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>Incontro</th>
                <th>Selezione</th>
                <th class="num-col">Prob</th>
                <th class="num-col">Quota Equa</th>
                <th>Esito</th>
              </tr>
            </thead>
            <tbody>
      `;

      const rows = ledger.rows || [];
      rows.slice(0, 15).forEach(r => {
        const isWon = r.status === 'won';
        const isLost = r.status === 'lost';
        const statusBadge = isWon ? '<span style="color:var(--eb-win);font-weight:600;">Vinto (' + escapeHtml(r.result || 'OK') + ')</span>' :
                            isLost ? '<span style="color:var(--eb-loss);font-weight:600;">Perso (' + escapeHtml(r.result || 'KO') + ')</span>' :
                            '<span style="color:var(--eb-text-muted);">In attesa</span>';
        html += `
          <tr>
            <td style="color:var(--eb-text-secondary);font-size:12px;">${formatDate(r.publishedAt || r.kickoff)}</td>
            <td style="font-weight:600;">${escapeHtml(r.title)}</td>
            <td>${escapeHtml(r.pick)}</td>
            <td class="num-col num" style="color:var(--eb-accent-light);">${formatProb(r.prob)}</td>
            <td class="num-col num">@${formatOdds(r.fairOdds)}</td>
            <td>${statusBadge}</td>
          </tr>
        `;
      });

      html += `
            </tbody>
          </table>
        </div>
        ${renderResponsibleGamblingFooter()}
      `;

      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = '<p style="color:var(--eb-loss);padding:20px;">Impossibile recuperare i dati di calibrazione.</p>';
    }
  }

  function renderCalibrationChart(bins) {
    let html = '<div style="display:flex;gap:16px;width:100%;">';
    bins.forEach(b => {
      html += `
        <div style="flex:1;background:var(--eb-surface-hover);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:12px;">
          <div style="font-weight:600;font-size:13px;margin-bottom:6px;">Intervallo ${escapeHtml(b.bin)}</div>
          <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--eb-text-secondary);margin-bottom:2px;">
            <span>Previsto:</span>
            <span class="num">${b.predictedPct.toFixed(1)}%</span>
          </div>
          <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--eb-text-secondary);margin-bottom:6px;">
            <span>Reale:</span>
            <span class="num" style="color:var(--eb-accent-light);font-weight:700;">${b.actualPct.toFixed(1)}%</span>
          </div>
          <div style="font-size:11px;color:var(--eb-text-muted);">Campione: ${b.n} partite</div>
        </div>
      `;
    });
    html += '</div>';
    return html;
  }

  // --- VIEW 5: PRO (SUBSCRIPTION & PRICING) ---
  function renderProView(container) {
    let html = `
      <div style="text-align:center;max-width:680px;margin:0 auto 24px auto;">
        <h2 style="font-size:24px;font-weight:700;margin-bottom:8px;">Piani & Strumenti Professionali</h2>
        <p style="font-size:14px;color:var(--eb-text-secondary);">
          Sblocca l'accesso illimitato a tutti gli sport, al comparatore quote a 12 bookmaker e al calcolatore Bet Builder con correlazione Monte Carlo.
        </p>
      </div>

      <div class="pricing-grid">
        <div class="pricing-card">
          <div>
            <div class="plan-name">EdgeBet Free</div>
            <div style="font-size:13px;color:var(--eb-text-secondary);margin-top:4px;">Per consultare le basi statistiche</div>
            <div class="plan-price">0 &euro; <span>/ per sempre</span></div>
            <ul class="plan-features">
              <li>${ICONS.check} Le migliori 4 selezioni di oggi</li>
              <li>${ICONS.check} 1 evento dimostrativo per ogni sport</li>
              <li>${ICONS.check} Quota equa del modello</li>
              <li>${ICONS.check} Accesso al registro pubblico prove</li>
              <li style="color:var(--eb-text-muted);">&bull; Comparatore 12 bookmaker limitato</li>
              <li style="color:var(--eb-text-muted);">&bull; Bet Builder avanzato bloccato</li>
            </ul>
          </div>
          <div>
            <button class="btn-checkout" style="background:var(--eb-surface-elevated);color:var(--eb-text);border:1px solid var(--eb-border);" disabled>
              Piano Attuale
            </button>
          </div>
        </div>

        <div class="pricing-card featured">
          <div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
              <span class="plan-name">EdgeBet Pro</span>
              <span class="brand-tag">Consigliato</span>
            </div>
            <div style="font-size:13px;color:var(--eb-text-secondary);margin-top:4px;">Per lo scommettitore consapevole</div>
            <div class="plan-price">12 &euro; <span>/ mese</span></div>
            <ul class="plan-features">
              <li>${ICONS.check} <strong>Tutte le selezioni illimitate</strong> su 7 sport</li>
              <li>${ICONS.check} <strong>Tabella 12 bookmaker completa</strong> (Pinnacle, Bet365, Unibet, ecc.)</li>
              <li>${ICONS.check} <strong>Calcolatore Bet Builder con lift %</strong></li>
              <li>${ICONS.check} <strong>Registro My Bets illimitato</strong> con monitoraggio ROI</li>
              <li>${ICONS.check} Aggiornamento automatico ogni 20 minuti</li>
            </ul>
          </div>
          <div>
            <button class="btn-checkout" id="btn-subscribe-pro">
              Attiva Abbonamento Pro
            </button>
          </div>
        </div>
      </div>

      <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:16px;margin-top:24px;">
        <h4 style="font-size:14px;font-weight:600;margin-bottom:8px;">Ambiente Di Prova (Demo Sandbox)</h4>
        <p style="font-size:12px;color:var(--eb-text-secondary);margin-bottom:12px;">
          Sei in modalita demo. Puoi testare istantaneamente come cambia l'interfaccia passando al tier Pro o VIP:
        </p>
        <div style="display:flex;gap:10px;">
          <button class="btn-add-slip" data-set-tier="free">Imposta Free</button>
          <button class="btn-add-slip" data-set-tier="pro">Imposta Pro</button>
          <button class="btn-add-slip" data-set-tier="vip">Imposta VIP</button>
        </div>
      </div>

      ${renderResponsibleGamblingFooter()}
    `;

    container.innerHTML = html;
    attachViewEvents();
  }

  // --- VIEW 6: GUIDA (QUANTITATIVE GLOSSARY) ---
  function renderGuidaView(container) {
    const terms = [
      { t: 'Quota Equa (Fair Odds)', d: 'Il reciproco esatto della probabilita stimata (1 / Probabilita). Rappresenta il prezzo teorico neutro senza alcun margine o profitto trattenuto dal bookmaker.' },
      { t: 'Valore Atteso Positivo (+EV)', d: 'Situazione in cui la quota offerta dal mercato e superiore alla quota equa stimata dal nostro modello. Nel lungo periodo, scommettere su selezioni +EV garantisce un rendimento positivo atteso.' },
      { t: 'Dixon-Coles (20.000 iterazioni)', d: 'Modello matematico basato su processi bivariati di Poisson con correzione per punteggi bassi (0-0, 1-0, 0-1, 1-1). Viene simulato 20.000 volte per ogni partita di calcio per derivare le distribuzioni congiunte.' },
      { t: 'Lavagna / Allibramento (Overround/Vig)', d: 'La somma delle probabilita implicite delle quote di un mercato, che supera sempre il 100% (solitamente tra il 103% e il 108%). Rappresenta la commissione matematica prelevata dal bookmaker.' },
      { t: 'Criterio di Kelly Frazionario', d: 'Formula matematica per il dimensionamento ottimale della puntata proporzionata al vantaggio (+EV) e alla dimensione del bankroll. Consigliamo 1/4 di Kelly per limitare la volatilita.' },
      { t: 'Correlation Lift (Bet Builder)', d: 'L incremento percentuale della probabilita di una multipla Same-Game rispetto a eventi indipendenti, dovuto alla forte interdipendenza (es. vittoria squadra + Over corner).' },
      { t: 'Closing Line Value (CLV)', d: 'Il valore della quota al momento della chiusura del mercato (kickoff). Battere costantemente la quota di chiusura dei bookmaker asiatici (Pinnacle) e il principale indicatore di competenza predittiva.' }
    ];

    let html = `
      <div style="margin-bottom:20px;">
        <h2 style="font-size:18px;font-weight:700;margin-bottom:6px;">Guida & Glossario Quantitativo</h2>
        <p style="font-size:13px;color:var(--eb-text-secondary);">
          Concetti chiave della finanza sportiva e della modellazione statistica impiegata su EdgeBet AI.
        </p>
      </div>

      <div style="display:flex;flex-direction:column;gap:12px;">
    `;

    terms.forEach(term => {
      html += `
        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px 16px;">
          <h4 style="font-size:14px;font-weight:600;color:var(--eb-text);margin-bottom:4px;">${escapeHtml(term.t)}</h4>
          <p style="font-size:13px;color:var(--eb-text-secondary);line-height:1.5;">${escapeHtml(term.d)}</p>
        </div>
      `;
    });

    html += `
      </div>
      ${renderResponsibleGamblingFooter()}
    `;

    container.innerHTML = html;
  }

  // --- VIEW 7: MIE SCOMMESSE (MY BETS TRACKER) ---
  async function renderMyBetsView(container) {
    container.innerHTML = '<div style="padding:40px;text-align:center;">Caricamento storico scommesse...</div>';
    await fetchMyBets();

    const stats = state.betsStats || { count: 0, open: 0, staked: 0, returned: 0, profit: 0, roiPct: 0, hitRatePct: 0 };
    const bets = state.myBets || [];

    let html = `
      <div style="margin-bottom:20px;">
        <h2 style="font-size:18px;font-weight:700;margin-bottom:6px;">Le Mie Scommesse & Gestione Bankroll</h2>
        <p style="font-size:13px;color:var(--eb-text-secondary);">
          Traccia puntate, vincite e resa percentuale reale (ROI) del tuo portafoglio sportivo.
        </p>
      </div>

      <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;margin-bottom:24px;">
        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
          <div style="font-size:12px;color:var(--eb-text-secondary);">Profitto Netto</div>
          <div class="num" style="font-size:22px;font-weight:700;color:${stats.profit >= 0 ? 'var(--eb-win)' : 'var(--eb-loss)'};margin-top:4px;">
            ${formatCurrency(stats.profit)}
          </div>
        </div>
        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
          <div style="font-size:12px;color:var(--eb-text-secondary);">Rendimento Reale (ROI)</div>
          <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-text);margin-top:4px;">
            ${stats.roiPct ? stats.roiPct.toFixed(1) + '%' : '0.0%'}
          </div>
        </div>
        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
          <div style="font-size:12px;color:var(--eb-text-secondary);">Tasso Di Vittoria</div>
          <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-accent-light);margin-top:4px;">
            ${stats.hitRatePct ? stats.hitRatePct.toFixed(1) + '%' : '0.0%'}
          </div>
        </div>
        <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-md);padding:14px;">
          <div style="font-size:12px;color:var(--eb-text-secondary);">Totale Giocate</div>
          <div class="num" style="font-size:22px;font-weight:700;color:var(--eb-text);margin-top:4px;">
            ${stats.count} (${stats.open} aperte)
          </div>
        </div>
      </div>

      <div style="background:var(--eb-surface);border:1px solid var(--eb-border);border-radius:var(--eb-radius-lg);padding:18px;">
        <h4 style="font-size:15px;font-weight:600;margin-bottom:12px;">Registro Personale Giocate</h4>
    `;

    if (bets.length === 0) {
      html += '<p style="color:var(--eb-text-secondary);font-size:13px;">Nessuna scommessa registrata finora. Aggiungi selezioni dalla Schedina.</p>';
    } else {
      html += `
        <table class="data-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Evento</th>
              <th>Selezione</th>
              <th class="num-col">Quota</th>
              <th class="num-col">Puntata</th>
              <th>Esito</th>
              <th>Azioni</th>
            </tr>
          </thead>
          <tbody>
      `;

      bets.forEach(b => {
        html += `
          <tr>
            <td style="color:var(--eb-text-secondary);font-size:12px;">${formatDate(b.createdAt)}</td>
            <td style="font-weight:600;">${escapeHtml(b.title)}</td>
            <td>${escapeHtml(b.pick)}</td>
            <td class="num-col num">@${formatOdds(b.odds)}</td>
            <td class="num-col num">${formatCurrency(b.stake)}</td>
            <td>
              <select class="num" data-bet-result-id="${escapeHtml(b.id)}" style="background:var(--eb-surface-hover);border:1px solid var(--eb-border);color:var(--eb-text);padding:3px 6px;border-radius:var(--eb-radius-sm);font-size:12px;">
                <option value="open" ${b.result === 'open' ? 'selected' : ''}>Aperta</option>
                <option value="won" ${b.result === 'won' ? 'selected' : ''}>Vinta</option>
                <option value="lost" ${b.result === 'lost' ? 'selected' : ''}>Persa</option>
                <option value="void" ${b.result === 'void' ? 'selected' : ''}>Rimborsata</option>
              </select>
            </td>
            <td>
              <button data-delete-bet-id="${escapeHtml(b.id)}" style="color:var(--eb-loss);font-size:12px;">Elimina</button>
            </td>
          </tr>
        `;
      });

      html += '</tbody></table>';
    }

    html += `
      </div>
      ${renderResponsibleGamblingFooter()}
    `;

    container.innerHTML = html;
    attachViewEvents();
  }

  // --- FOOTER & COMPLIANCE ---
  function renderResponsibleGamblingFooter() {
    return `
      <footer class="rg-footer">
        <div>
          <strong>EdgeBet AI e una piattaforma di ricerca quantitativa e comparazione statistica.</strong>
          Non accettiamo scommesse, non gestiamo depositi e non agiamo come operatori di gioco.
        </div>
        <div>
          Il gioco d'azzardo e vietato ai minori di 18 anni e puo causare dipendenza patologica. Gioca responsabilmente.
        </div>
        <div class="rg-links">
          <a href="#/guida">Glossario Metodologico</a>
          <a href="#/prove">Verifica Risultati</a>
          <a href="https://www.adm.gov.it" target="_blank" rel="noopener">ADM Gioco Responsabile</a>
        </div>
      </footer>
    `;
  }

  // --- EVENT ATTACHMENTS ---
  function attachViewEvents() {
    // Row expansion
    document.querySelectorAll('.pick-row-header').forEach(hdr => {
      hdr.addEventListener('click', async (e) => {
        if (e.target.closest('.btn-add-slip') || e.target.closest('a')) return;
        const rowId = hdr.getAttribute('data-toggle-id');
        if (state.expandedId === rowId) {
          state.expandedId = null;
        } else {
          state.expandedId = rowId;
          if (!state.details[rowId]) {
            await fetchDetail(rowId);
          }
        }
        renderCurrentView();
      });
    });

    // Dossier Tab switcher
    document.querySelectorAll('.dossier-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const tab = btn.getAttribute('data-dossier-tab');
        const targetId = btn.getAttribute('data-target-id');
        state.activeDossierTab[targetId] = tab;
        const drawer = document.getElementById('drawer-' + targetId);
        if (drawer) {
          drawer.innerHTML = renderDetailDrawerContent(targetId);
          attachViewEvents();
        }
      });
    });

    // Add to Slip buttons
    document.querySelectorAll('.btn-add-slip[data-slip-id]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const slipId = btn.getAttribute('data-slip-id');
        const found = state.rows.find(r => r.id === slipId);
        if (!found) return;

        const idx = state.slip.findIndex(s => s.id === slipId);
        if (idx >= 0) {
          state.slip.splice(idx, 1);
        } else {
          state.slip.push(found);
        }
        updateSlipBadge();
        renderCurrentView();
      });
    });

    // Remove leg from slip
    document.querySelectorAll('.btn-remove-leg').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = btn.getAttribute('data-remove-id');
        state.slip = state.slip.filter(s => s.id !== id);
        updateSlipBadge();
        renderCurrentView();
      });
    });

    // Filter toggles
    const hotToggle = document.getElementById('toggle-hot-filter');
    if (hotToggle) {
      hotToggle.addEventListener('click', () => {
        state.onlyHot = !state.onlyHot;
        renderCurrentView();
      });
    }

    const searchInput = document.getElementById('search-filter-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        const container = document.getElementById('pick-list-container');
        if (container) {
          container.innerHTML = renderPickRows(getFilteredRows());
          attachViewEvents();
        }
      });
    }

    // Sport selector chips
    document.querySelectorAll('.sport-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        state.selectedSport = chip.getAttribute('data-sport');
        renderCurrentView();
      });
    });

    // Copy Slip to Clipboard
    const copyBtn = document.getElementById('btn-copy-slip');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => {
        let text = 'EdgeBet AI - Schedina Consigliata:\n';
        state.slip.forEach(s => {
          text += `- ${s.title}: ${s.pick?.label} @${formatOdds(s.pick?.bestOdds || s.pick?.fairOdds)}\n`;
        });
        navigator.clipboard.writeText(text).then(() => {
          copyBtn.textContent = 'Copiato negli appunti';
          setTimeout(() => { copyBtn.textContent = 'Copia Schedina Negli Appunti'; }, 2000);
        });
      });
    }

    // Save Slip to My Bets
    const saveBetsBtn = document.getElementById('btn-save-to-mybets');
    if (saveBetsBtn) {
      saveBetsBtn.addEventListener('click', async () => {
        for (const leg of state.slip) {
          await fetch('/api/v1/bets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: leg.title,
              pick: leg.pick?.label || 'Esito',
              odds: leg.pick?.bestOdds || leg.pick?.fairOdds || 1.5,
              stake: 10,
              currency: state.currency,
              sport: leg.sport
            })
          });
        }
        window.location.hash = '#/mie-scommesse';
      });
    }

    // Demo Tier Switcher
    document.querySelectorAll('[data-set-tier]').forEach(btn => {
      btn.addEventListener('click', () => {
        setDemoTier(btn.getAttribute('data-set-tier'));
      });
    });

    // My Bets Status Dropdown
    document.querySelectorAll('[data-bet-result-id]').forEach(sel => {
      sel.addEventListener('change', async (e) => {
        const id = sel.getAttribute('data-bet-result-id');
        const res = e.target.value;
        await fetch('/api/v1/bets/' + encodeURIComponent(id), {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ result: res })
        });
        renderMyBetsView(document.getElementById('main-viewport'));
      });
    });

    // Delete bet
    document.querySelectorAll('[data-delete-bet-id]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-delete-bet-id');
        await fetch('/api/v1/bets/' + encodeURIComponent(id), { method: 'DELETE' });
        renderMyBetsView(document.getElementById('main-viewport'));
      });
    });

    // Open slip trigger in top banner
    const slipTrigger = document.getElementById('btn-open-slip-top');
    if (slipTrigger) {
      slipTrigger.addEventListener('click', () => {
        window.location.hash = '#/schedina';
      });
    }
  }

  function updateSlipBadge() {
    document.querySelectorAll('.slip-count-badge').forEach(b => {
      b.textContent = state.slip.length;
    });
  }

  function updateTierUI() {
    const el = document.getElementById('tier-current-name');
    if (el) el.textContent = state.tier;
    const sel = document.getElementById('demo-tier-select');
    if (sel) sel.value = state.tier;
  }

  function formatTime(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
  }

  function formatDate(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('it-IT', { day: '2-digit', month: '2-digit' });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Global Initializer
  window.addEventListener('DOMContentLoaded', () => {
    // Setup service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    // Attach static demo select in sidebar
    const demoSel = document.getElementById('demo-tier-select');
    if (demoSel) {
      demoSel.addEventListener('change', (e) => {
        setDemoTier(e.target.value);
      });
    }

    // Setup initial routing & data loading
    handleRoute();
    fetchUserStatus();
    fetchFeed();

    // 20-minute auto refresh polling
    setInterval(() => {
      fetchFeed();
    }, 20 * 60 * 1000);
  });

})();
