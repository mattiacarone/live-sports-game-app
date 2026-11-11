const fs = require('fs');
const report = JSON.parse(fs.readFileSync('.taste-skill/inspect/report.json', 'utf8'));
console.log('Findings:', JSON.stringify(report.findings, null, 2));
