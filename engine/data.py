"""ESPN public-feed data layer with memory + disk caching.

Completed-match summaries never change, so they are compacted and stored on disk
(cache/ev_<id>.json) — after the first run the app starts in seconds.
"""
import json, threading, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = "https://site.api.espn.com/apis"
CACHE = Path(__file__).resolve().parent.parent / "cache"
CACHE.mkdir(exist_ok=True)
LEAGUES = {
    "eng.1": "Premier League", "esp.1": "La Liga", "ita.1": "Serie A",
    "ger.1": "Bundesliga", "fra.1": "Ligue 1",
    "ned.1": "Eredivisie", "por.1": "Primeira Liga", "eng.2": "Championship",
    "uefa.champions": "Champions League", "uefa.europa": "Europa League",
    "uefa.europa.conf": "Conference League",
}
LEAGUE_META = {
    "eng.1": {"country": "England", "flag": "GB", "tier": 1},
    "esp.1": {"country": "Spain", "flag": "ES", "tier": 1},
    "ita.1": {"country": "Italy", "flag": "IT", "tier": 1},
    "ger.1": {"country": "Germany", "flag": "DE", "tier": 1},
    "fra.1": {"country": "France", "flag": "FR", "tier": 1},
    "ned.1": {"country": "Netherlands", "flag": "NL", "tier": 1},
    "por.1": {"country": "Portugal", "flag": "PT", "tier": 1},
    "eng.2": {"country": "England", "flag": "GB", "tier": 2},
    "uefa.champions": {"country": "Europe", "flag": "EU", "tier": 1},
    "uefa.europa": {"country": "Europe", "flag": "EU", "tier": 1},
    "uefa.europa.conf": {"country": "Europe", "flag": "EU", "tier": 2},
}
HISTORY = 12          # recent competitive matches per team
_mem, _lock = {}, threading.Lock()


def get(url, ttl=600):
    now = time.time()
    with _lock:
        hit = _mem.get(url)
        if hit and now - hit[0] < ttl:
            return hit[1]
    data = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=15))
            break
        except Exception:
            time.sleep(0.6 * (attempt + 1))
    with _lock:
        _mem[url] = (now, data)
    return data


def _num(v):
    if isinstance(v, dict):
        v = v.get("value", v.get("displayValue"))
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _american(v):
    v = _num(str(v).replace("+", "")) if v is not None else None
    if v is None or v == 0:
        return None
    return 1 + (v / 100 if v > 0 else 100 / -v)  # decimal odds


_NAMES_FILE = CACHE / "team_names.json"
try:
    _TEAM_NAMES = json.loads(_NAMES_FILE.read_text("utf-8")) if _NAMES_FILE.exists() else {}
except Exception:
    _TEAM_NAMES = {}


def _record_teams(competitors):
    changed = False
    with _lock:
        for c in competitors or []:
            t = c.get("team") or {}
            tid, nm = str(t.get("id") or ""), t.get("displayName") or t.get("name") or ""
            if tid and nm and _TEAM_NAMES.get(tid) != nm:
                _TEAM_NAMES[tid] = nm
                changed = True
        if changed:
            try:
                _NAMES_FILE.write_text(json.dumps(_TEAM_NAMES, ensure_ascii=False), "utf-8")
            except Exception:
                pass


def team_name(tid):
    return _TEAM_NAMES.get(str(tid), f"Club #{tid}")


def all_cached_summaries():
    """Load all compacted completed match summaries from disk sorted chronologically."""
    out = []
    for f in CACHE.glob("ev_*.json"):
        try:
            d = json.loads(f.read_text("utf-8"))
            if d and "teams" in d and len(d["teams"]) == 2:
                out.append(d)
        except Exception:
            pass
    out.sort(key=lambda x: x.get("date", ""))
    return out


# ---------------------------------------------------------------- fixtures
def fixtures(days=7):
    today = datetime.now(timezone.utc).date()
    jobs = [(lg, (today + timedelta(d)).strftime("%Y%m%d")) for lg in LEAGUES for d in range(days)]
    with ThreadPoolExecutor(10) as ex:
        boards = list(ex.map(lambda j: get(f"{BASE}/site/v2/sports/soccer/{j[0]}/scoreboard?dates={j[1]}"), jobs))
    out, seen = [], set()
    for (lg, _), b in zip(jobs, boards):
        meta = LEAGUE_META.get(lg, {"country": "Europe", "flag": "🇪🇺", "tier": 1})
        for ev in (b or {}).get("events", []):
            c = ev["competitions"][0]
            _record_teams(c.get("competitors", []))
            if ev["id"] in seen or c["status"]["type"]["state"] != "pre":
                continue
            seen.add(ev["id"])
            cs = {x["homeAway"]: x for x in c["competitors"]}
            out.append(dict(
                id=ev["id"], date=ev["date"], league=lg, leagueName=LEAGUES[lg],
                country=meta["country"], flag=meta["flag"],
                home=dict(id=cs["home"]["team"]["id"], name=cs["home"]["team"]["displayName"], short=cs["home"]["team"].get("abbreviation", "")),
                away=dict(id=cs["away"]["team"]["id"], name=cs["away"]["team"]["displayName"], short=cs["away"]["team"].get("abbreviation", "")),
                venue=(c.get("venue") or {}).get("fullName", ""),
                odds=_odds(c),
            ))
    out.sort(key=lambda f: f["date"])
    return out


