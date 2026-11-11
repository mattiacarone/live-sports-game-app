const fs = require('fs');

let html = fs.readFileSync('public/index.html', 'utf8');

// 1. Update .top-shell to pure minimalist white
html = html.replace(
  /\.top-shell\s*\{[^}]*\}/s,
  `.top-shell {
      background: var(--surface);
      color: var(--text);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 100;
      width: 100%;
    }`
);

// 2. Update brand mark, name, tag
html = html.replace(
  /\.brand-name\s*\{[^}]*\}/s,
  `.brand-name {
      font-size: 15px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--text);
    }`
);

html = html.replace(
  /\.brand-mark\s*\{[^}]*\}/s,
  `.brand-mark {
      width: 26px;
      height: 26px;
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 12px;
      letter-spacing: -0.02em;
    }`
);

html = html.replace(
  /\.brand-tag\s*\{[^}]*\}/s,
  `.brand-tag {
      font-size: 11px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: var(--radius-chip);
      background: var(--ground);
      color: var(--muted);
      border: 1px solid var(--border);
    }`
);

// 3. Update view tabs
html = html.replace(
  /\.view-tab-btn\s*\{[^}]*\}/s,
  `.view-tab-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 32px;
      padding: 0 11px;
      border-radius: var(--radius-control);
      color: var(--muted);
      background: transparent;
      border: 1px solid transparent;
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
      transition: all 120ms ease;
    }`
);

html = html.replace(
  /\.view-tab-btn:hover\s*\{[^}]*\}/s,
  `.view-tab-btn:hover {
      color: var(--text);
      background: var(--raised);
    }`
);

html = html.replace(
  /\.view-tab-btn\.active\s*\{[^}]*\}/s,
  `.view-tab-btn.active {
      color: #ffffff;
      background: var(--primary);
      border-color: var(--primary);
      font-weight: 600;
    }`
);

html = html.replace(
  /\.view-tab-btn\.vip-tab\.active\s*\{[^}]*\}/s,
  `.view-tab-btn.vip-tab.active {
      background: #78350f;
      border-color: #92400e;
      color: #ffffff;
    }`
);

html = html.replace(
  /\.tab-count-pill\s*\{[^}]*\}/s,
  `.tab-count-pill {
      padding: 1px 6px;
      border-radius: var(--radius-chip);
      background: var(--raised);
      color: var(--muted);
      font-size: 11px;
      font-weight: 600;
    }
    .view-tab-btn.active .tab-count-pill {
      background: #334155;
      color: #ffffff;
    }`
);

// 4. Update sync pill, util buttons, slip trigger
html = html.replace(
  /\.sync-pill\s*\{[^}]*\}/s,
  `.sync-pill {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      height: 32px;
      padding: 0 10px;
      border-radius: var(--radius-control);
      background: var(--ground);
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 12px;
    }`
);

html = html.replace(
  /\.util-btn\s*\{[^}]*\}/s,
  `.util-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      height: 32px;
      padding: 0 11px;
      border-radius: var(--radius-control);
      background: var(--surface);
      border: 1px solid var(--border);
      color: var(--text);
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
      transition: all 120ms ease;
    }`
);

html = html.replace(
  /\.util-btn:hover\s*\{[^}]*\}/s,
  `.util-btn:hover {
      background: var(--raised);
      border-color: #cbd5e1;
    }`
);

html = html.replace(
  /\.slip-trigger-btn\s*\{[^}]*\}/s,
  `.slip-trigger-btn {
      background: var(--accent);
      color: #ffffff;
      border-color: var(--accent);
      font-weight: 600;
    }`
);

html = html.replace(
  /\.slip-trigger-btn:hover\s*\{[^}]*\}/s,
  `.slip-trigger-btn:hover {
      background: #036347;
      border-color: #036347;
    }`
);

// 5. Update KPI labels to uppercase micro-labels
html = html.replace(
  /\.kpi-label\s*\{[^}]*\}/s,
  `.kpi-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--muted);
    }`
);

html = html.replace(
  /\.kpi-cell\s*\{[^}]*\}/s,
  `.kpi-cell {
      padding: 12px 16px;
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      justify-content: center;
      gap: 3px;
    }`
);

html = html.replace(
  /\.kpi-value\s*\{[^}]*\}/s,
  `.kpi-value {
      font-size: 22px;
      font-weight: 700;
      color: var(--text);
      line-height: 1.15;
    }`
);

html = html.replace(
  /\.kpi-cell\.lead-cell \.kpi-value\s*\{[^}]*\}/s,
  `.kpi-cell.lead-cell .kpi-value {
      font-size: 26px;
      font-weight: 700;
      color: var(--accent);
    }`
);

// 6. Make event card padding cleaner and add collapsible dossier styling
const dossierCss = `
    /* DOSSIER EXPANSION ACCORDION */
    .dossier-toggle-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 8px 12px;
      background: var(--ground);
      border: 1px solid var(--rule);
      border-radius: var(--radius-control);
      font-size: 12px;
      font-weight: 500;
      color: var(--muted);
      cursor: pointer;
      transition: all 140ms ease;
    }
    .dossier-toggle-bar:hover {
      background: var(--raised);
      color: var(--text);
      border-color: var(--border);
    }
    .dossier-toggle-bar.open {
      background: #f1f5f9;
      color: var(--text);
      border-color: var(--border);
      border-bottom-left-radius: 0;
      border-bottom-right-radius: 0;
    }
    .dossier-chevron {
      font-size: 11px;
      transition: transform 180ms ease;
    }
    .dossier-toggle-bar.open .dossier-chevron {
      transform: rotate(180deg);
    }
    .dossier-wrapper {
      display: none;
      padding: 12px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-top: none;
      border-bottom-left-radius: var(--radius-control);
      border-bottom-right-radius: var(--radius-control);
    }
    .dossier-wrapper.open {
      display: block;
    }
`;

if (!html.includes('.dossier-toggle-bar')) {
  html = html.replace('.dossier-tab-nav {', dossierCss + '\n    .dossier-tab-nav {');
}

fs.writeFileSync('public/index.html', html, 'utf8');
console.log('Successfully updated CSS styles in public/index.html');

