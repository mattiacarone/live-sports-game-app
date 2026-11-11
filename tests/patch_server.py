import re
from pathlib import Path

p = Path(r"c:\Users\Mattia\gameApp\server.py")
t = p.read_text(encoding="utf-8")

# ------------------------------------------------------------------ imports
t = t.replace("import json, math, threading, time, traceback, urllib.parse, urllib.request\n",
              "import gzip, hashlib, json, math, os, threading, time, traceback, urllib.parse, urllib.request\n", 1)
t = re.sub(r"(from engine\.multisport import \([^)]*\)\n)",
           r"\1from engine import api, accounts, store, odds_feed, grading, feed\n", t, count=1)

# ----------------------------------------------------- tier is decided server side
t = t.replace('tier = qs.get("tier", ["pro"])[0].lower()', "tier = self.tier")
t = t.replace('tier = (qs.get("tier", ["pro"])[0] or "pro").lower()', "tier = self.tier")
t = re.sub(r'(\n([ \t]+)(\w+)\["locked"\] = True\n)', r"\1\2_strip_locked(\3)\n", t)

# ------------------------------------------ performance cache with a 6h refresh
t = t.replace('''    with _lock:
        if _state["performance"] is not None:
            return _state["performance"]
''', '''    with _lock:
        if _state["performance"] is not None and time.time() - _state.get("perf_ts", 0) < 6 * 3600:
            return _state["performance"]
''', 1)
t = t.replace('''    with _lock:
        _state["performance"] = perf
''', '''    with _lock:
        _state["performance"] = perf
        _state["perf_ts"] = time.time()
''', 1)

# ----------------------------------------------- football events: honest fields
anchor = "        football_events.append({\n"
live_block = '''        # real prices only: ESPN single-book odds and, if configured, The Odds API
        lp, lmove, lasof, lnote = [], None, None, None
        try:
            fxlike = {"league": m.get("leagueCode"), "home": {"name": m["home"]}, "away": {"name": m["away"]},
                      "date": m["date"], "odds": m.get("odds")}
            live = odds_feed.live_for_fixture(fxlike)
            lasof = live["asOf"]
            lp = odds_feed.prices_for_pick(best["label"], m["home"], m["away"], live)
            for i, b in enumerate(lp):
                mv, _ = store.record_price(f"{m['id']}|{best['label']}|{b['name']}", b["price"], "live")
                if i == 0:
                    lmove = mv
            if live["x2"]:
                bestpx = {}
                for bk, px in live["x2"].items():
                    for side in ("home", "draw", "away"):
                        if side not in bestpx or px[side] > bestpx[side][0]:
                            bestpx[side] = (px[side], bk)
                mp = {"home": probs.get("home", 0), "draw": probs.get("draw", 0), "away": probs.get("away", 0)}
                names = {"home": m["home"], "draw": "X", "away": m["away"]}
                parts, edges = [], []
                for side in ("home", "draw", "away"):
                    pr, bk = bestpx[side]
                    parts.append(f"{names[side]} @{pr:.2f} ({bk}), modello {round(mp[side] * 100)}%")
                    e = mp[side] * pr - 1
                    if e > 0.03:
                        edges.append(f"{names[side]} +{round(e * 100, 1)}%")
                lnote = "Mercato 1X2 live, miglior prezzo: " + " | ".join(parts) + "."
                if edges:
                    lnote += " Vantaggio stimato sul miglior prezzo: " + ", ".join(edges) + "."
        except Exception:
            traceback.print_exc()

'''
t = t.replace(anchor, live_block + anchor, 1)
t = t.replace('            "original_id": m["id"],\n',
              '            "original_id": m["id"],\n'
              '            "league_code": m.get("leagueCode", ""),\n'
              '            "kickoff": m["date"],\n'
              '            "home": m["home"],\n'
              '            "away": m["away"],\n'
              '            "thin": bool(m.get("thin")),\n'
              '            "samples": m.get("samples"),\n'
              '            "live_prices": lp,\n'
              '            "live_move": lmove,\n'
              '            "live_asof": lasof,\n'
              '            "live_x2_note": lnote,\n', 1)
t = re.sub(r'"why": f"\{best\.get\(\'why\', \'\'\)\} [^\n]*\n',
           '"why": best.get("why", ""),\n', t, count=1)

