with open('server.py', 'r', encoding='utf-8') as f:
    text = f.read()

old_csp = "script-src 'self';"
new_csp = "script-src 'self' 'unsafe-inline';"

if old_csp in text:
    text = text.replace(old_csp, new_csp, 1)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated CSP in server.py with 'unsafe-inline'")
else:
    print("old_csp not found")
