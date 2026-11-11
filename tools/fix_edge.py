with open('public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix contrast
text = text.replace(
    "color: #047857;",
    "color: #047857 !important;"
)

# Fix mobile comp-nav-item padding to keep counts away from the phone's right edge
text = text.replace(
    ".comp-nav-item {\n        max-width: 100%;\n        overflow: hidden;\n      }",
    ".comp-nav-item {\n        max-width: 100%;\n        overflow: hidden;\n        padding: 6px 16px !important;\n      }"
)

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated padding and contrast")