def _odds(c):
    o = (c.get("odds") or [None])[0]
    if not o:
        return None
    try:
        ml = o["moneyline"]
        raw_book = o.get("provider", {}).get("displayName", "") or "ESPN"
        # keep the real provider name: never relabel a price as another bookmaker's
        book = raw_book
        r = dict(book=book,
                 h=_american(ml["home"]["close"]["odds"]), d=_american(ml["draw"]["close"]["odds"]),
                 a=_american(ml["away"]["close"]["odds"]), line=_num(o.get("overUnder")))
        t = o.get("total") or {}
        r["over"] = _american(t.get("over", {}).get("close", {}).get("odds"))
        r["under"] = _american(t.get("under", {}).get("close", {}).get("odds"))
        return r if all((r["h"], r["d"], r["a"])) else None
    except Exception:
        return None


# ---------------------------------------------------------------- history
def team_history(tid, leagues):
    evs = {}
    srcs = [get(f"{BASE}/site/v2/sports/soccer/all/teams/{tid}/schedule", 3600)]
    if not srcs[0]:
        srcs = [get(f"{BASE}/site/v2/sports/soccer/{lg}/teams/{tid}/schedule", 3600) for lg in leagues]
    for s in srcs:
        for e in (s or {}).get("events", []):
            comp = e["competitions"][0]
            _record_teams(comp.get("competitors", []))
            slug = (e.get("league") or {}).get("slug") or ""
            if not comp["status"]["type"].get("completed") or "friendly" in slug or not slug:
                continue
            evs[e["id"]] = (e["date"], slug)
    return sorted(evs.items(), key=lambda kv: kv[1][0])[-HISTORY:]


def summary(eid, slug):
    f = CACHE / f"ev_{eid}.json"
    if f.exists():
        return json.loads(f.read_text("utf-8"))
    d = get(f"{BASE}/site/v2/sports/soccer/{slug}/summary?event={eid}", 3600)
    s = _compact(d, eid, slug) if d else None
    if s:
        f.write_text(json.dumps(s), "utf-8")
    return s


def _compact(d, eid, slug):
    try:
        comp = d["header"]["competitions"][0]
        if not comp["status"]["type"].get("completed"):
            return None
        _record_teams(comp.get("competitors", []))
        teams = {}
        for c in comp["competitors"]:
            ls = c.get("linescores") or []
            nm = (c.get("team") or {}).get("displayName") or ""
            teams[c["id"]] = dict(home=c["homeAway"] == "home", name=nm, goals=_num(c.get("score")) or 0,
                                  ht=_num(ls[0].get("displayValue")) if ls else None, stats={}, players=[])
        for t in d.get("boxscore", {}).get("teams", []):
            tid = t["team"]["id"]
            if tid in teams:
                teams[tid]["stats"] = {x["name"]: _num(x.get("displayValue")) for x in t.get("statistics", [])}
        for r in d.get("rosters", []):
            tid = r.get("team", {}).get("id")
            if tid not in teams:
                continue
            for p in r.get("roster", []):
                st = {x["name"]: _num(x.get("displayValue")) or 0 for x in p.get("stats", [])}
                teams[tid]["players"].append(dict(
                    id=p.get("athlete", {}).get("id"), name=p.get("athlete", {}).get("displayName", "?"),
                    pos=(p.get("position") or {}).get("abbreviation", ""), start=bool(p.get("starter")),
                    g=st.get("totalGoals", 0), a=st.get("goalAssists", 0), sh=st.get("totalShots", 0),
                    sot=st.get("shotsOnTarget", 0), y=st.get("yellowCards", 0), r=st.get("redCards", 0),
                    app=st.get("appearances", 0)))
        if len(teams) != 2 or not all(t["stats"] for t in teams.values()):
            return None
        return dict(id=eid, date=comp.get("date", ""), league=slug, teams=teams)
    except Exception:
        return None


def lineup(eid, slug):
    """Confirmed starters if ESPN has published them (usually ~1h before kick-off)."""
    d = get(f"{BASE}/site/v2/sports/soccer/{slug}/summary?event={eid}", 900)
    out = {}
    for r in (d or {}).get("rosters", []):
        starters = {p.get("athlete", {}).get("id") for p in r.get("roster", []) if p.get("starter")}
        if len(starters) >= 11:
            out[r["team"]["id"]] = starters
    return out


