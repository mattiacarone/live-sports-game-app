with open('server.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'b = json.dumps(_clean(body), ensure_ascii=False, allow_nan=False).encode("utf-8")'
replacement = '''try:
                b = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
            except ValueError:
                b = json.dumps(_clean(body), ensure_ascii=False).encode("utf-8")'''

if target in text:
    text = text.replace(target, replacement, 1)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully patched send() in server.py")
else:
    print("Target not found")
