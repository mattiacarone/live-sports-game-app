with open('public/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: contrast on pick-category-meta
text = text.replace(
    ".pick-category-meta {\n      font-size: 13px;\n      font-weight: 600;\n      color: var(--positive);",
    ".pick-category-meta {\n      font-size: 13px;\n      font-weight: 600;\n      color: #047857;"
)

# Fix 2: mobile responsive enhancements
old_media = """    @media (max-width: 640px) {
      :root {
        --pad: 16px;
        --card-pad: 16px;
      }
      .canvas-title-block h1 {
        font-size: 20px;
      }
      .event-title {
        font-size: 16px;
      }
      .primary-pick-banner {
        flex-direction: column;
        align-items: stretch;
      }
      .price-compare-col {
        text-align: left;
      }
    }"""

new_media = """    @media (max-width: 640px) {
      :root {
        --pad: 16px;
        --card-pad: 16px;
      }
      .canvas-title-block h1 {
        font-size: 20px;
      }
      .kpi-value {
        font-size: 17px !important;
      }
      .kpi-cell.lead-cell .kpi-value {
        font-size: 20px !important;
      }
      .comp-sidebar {
        padding: 12px 16px;
        overflow-x: hidden;
      }
      .comp-nav-item {
        max-width: 100%;
        overflow: hidden;
      }
      .comp-name-text {
        max-width: 170px;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .event-title {
        font-size: 16px;
      }
      .primary-pick-banner {
        flex-direction: column;
        align-items: stretch;
      }
      .price-compare-col {
        text-align: left;
      }
    }"""

if old_media in text:
    text = text.replace(old_media, new_media, 1)
    print("Replaced mobile media query")
else:
    # Handle possible blank line differences
    import re
    text = re.sub(r'@media\s*\(max-width:\s*640px\)\s*\{[^}]+\}', new_media, text, count=1)
    print("Regex replaced mobile media query")

with open('public/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated public/index.html with mobile polish")
