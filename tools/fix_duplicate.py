with open('public/index.html', encoding='utf-8') as f:
    text = f.read()

# Replace the duplicated fetch block
duplicate_block = """    async function fetchMultisportData(isAutoTick = false) {
      window.__fetch_trace = 'entered';
      try {
        window.__fetch_trace = 'fetching';
        const res = await fetch(`/api/multisport?tier=${APP.tier}`);
        window.__fetch_trace = 'res_' + res.status;

        const res = await fetch(`/api/multisport?tier=${APP.tier}`);"""

clean_block = """    async function fetchMultisportData(isAutoTick = false) {
      try {
        const res = await fetch(`/api/multisport?tier=${APP.tier}`);"""

# Also remove the head error catcher
if duplicate_block in text:
    text = text.replace(duplicate_block, clean_block, 1)
    print("Cleaned duplicate block")
else:
    # Try regex
    import re
    text = re.sub(r'async function fetchMultisportData[^{]+\{[^c]+const res = await fetch[^\n]+\n[^\n]+\n\s+const res = await fetch[^\n]+;', clean_block, text, count=1)
    print("Regex cleaned duplicate block")

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated public/index.html")
