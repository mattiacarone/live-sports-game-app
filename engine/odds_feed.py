"""Live bookmaker prices.

Two real sources, both optional and honest about what they are:
1. The Odds API (multi-bookmaker 1X2) when ODDS_API_KEY is set.
2. The single-bookmaker odds ESPN publishes on the scoreboard (1X2 + main total line),
   under the provider's real name.

If neither is available the app falls back to *modeled* fair prices and labels them as such.
Credit usage note (The Odds API): one call per league costs markets x regions credits, so
ODDS_REGIONS (default "eu") and ODDS_TTL_SEC (default 1800) keep the bill predictable.
"""
import json
import os
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from difflib import SequenceMatcher

ODDS_KEY = os.environ.get("ODDS_API_KEY", "")
REGIONS = os.environ.get("ODDS_REGIONS", "eu")
TTL = int(os.environ.get("ODDS_TTL_SEC", "1800"))
API = "https://api.the-odds-api.com/v4"

SPORT_KEYS = {
    "eng.1": "soccer_epl", "esp.1": "soccer_spain_la_liga", "ita.1": "soccer_italy_serie_a",
    "ger.1": "soccer_germany_bundesliga", "fra.1": "soccer_france_ligue_one",
    "ned.1": "soccer_netherlands_eredivisie", "por.1": "soccer_portugal_primeira_liga",
    "eng.2": "soccer_efl_champ", "uefa.champions": "soccer_uefa_champs_league",
    "uefa.europa": "soccer_uefa_europa_league", "uefa.europa.conf": "soccer_uefa_europa_conference_league",
}
# The Odds API bookmaker key -> display name (coverage depends on region/plan; verify in your dashboard)
BOOK_NAMES = {
    "pinnacle": "Pinnacle", "betfair_ex_eu": "Betfair Exchange", "betfair_ex_uk": "Betfair Exchange",
    "unibet_eu": "Unibet", "unibet_uk": "Unibet", "williamhill": "William Hill", "draftkings": "DraftKings",
    "fanduel": "FanDuel", "winamax_fr": "Winamax", "winamax_de": "Winamax", "tipico_de": "Tipico",
    "betsson": "Betsson", "bwin": "bwin", "sport888": "888sport", "betclic": "Betclic", "marathonbet": "Marathonbet",
    "nordicbet": "NordicBet", "coolbet": "Coolbet", "matchbook": "Matchbook", "betonlineag": "BetOnline",
}

_cache = {}
_lock = threading.Lock()
_status = {"configured": bool(ODDS_KEY), "lastOk": None, "lastError": None, "books": []}


def configured():
    return bool(ODDS_KEY)


def status():
    with _lock:
        return dict(_status, provider="The Odds API")


def _http_json(url):
    last = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EdgeBetAI/1.0"})
            return json.load(urllib.request.urlopen(req, timeout=15))
        except Exception as e:  # network errors degrade gracefully to modeled prices
            last = e
            time.sleep(0.6 * (attempt + 1))
    raise last


