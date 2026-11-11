const fs = require('fs');

let html = fs.readFileSync('public/index.html', 'utf8');

// Add toggleDossier function
const toggleFn = `
    function toggleDossier(cardUid, btnEl) {
      const wrap = document.getElementById('dossier-wrap-' + cardUid);
      if (!wrap) return;
      const isOpen = wrap.classList.toggle('open');
      btnEl.classList.toggle('open', isOpen);
    }
`;

if (!html.includes('function toggleDossier')) {
  html = html.replace('function switchDossierTab(', toggleFn + '\n    function switchDossierTab(');
}

// Wrap dossier inside dossier-toggle-bar and dossier-wrapper
const oldDossierStart = `          <!-- DOSSIER TABS -->\n\n          <div class="dossier-tab-nav" role="tablist">`;
const newDossierStart = `          <!-- DOSSIER ACCORDION TOGGLE -->\n          <button type="button" class="dossier-toggle-bar" onclick="toggleDossier('\${uid}', this)">\n            <span>Analisi Dettagliata &bull; 12 Bookmaker, Flussi Sindacati e Mercati (\${books.length || 12} siti)</span>\n            <span class="dossier-chevron">&#9662;</span>\n          </button>\n          <div id="dossier-wrap-\${uid}" class="dossier-wrapper">\n          <div class="dossier-tab-nav" role="tablist">`;

const oldDossierEnd = `          <div id="panel-\${uid}-markets" class="dossier-panel">\n\n            \${renderMarketMatrix(uid, mktCats, builders, title, sportId)}\n\n          </div>\n\n        </article>`;
const newDossierEnd = `          <div id="panel-\${uid}-markets" class="dossier-panel">\n\n            \${renderMarketMatrix(uid, mktCats, builders, title, sportId)}\n\n          </div>\n          </div><!-- /dossier-wrapper -->\n\n        </article>`;

html = html.replace(oldDossierStart, newDossierStart);
html = html.replace(oldDossierEnd, newDossierEnd);

fs.writeFileSync('public/index.html', html, 'utf8');
console.log('Successfully wrapped dossier in collapsible toggle');

