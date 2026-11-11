const fs = require('fs');

let html = fs.readFileSync('public/index.html', 'utf8');

const target1 = '<!-- DOSSIER TABS -->';
const target2 = '${renderMarketMatrix(uid, mktCats, builders, title, sportId)}\r\n\r\n          </div>\r\n\r\n        </article>';

if (html.includes(target1)) {
  const replacement1 = `<!-- DOSSIER ACCORDION TOGGLE -->
          <button type="button" class="dossier-toggle-bar" onclick="toggleDossier('\${uid}', this)">
            <span>Analisi Dettagliata &bull; 12 Bookmaker, Flussi Sindacati e Mercati (\${books.length || 12} siti)</span>
            <span class="dossier-chevron">&#9662;</span>
          </button>
          <div id="dossier-wrap-\${uid}" class="dossier-wrapper">
          <div class="dossier-tab-nav" role="tablist">`;

  // Replace from <!-- DOSSIER TABS --> to <div class="dossier-tab-nav" role="tablist">
  html = html.replace(/<!-- DOSSIER TABS -->\r?\n\r?\n\s*<div class="dossier-tab-nav" role="tablist">/, replacement1);
}

if (html.includes(target2)) {
  const replacement2 = '${renderMarketMatrix(uid, mktCats, builders, title, sportId)}\r\n\r\n          </div>\r\n          </div><!-- /dossier-wrapper -->\r\n\r\n        </article>';
  html = html.replace(target2, replacement2);
} else {
  // Try regex for CRLF / LF
  html = html.replace(/(\$\{renderMarketMatrix\([^}]+\)\}\r?\n\r?\n\s*<\/div>)(\r?\n\r?\n\s*<\/article>)/, '$1\r\n          </div><!-- /dossier-wrapper -->$2');
}

fs.writeFileSync('public/index.html', html, 'utf8');
console.log('Applied dossier toggle wrapping successfully');