def fetch_league(slug):
    """Cached list of Odds API events (h2h) for an ESPN league slug, or [] if unavailable."""
    key = SPORT_KEYS.get(slug)
    if not ODDS_KEY or not key:
        return []
    now = time.time()
    with _lock:
        hit = _cache.get(slug)
        if hit and now - hit[0] < TTL:
            return hit[1]
    url = f"{API}/sports/{key}/odds/?" + urllib.parse.urlencode(
        {"apiKey": ODDS_KEY, "regions": REGIONS, "markets": "h2h", "oddsFormat": "decimal", "dateFormat": "iso"})
    try:
        data = _http_json(url)
        with _lock:
            _cache[slug] = (now, data)
            _status["lastOk"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            _status["lastError"] = None
            names = sorted({BOOK_NAMES.get(b["key"], b.get("title", b["key"])) for ev in data for b in ev.get("bookmakers", [])})
            _status["books"] = sorted(set(_status["books"]) | set(names))
        return data
    except Exception as e:
        with _lock:
            _status["lastError"] = str(e)[:140]
            _cache[slug] = (now - TTL + 120, hit[1] if hit else [])  # retry in 2 minutes, keep stale data
        return hit[1] if hit else []


# ------------------------------------------------------------------ matching
_NOISE = re.compile(r"\b(fc|cf|ac|as|sc|ssc|afc|cd|ud|sv|fk|rc|us|ogc|real|club|de|calcio)\b")


def norm(name):
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = _NOISE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def _same(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.82


def match_event(events, home, away, kickoff_iso):
    try:
        ko = datetime.fromisoformat(kickoff_iso.replace("Z", "+00:00"))
    except Exception:
        ko = None
    for ev in events:
        if not (_same(ev.get("home_team"), home) and _same(ev.get("away_team"), away)):
            continue
        if ko:
            try:
                ct = datetime.fromisoformat(ev["commence_time"].replace("Z", "+00:00"))
                if abs((ct - ko).total_seconds()) > 12 * 3600:
                    continue
            except Exception:
                pass
        return ev
    return None


def books_1x2(ev, home, away):
    """{book: {home, draw, away, updated}} from an Odds API event (only books with all 3 prices)."""
    out = {}
    for b in ev.get("bookmakers", []):
        mk = next((m for m in b.get("markets", []) if m.get("key") == "h2h"), None)
        if not mk:
            continue
        px = {}
        for o in mk.get("outcomes", []):
            if o["name"] == "Draw":
                px["draw"] = o["price"]
            elif _same(o["name"], home):
                px["home"] = o["price"]
            elif _same(o["name"], away):
                px["away"] = o["price"]
        if len(px) == 3:
            name = BOOK_NAMES.get(b["key"], b.get("title", b["key"]))
            px["updated"] = b.get("last_update")
            out[name] = px
    return out


def live_for_fixture(fx):
    """Collect every real price we hold for a football fixture.

    Returns {"x2": {book: {home,draw,away,updated}}, "total": {line, over, under, book} | None, "asOf": iso}
    """
    asof = datetime.now(timezone.utc).isoformat(timespec="seconds")
    x2, total = {}, None
    ev = None
    if ODDS_KEY:
        ev = match_event(fetch_league(fx.get("league")), fx["home"]["name"], fx["away"]["name"], fx.get("date", ""))
        if ev:
            x2.update(books_1x2(ev, fx["home"]["name"], fx["away"]["name"]))
    o = fx.get("odds")
    if o:
        book = o.get("book") or "ESPN"
        if book not in x2:
            x2[book] = dict(home=o["h"], draw=o["d"], away=o["a"], updated=asof)
        if o.get("line") and o.get("over") and o.get("under"):
            total = dict(line=o["line"], over=o["over"], under=o["under"], book=book, updated=asof)
    return {"x2": x2, "total": total, "asOf": asof}


def prices_for_pick(label, hn, an, live):
    """Real prices for a pick label, or [] when the pick is not a 1X2 / main-total market.

    Each entry: name, price, updated, vigPct, noVigProb (from that book's own overround).
    """
    if not live:
        return []
    res = []
    side = {f"{hn} to win": "home", "Draw": "draw", f"{an} to win": "away"}.get(label)
    if side:
        for name, px in live["x2"].items():
            inv = sum(1.0 / px[k] for k in ("home", "draw", "away"))
            res.append(dict(name=name, price=px[side], updated=px.get("updated"),
                            vigPct=round((inv - 1) * 100, 1), noVigProb=round((1.0 / px[side]) / inv, 4)))
    t = live.get("total")
    if t:
        m = re.fullmatch(r"(Over|Under) ([0-9.]+) goals", label)
        if m and abs(float(m.group(2)) - float(t["line"])) < 1e-9:
            price = t["over"] if m.group(1) == "Over" else t["under"]
            inv = 1.0 / t["over"] + 1.0 / t["under"]
            res.append(dict(name=t["book"], price=price, updated=t.get("updated"),
                            vigPct=round((inv - 1) * 100, 1), noVigProb=round((1.0 / price) / inv, 4)))
    res.sort(key=lambda r: -r["price"])
    return res

