const fs = require('fs');
const s = fs.readFileSync('public/index.html', 'utf8');
const regex = /class="([^"]*)"/g;
let m;
const set = new Set();
const chartRe = /(^|[\s_-])(chart|plot|graph|timeline|calendar|cal|gantt|heatmap|matrix|strip)([\s_-]|$)/i;
while ((m = regex.exec(s)) !== null) {
  m[1].split(/\s+/).forEach(c => {
    if (chartRe.test(c)) set.add(c);
  });
}
console.log('Chart-matching classes:', [...set]);
