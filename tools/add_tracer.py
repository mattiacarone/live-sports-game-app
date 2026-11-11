with open('public/index.html', encoding='utf-8') as f:
    text = f.read()

target = 'async function fetchMultisportData(isAutoTick = false) {\n      try {'
replacement = '''async function fetchMultisportData(isAutoTick = false) {
      window.__fetch_trace = 'entered';
      try {
        window.__fetch_trace = 'fetching';
        const res = await fetch(`/api/multisport?tier=${APP.tier}`);
        window.__fetch_trace = 'res_' + res.status;'''

if target in text:
    text = text.replace(target, replacement, 1)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Tracer added")
else:
    # Try with single or double spacing
    import re
    text = re.sub(r'async function fetchMultisportData\([^\)]*\)\s*\{\s*try\s*\{', replacement, text, count=1)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Regex tracer added")
