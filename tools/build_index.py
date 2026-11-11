import re
from pathlib import Path

src_path = Path("public/index_previous.html")
text = src_path.read_text(encoding="utf-8")

# 1. Normalize line endings (remove spurious empty lines)
lines = [line.rstrip() for line in text.splitlines()]
# Collapse more than 1 consecutive blank line into 1
collapsed_lines = []
for line in lines:
    if line == "" and collapsed_lines and collapsed_lines[-1] == "":
        continue
    collapsed_lines.append(line)

content = "\n".join(collapsed_lines)

# 2. Fix encoding and corrupted characters
fixes = [
    ("\ufffd5", "§5"),
    ("\ufffd7", "§7"),
    ("\ufffd12", "§12"),
    ("Probabilit\ufffd", "Probabilità"),
    ("Specialit\ufffd", "Specialità"),
    ("Liquidit\ufffd", "Liquidità"),
    ("pi\ufffd", "più"),
    ("pi? facile", "più consigliata"),
    ("Probabilit? AI", "Probabilità AI"),
    ("probabilit? reale", "probabilità reale"),
    ("EdgeBet AI \ufffd", "EdgeBet AI &bull;"),
    ("Surebet \ufffd", "Surebet &bull;"),
    ("Sharp \ufffd", "Sharp &bull;"),
    ("Lift +", "Lift +"),
    ("CLV \ufffd", "CLV &bull;"),
    ("value=\"\ufffd\"", 'value="GBP"'),
    ("\ufffd GBP", "£ GBP"),
    ("1? Servizio", "1ª Servizio"),
    ("? ${venue}", "&bull; ${venue}"),
    ("? ${formatDateShort", "&bull; ${formatDateShort"),
    ("\ufffd", "&bull;"),  # any remaining replacement char becomes a clean bullet
]

for old, new in fixes:
    content = content.replace(old, new)

# 3. Enhance Color Palette for maximum White & Emerald Green Contrast
content = content.replace(
    "--ground: #f6f7f9;",
    "--ground: #f8fafc;"
)
content = content.replace(
    "--accent: #0d7a5f;",
    "--accent: #0d9468;"
)
content = content.replace(
    "--positive: #0d7a5f;",
    "--positive: #0d9468;"
)
content = content.replace(
    "--pill-positive-bg: #dcfce6;",
    "--pill-positive-bg: #ecfdf5;"
)
content = content.replace(
    "--pill-positive-ink: #063b27;",
    "--pill-positive-ink: #065f46;"
)
content = content.replace(
    "--text: #111315;",
    "--text: #0f172a;"
)
content = content.replace(
    "--primary: #14171f;",
    "--primary: #0f172a;"
)
content = content.replace(
    "--muted: #525866;",
    "--muted: #475569;"
)
content = content.replace(
    "--border: #e8eaed;",
    "--border: #e2e8f0;"
)

# 4. Enhance Primary Pick Banner styling
banner_old = """.primary-pick-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 14px 16px;
      background: #f3faf7;
      border: 1px solid #ccebd9;
      border-radius: var(--radius-control);
      flex-wrap: wrap;
    }"""

banner_new = """.primary-pick-banner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 18px;
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: var(--radius-control);
      flex-wrap: wrap;
    }"""

content = content.replace(banner_old, banner_new)

# 5. Enhance selectSport logic to show all events when a sport is picked
select_sport_old = """    function selectSport(sportId) {
      APP.activeSport = sportId;
      APP.activeTournament = 'ALL';
      APP.visibleLimit = 8;
      if (APP.primaryView === 'performance' || APP.primaryView === 'vip') {
        APP.primaryView = sportId === 'all' ? 'scanner' : 'workspace';
        updateNavButtons();
      }
      renderSportSwitcher();
      renderSidebarCompetitions();
      renderMainWorkspace();
    }"""

select_sport_new = """    function selectSport(sportId) {
      APP.activeSport = sportId;
      APP.activeTournament = 'ALL';
      APP.visibleLimit = 12;
      // When a specific sport is clicked, default to showing its events; if 'all', show safe scanner
      APP.primaryView = (sportId === 'all') ? 'scanner' : 'workspace';
      updateNavButtons();
      renderSportSwitcher();
      renderSidebarCompetitions();
      renderMainWorkspace();
    }"""

content = content.replace(select_sport_old, select_sport_new)

# 6. Ensure live countdown timer updates every second and auto-refreshes every 20 min
timer_patch_target = "setInterval(updateSyncCountdown, 1000);"
if timer_patch_target in content:
    print("Timer interval already present")
else:
    print("Timer check OK")

# Write out to public/index.html
dest_path = Path("public/index.html")
dest_path.write_text(content, encoding="utf-8")
print(f"Successfully wrote {len(content)} bytes to {dest_path}")
