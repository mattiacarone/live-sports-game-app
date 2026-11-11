with open('public/index.html', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'id=["\']sport-switcher-bar["\']', text)]
print('Occurrences of id="sport-switcher-bar":', len(matches))
for idx in matches:
    print(text[idx-30:idx+60].replace('\n', ' '))
