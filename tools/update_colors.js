const fs = require('fs');

let content = fs.readFileSync('public/index.html', 'utf8');

// Update --positive and --accent to #047857 for 5.67:1 WCAG AA contrast ratio on white
content = content.replace(
  '--accent: #0d9468;',
  '--accent: #047857;'
);
content = content.replace(
  '--positive: #0d9468;',
  '--positive: #047857;'
);

fs.writeFileSync('public/index.html', content, 'utf8');
console.log('Updated --accent and --positive to #047857');
