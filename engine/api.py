"""Routing for /api/v1/*. Pure functions over a provider object so server.py stays a thin HTTP layer.

provider must expose: events() -> list, event(id) -> dict|None, meta() -> dict, suite() -> dict,
backtest() -> dict, price_status() -> dict.
"""
from http.cookies import SimpleCookie

from engine import accounts, feed, store
from engine.accounts import AuthError

PROVIDER = None
SESSION_COOKIE = "eb_session"
DEMO_COOKIE = "eb_demo_tier"


class Resp:
    def __init__(self, body, status=200, cookies=None, raw=False):
        self.body, self.status, self.cookies, self.raw = body, status, cookies or [], raw


def err(message, code, status):
    return Resp({"error": message, "code": code}, status)


def parse_cookies(header):
    c = SimpleCookie()
    try:
        c.load(header or "")
    except Exception:
        return {}
    return {k: v.value for k, v in c.items()}


def _cookie(name, value, max_age, secure=False):
    s = f"{name}={value}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"
    return s + ("; Secure" if secure else "")


def context(cookies):
    user = accounts.user_from_token(cookies.get(SESSION_COOKIE))
    tier = accounts.effective_tier(user, cookies.get(DEMO_COOKIE))
    return user, tier


def _me(user, tier):
    return {"user": accounts.public_user(user), "tier": tier, "demoMode": accounts.DEMO_MODE}


def handle(method, path, qs, body, cookies, ip="-", raw=b"", headers=None, secure=False):
    """Return a Resp for any /api/v1 route, or None if the path is not an API v1 route."""
    if not path.startswith("/api/v1/"):
        return None
    route = path[len("/api/v1/"):].strip("/")
    user, tier = context(cookies)
    try:
        return _dispatch(method, route, qs, body or {}, cookies, user, tier, ip, raw, headers or {}, secure)
    except AuthError as e:
        return err(e.message, e.code, e.status)


def _need_user(user):
    if user is None:
        raise AuthError("Accedi per usare questa funzione.", "auth_required", 401)
    return user


def _dispatch(method, route, qs, body, cookies, user, tier, ip, raw, headers, secure):
    P = PROVIDER
    # ---------------------------------------------------------------- read-only
    if method == "GET" and route == "feed":
        return Resp(feed.build_feed(P.events(), tier, P.meta(tier)))
    if method == "GET" and route.startswith("detail/"):
        eid = route.split("/", 1)[1]
        ev = P.event(eid)
        if ev is None:
            return err("Evento non trovato.", "not_found", 404)
        rows = {r["id"]: r for r in feed.build_rows([ev], "pro")}
        if tier == "free":
            # the lock decision depends on the rank inside the full feed, not on this event alone
            full = {r["id"]: r for r in feed.build_rows(P.events(), tier)}
            if full.get(eid, {}).get("locked", True):
                return err("Questa selezione e riservata ai piani Pro e VIP.", "upgrade_required", 403)
        elif eid not in rows:
            return err("Evento non piu disponibile.", "not_found", 404)
        return Resp(feed.build_detail(ev, tier))
    if method == "GET" and route == "ledger":
        return Resp(feed.build_ledger())
    if method == "GET" and route == "backtest":
        return Resp(P.backtest())
    if method == "GET" and route == "method":
        return Resp(feed.build_method(P.price_status(), P.backtest()))
    if method == "GET" and route == "premium":
        return Resp(feed.build_premium(P.suite(), tier))
    if method == "GET" and route == "me":
        return Resp(_me(user, tier))

    # --------------------------------------------------------------------- auth
    if method == "POST" and route == "auth/register":
        uid = accounts.register(body.get("email"), body.get("password"), ip)
        tok = accounts.new_session(uid)
        row = accounts.user_from_token(tok)
        return Resp({"user": accounts.public_user(row)}, 200,
                    [_cookie(SESSION_COOKIE, tok, accounts.SESSION_DAYS * 86400, secure)])
    if method == "POST" and route == "auth/login":
        uid = accounts.login(body.get("email"), body.get("password"), ip)
        tok = accounts.new_session(uid)
        row = accounts.user_from_token(tok)
        return Resp({"user": accounts.public_user(row)}, 200,
                    [_cookie(SESSION_COOKIE, tok, accounts.SESSION_DAYS * 86400, secure)])
    if method == "POST" and route == "auth/guest":
        uid = accounts.create_guest()
        tok = accounts.new_session(uid)
        row = accounts.user_from_token(tok)
        return Resp({"user": accounts.public_user(row)}, 200,
                    [_cookie(SESSION_COOKIE, tok, accounts.SESSION_DAYS * 86400, secure)])
    if method == "POST" and route == "auth/logout":
        accounts.end_session(cookies.get(SESSION_COOKIE))
        return Resp({"ok": True}, 200, [_cookie(SESSION_COOKIE, "", 0, secure), _cookie(DEMO_COOKIE, "", 0, secure)])
    if method == "POST" and route == "demo/tier":
        if not accounts.DEMO_MODE:
            raise AuthError("Modalita demo disattivata.", "demo_disabled", 403)
        t = body.get("tier")
        if t not in accounts.TIERS:
            raise AuthError("Piano non valido.", "invalid_input", 400)
        return Resp({"tier": t}, 200, [_cookie(DEMO_COOKIE, t, 30 * 86400, secure)])

    # ------------------------------------------------------------------ billing
    if method == "POST" and route == "billing/checkout":
        url = accounts.create_checkout(user, body.get("plan"))
        return Resp({"url": url})
    if method == "POST" and route == "billing/webhook":
        import json
        if not accounts.verify_stripe_signature(raw, headers.get("Stripe-Signature", "")):
            return err("Firma non valida.", "invalid_signature", 400)
        try:
            evt = json.loads(raw.decode("utf-8"))
        except Exception:
            return err("Payload non valido.", "invalid_json", 400)
        accounts.handle_stripe_event(evt)
        return Resp({"received": True})

    # --------------------------------------------------------------------- bets
    if route == "bets" and method == "GET":
        u = _need_user(user)
        return Resp({"bets": accounts.list_bets(u["id"]), "stats": store.bet_stats(u["id"]),
                     "limit": accounts.FREE_BET_LIMIT if tier == "free" else None, "tier": tier})
    if route == "bets" and method == "POST":
        u = _need_user(user)
        return Resp({"bet": accounts.add_bet(u["id"], tier, body)})
    if route.startswith("bets/") and method in ("PATCH", "DELETE"):
        u = _need_user(user)
        bid = route.split("/", 1)[1]
        if not bid.isdigit():
            return err("Identificativo non valido.", "invalid_input", 400)
        if method == "PATCH":
            bet = accounts.set_bet_result(u["id"], int(bid), body.get("result"))
            return Resp({"bet": bet, "stats": store.bet_stats(u["id"])})
        accounts.delete_bet(u["id"], int(bid))
        return Resp({"ok": True, "stats": store.bet_stats(u["id"])})

    return err("Risorsa non trovata.", "not_found", 404)

