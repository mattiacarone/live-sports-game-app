const fs = require('fs');

let content = fs.readFileSync('public/index.html', 'utf8');

// 1. Currency options & state
content = content.replace(
  '<option value="?">? EUR</option>',
  '<option value="€">€ EUR</option>'
);
content = content.replace(
  '<option value="GBP">£ GBP</option>',
  '<option value="£">£ GBP</option>'
);
content = content.replace(
  "currency: '?',",
  "currency: '€',"
);

// 2. Search keyboard shortcut
content = content.replace(
  '<span class="search-kbd">?K</span>',
  '<span class="search-kbd">Ctrl+K</span>'
);

// 3. Typo in KPI label & subtitle
content = content.replace(
  'Giocate ad alta probabilit&bull; (&ge;74%)',
  'Giocate ad alta probabilità (&ge;74%)'
);
content = content.replace(
  'selezioni validate (>=74% probabilit&bull; reale)',
  'selezioni validate (&ge;74% probabilità reale)'
);
content = content.replace(
  '${arbCount} Surebet &bull; ${droppingCount} Drop',
  '${arbCount} Surebet · ${droppingCount} Drop'
);
content = content.replace(
  'EdgeBet AI &bull;',
  'EdgeBet AI ·'
);
content = content.replace(
  'Probabilita stimata dal modello:',
  'Probabilità stimata dal modello:'
);

fs.writeFileSync('public/index.html', content, 'utf8');
console.log('Fixed typography, encoding and currency strings');