# ----------------------------------------- refresh worker: ledger + grading
t = t.replace('''            safe_scanner = get_global_safe_scanner(all_events, min_prob=0.72)
            premium_suite = generate_mocked_premium_suite(all_events)
''', '''            safe_scanner = get_global_safe_scanner(all_events, min_prob=0.72)
            premium_suite = generate_mocked_premium_suite(all_events)

            try:
                for fev in football_cat:
                    bp = fev["best_pick"]
                    grading.record_pick(fev, dict(label=bp["label"], market=bp.get("market"), prob=bp["prob"],
                                                  fairOdds=bp["fairOdds"]))
                graded = grading.grade_pending()
                store.prune_snapshots()
                if graded:
                    print(f"[LEDGER] graded {graded} predictions")
            except Exception:
                traceback.print_exc()
''', 1)

# --------------------------------------------------------------- Handler class
start = t.index("class Handler(BaseHTTPRequestHandler):")
end = t.index("    def do_GET(self):\n        parsed = urllib.parse.urlparse(self.path)")
handler = '''_HEAVY = ("bookmakers", "all_books", "allBooks", "facts", "stats", "comparison_bars", "market_categories",
          "markets", "vip_insights", "bet_builders", "kelly", "why")


def _strip_locked(d):
    """Server-side paywall: locked items never carry the premium payload."""
    for k in _HEAVY:
        d.pop(k, None)


def _clean(o):
    """JSON must never contain NaN/Infinity."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    return o


PUBLIC_DIR = Path(__file__).parent / "public"
STATIC_TYPES = {".css": "text/css", ".js": "application/javascript", ".svg": "image/svg+xml",
                ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain", ".html": "text/html"}
ALLOWED_ORIGINS = {o.strip() for o in os.environ.get("EDGEBET_ORIGINS", "").split(",") if o.strip()}
SECURE_COOKIES = os.environ.get("EDGEBET_SECURE", "0") == "1"
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
       "base-uri 'self'; form-action 'self'")
_last_manual_refresh = [0.0]


class Provider:
    """Adapter used by engine.api (keeps server state private to this module)."""

    def events(self):
        with _lock:
            return list(_state["multisport_events"])

    def event(self, eid):
        with _lock:
            return next((e for e in _state["multisport_events"] if e["id"] == eid), None)

    def meta(self):
        with _lock:
            loading = _state["loading"] and not _state["analyzed"]
            return dict(updated=_state["updated"], nextSync=_state["next_sync_20m"], syncCycle=_state["sync_cycle"],
                        demoMode=accounts.DEMO_MODE, liveBooks=odds_feed.status().get("books", []), loading=loading,
                        sportNames={k: v["name"] for k, v in SPORTS_CONFIG.items()},
                        sportDesc={k: v["description"] for k, v in SPORTS_CONFIG.items()})

    def suite(self):
        with _lock:
            suite = _state["premium_suite"]
            evs = list(_state["multisport_events"])
        return suite or generate_mocked_premium_suite(evs)

    def backtest(self):
        with _lock:
            perf = _state["performance"]
        if perf is None:
            return {"n": 0, "loading": True, "calibration": [], "byMarket": [], "note": "Backtest in calcolo."}
        return {k: perf.get(k) for k in ("n", "hitRatePct", "avgProbPct", "brier", "logLoss", "calibration",
                                         "byMarket", "range", "note")}

    def price_status(self):
        return odds_feed.status()


api.PROVIDER = Provider()


class Handler(BaseHTTPRequestHandler):
    server_version = "EdgeBetAI/1.0"

    def log_message(self, *a):
        pass

    # ------------------------------------------------------------- plumbing
    def _prepare(self):
        self.cookies = api.parse_cookies(self.headers.get("Cookie"))
        self.user, self.tier = api.context(self.cookies)

    def _cors(self):
        origin = self.headers.get("Origin")
        if origin and origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Vary", "Origin")
        elif not origin and self.path.startswith("/api/") and not self.path.startswith("/api/v1/"):
            self.send_header("Access-Control-Allow-Origin", "*")  # legacy public read-only endpoints

    def send(self, body, status=200, ctype="application/json", cookies=None, cache="no-store"):
        if isinstance(body, (dict, list)):
            b = json.dumps(_clean(body), ensure_ascii=False, allow_nan=False).encode("utf-8")
        elif isinstance(body, str):
            b = body.encode("utf-8")
        else:
            b = body
        etag = None
        if ctype != "application/json" and status == 200 and self.command == "GET":
            etag = '"' + hashlib.md5(b).hexdigest()[:16] + '"'
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Cache-Control", cache)
                self.end_headers()
                return
        enc = None
        if len(b) > 1024 and "gzip" in (self.headers.get("Accept-Encoding") or ""):
            b, enc = gzip.compress(b, 5), "gzip"
        self.send_response(status)
        self.send_header("Content-Type", ctype + "; charset=utf-8" if ctype.startswith(("text/", "application/json", "application/javascript", "image/svg")) else ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", cache)
        self.send_header("Vary", "Accept-Encoding, Cookie, Origin")
        if enc:
            self.send_header("Content-Encoding", enc)
        if etag:
            self.send_header("ETag", etag)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        if ctype == "text/html":
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("X-Frame-Options", "DENY")
        for c in cookies or []:
            self.send_header("Set-Cookie", c)
        self._cors()
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(b)

    def _error(self, message, code, status):
        self.send({"error": message, "code": code}, status)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n > 65536:
            return None, b""
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return {}, raw
        try:
            data = json.loads(raw.decode("utf-8"))
            return (data if isinstance(data, dict) else {}), raw
        except Exception:
            return None, raw

    def _client_ip(self):
        return self.client_address[0] if self.client_address else "-"

    def _serve_api(self, method):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        body, raw = ({}, b"")
        if method in ("POST", "PATCH", "DELETE"):
            body, raw = self._body()
            if body is None and not parsed.path.endswith("/billing/webhook"):
                return self._error("JSON non valido o troppo grande.", "invalid_json", 400)
            body = body or {}
        res = api.handle(method, parsed.path, qs, body, self.cookies, self._client_ip(), raw,
                         dict(self.headers), SECURE_COOKIES)
        if res is None:
            return self._error("Risorsa non trovata.", "not_found", 404)
        self.send(res.body, res.status, cookies=res.cookies)

    def _guard(self, fn, *a):
        try:
            self._prepare()
            fn(*a)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            traceback.print_exc()
            try:
                self._error("Errore interno del server.", "internal_error", 500)
            except Exception:
                pass

    # --------------------------------------------------------------- verbs
    def do_OPTIONS(self):
        self.send_response(204)
        origin = self.headers.get("Origin")
        if origin and origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self):
        self._guard(self._serve_api, "POST")

    def do_PATCH(self):
        self._guard(self._serve_api, "PATCH")

    def do_DELETE(self):
        self._guard(self._serve_api, "DELETE")

    def do_GET(self):
        self._guard(self._get_dispatch)

    def _get_dispatch(self):
        p = urllib.parse.urlparse(self.path).path
        if p.startswith("/api/v1/"):
            return self._serve_api("GET")
        name = p.lstrip("/")
        if name and "/" not in name and "\\\\" not in name and not name.startswith("."):
            f = PUBLIC_DIR / name
            ext = f.suffix.lower()
            if ext in STATIC_TYPES and f.is_file() and f.resolve().parent == PUBLIC_DIR.resolve():
                cache = "no-cache" if name in ("sw.js", "index.html") else "public, max-age=300, must-revalidate"
                return self.send(f.read_bytes(), 200, STATIC_TYPES[ext], cache=cache)
        return self._legacy_get()

'''
t = t[:start] + handler + t[end:].replace("    def do_GET(self):\n        parsed", "    def _legacy_get(self):\n        parsed", 1)

# manual refresh: cooldown against abuse
t = t.replace('''        elif p == "/api/refresh":
            refresh_data(advance_cycle=True)''', '''        elif p == "/api/refresh":
            if time.time() - _last_manual_refresh[0] < 120:
                self._error("Aggiornamento gia richiesto di recente.", "rate_limited", 429)
                return
            _last_manual_refresh[0] = time.time()
            refresh_data(advance_cycle=True)''', 1)

p.write_text(t, encoding="utf-8")
print("server.py patched; Handler lines:", t.count("\n"))

