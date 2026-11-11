"""Accounts, sessions, entitlements and Stripe billing for EdgeBet AI.

Entitlement model (AGENT.md): tier free|pro|vip, status active|trialing|past_due|canceled,
expires_at, source stripe|apple|google|demo|none. The tier is always derived server side.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from engine import store

SESSION_DAYS = 30
PBKDF2_ROUNDS = 200_000
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")
TIERS = ("free", "pro", "vip")
FREE_BET_LIMIT = 10

DEMO_MODE = os.environ.get("EDGEBET_DEMO", "1") == "1"
STRIPE_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PUBLIC_URL = os.environ.get("EDGEBET_PUBLIC_URL", "http://localhost:8080")
# plan -> (tier, Stripe price id from env)
PLANS = {
    "pro_monthly": ("pro", "STRIPE_PRICE_PRO_MONTHLY"),
    "pro_annual": ("pro", "STRIPE_PRICE_PRO_ANNUAL"),
    "vip_monthly": ("vip", "STRIPE_PRICE_VIP_MONTHLY"),
    "vip_annual": ("vip", "STRIPE_PRICE_VIP_ANNUAL"),
}


class AuthError(Exception):
    def __init__(self, message, code, status=400):
        super().__init__(message)
        self.message, self.code, self.status = message, code, status


# ------------------------------------------------------------------ passwords
def _hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ROUNDS).hex()


_attempts = {}


def _rate_limit(ip, limit=8, window=60):
    now = time.time()
    hits = [t for t in _attempts.get(ip, []) if now - t < window]
    if len(hits) >= limit:
        raise AuthError("Troppi tentativi, riprova tra un minuto.", "rate_limited", 429)
    hits.append(now)
    _attempts[ip] = hits


def _user_dict(row):
    ent = entitlement(row["id"])
    return dict(email=row["email"] if not row["guest"] else "Ospite", guest=bool(row["guest"]),
                tier=ent["tier"], status=ent["status"], expiresAt=ent["expiresAt"], source=ent["source"])


def register(email, password, ip="-"):
    _rate_limit(ip)
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(password or "") < 8 or len(password) > 200:
        raise AuthError("Email non valida o password sotto gli 8 caratteri.", "invalid_input", 400)
    salt = secrets.token_hex(16)
    c = store.conn()
    try:
        cur = c.execute("INSERT INTO users(email, pw_hash, salt, guest, created_at) VALUES (?,?,?,0,?)",
                        (email, _hash_pw(password, salt), salt, store.now_iso()))
    except Exception:
        raise AuthError("Email gia registrata.", "email_taken", 409)
    uid = cur.lastrowid
    c.execute("INSERT OR IGNORE INTO entitlements(user_id) VALUES (?)", (uid,))
    return uid


def login(email, password, ip="-"):
    _rate_limit(ip)
    row = store.conn().execute("SELECT * FROM users WHERE email=? AND guest=0", ((email or "").strip().lower(),)).fetchone()
    if not row or not hmac.compare_digest(row["pw_hash"], _hash_pw(password or "", row["salt"])):
        raise AuthError("Credenziali non valide.", "invalid_credentials", 401)
    return row["id"]


def create_guest():
    if not DEMO_MODE:
        raise AuthError("Modalita demo disattivata.", "demo_disabled", 403)
    tok = secrets.token_hex(6)
    salt = secrets.token_hex(16)
    c = store.conn()
    cur = c.execute("INSERT INTO users(email, pw_hash, salt, guest, created_at) VALUES (?,?,?,1,?)",
                    (f"guest-{tok}@demo.local", secrets.token_hex(16), salt, store.now_iso()))
    c.execute("INSERT OR IGNORE INTO entitlements(user_id) VALUES (?)", (cur.lastrowid,))
    return cur.lastrowid


# ------------------------------------------------------------------- sessions
def _th(token):
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(user_id):
    token = secrets.token_urlsafe(32)
    store.conn().execute("INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?,?,?)",
                         (_th(token), user_id, time.time() + SESSION_DAYS * 86400))
    return token


def end_session(token):
    if token:
        store.conn().execute("DELETE FROM sessions WHERE token_hash=?", (_th(token),))


def user_from_token(token):
    if not token:
        return None
    c = store.conn()
    row = c.execute("SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?",
                    (_th(token), time.time())).fetchone()
    return row


def public_user(row):
    return _user_dict(row) if row else None


# --------------------------------------------------------------- entitlements
def entitlement(user_id):
    r = store.conn().execute("SELECT * FROM entitlements WHERE user_id=?", (user_id,)).fetchone()
    if not r:
        return dict(tier="free", status="active", expiresAt=None, source="none")
    return dict(tier=r["tier"], status=r["status"], expiresAt=r["expires_at"], source=r["source"])


def effective_tier(user_row, demo_cookie=None):
    """Tier from the paid/demo entitlement, else the demo cookie (demo mode only), else free."""
    if user_row is not None:
        ent = entitlement(user_row["id"])
        active = ent["status"] in ("active", "trialing", "past_due")
        if active and ent["tier"] in TIERS:
            exp = ent["expiresAt"]
            if not exp or exp > datetime.now(timezone.utc).isoformat():
                if ent["tier"] != "free":
                    return ent["tier"]
    if DEMO_MODE and demo_cookie in TIERS:
        return demo_cookie
    return "free"


def set_entitlement(user_id, tier, status="active", expires_at=None, source="stripe", customer=None, sub=None):
    c = store.conn()
    c.execute("INSERT OR IGNORE INTO entitlements(user_id) VALUES (?)", (user_id,))
    c.execute("UPDATE entitlements SET tier=?, status=?, expires_at=?, source=?, "
              "stripe_customer=COALESCE(?, stripe_customer), stripe_sub=COALESCE(?, stripe_sub) WHERE user_id=?",
              (tier, status, expires_at, source, customer, sub, user_id))


# -------------------------------------------------------------------- billing
def billing_configured():
    return bool(STRIPE_KEY)


def create_checkout(user_row, plan):
    if plan not in PLANS:
        raise AuthError("Piano non valido.", "invalid_input", 400)
    if not STRIPE_KEY:
        raise AuthError("Pagamenti non ancora attivi.", "billing_not_configured", 501)
    if user_row is None or user_row["guest"]:
        raise AuthError("Accedi con un account per abbonarti.", "auth_required", 401)
    tier, env_name = PLANS[plan]
    price = os.environ.get(env_name, "")
    if not price:
        raise AuthError("Prezzo Stripe non configurato per questo piano.", "billing_not_configured", 501)
    form = {
        "mode": "subscription",
        "line_items[0][price]": price,
        "line_items[0][quantity]": "1",
        "success_url": f"{PUBLIC_URL}/#/pro?checkout=ok",
        "cancel_url": f"{PUBLIC_URL}/#/pro?checkout=cancel",
        "client_reference_id": str(user_row["id"]),
        "customer_email": user_row["email"],
        "metadata[user_id]": str(user_row["id"]),
        "metadata[tier]": tier,
        "subscription_data[metadata][user_id]": str(user_row["id"]),
        "subscription_data[metadata][tier]": tier,
        "allow_promotion_codes": "true",
    }
    req = urllib.request.Request("https://api.stripe.com/v1/checkout/sessions",
                                 data=urllib.parse.urlencode(form).encode(),
                                 headers={"Authorization": f"Bearer {STRIPE_KEY}",
                                          "Content-Type": "application/x-www-form-urlencoded"})
    try:
        data = json.load(urllib.request.urlopen(req, timeout=15))
    except urllib.error.HTTPError as e:
        raise AuthError("Stripe ha rifiutato la richiesta.", "billing_error", 502) from e
    except Exception as e:
        raise AuthError("Stripe non raggiungibile.", "billing_error", 502) from e
    return data.get("url")


def verify_stripe_signature(payload: bytes, header: str, secret=None, tolerance=300, now=None):
    secret = secret if secret is not None else STRIPE_WEBHOOK_SECRET
    if not secret or not header:
        return False
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    ts = parts.get("t")
    sig = [v for k, v in (p.split("=", 1) for p in header.split(",") if "=" in p) if k == "v1"]
    if not ts or not sig:
        return False
    try:
        if abs((now or time.time()) - int(ts)) > tolerance:
            return False
    except ValueError:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sig)


def handle_stripe_event(evt):
    """Apply a verified Stripe event to entitlements. Returns True if it changed anything."""
    typ = evt.get("type", "")
    obj = (evt.get("data") or {}).get("object") or {}
    meta = obj.get("metadata") or {}
    uid = meta.get("user_id") or obj.get("client_reference_id")
    if not uid or not str(uid).isdigit():
        return False
    uid = int(uid)
    if typ == "checkout.session.completed":
        set_entitlement(uid, meta.get("tier", "pro"), "active", None, "stripe", obj.get("customer"), obj.get("subscription"))
        return True
    if typ in ("customer.subscription.updated", "customer.subscription.created"):
        status = obj.get("status", "active")
        mapped = {"active": "active", "trialing": "trialing", "past_due": "past_due"}.get(status, "canceled")
        end = obj.get("current_period_end")
        exp = datetime.fromtimestamp(end, timezone.utc).isoformat() if end else None
        set_entitlement(uid, meta.get("tier", "pro") if mapped != "canceled" else "free", mapped, exp, "stripe",
                        obj.get("customer"), obj.get("id"))
        return True
    if typ == "customer.subscription.deleted":
        set_entitlement(uid, "free", "canceled", None, "stripe", obj.get("customer"), obj.get("id"))
        return True
    return False


# ------------------------------------------------------------------------ bets
def list_bets(user_id):
    rows = store.conn().execute("SELECT * FROM bets WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    return [store.bet_to_dict(r) for r in rows]


def add_bet(user_id, tier, data):
    try:
        odds = float(data.get("odds"))
        stake = float(data.get("stake"))
    except (TypeError, ValueError):
        raise AuthError("Quota e puntata devono essere numeri.", "invalid_input", 400)
    title = str(data.get("title") or "").strip()[:140]
    pick = str(data.get("pick") or "").strip()[:140]
    if not title or not pick or not (1.01 <= odds <= 1000) or not (0 < stake <= 1_000_000):
        raise AuthError("Dati puntata non validi.", "invalid_input", 400)
    n = store.conn().execute("SELECT COUNT(*) n FROM bets WHERE user_id=?", (user_id,)).fetchone()["n"]
    if tier == "free" and n >= FREE_BET_LIMIT:
        raise AuthError("Limite di 10 puntate del piano gratuito raggiunto.", "limit_reached", 402)
    cur = store.conn().execute(
        "INSERT INTO bets(user_id,created_at,title,pick,odds,stake,currency,sport,pick_id) VALUES (?,?,?,?,?,?,?,?,?)",
        (user_id, store.now_iso(), title, pick, odds, stake, str(data.get("currency") or "EUR")[:3].upper(),
         str(data.get("sport") or "")[:20], str(data.get("pickId") or "")[:80]))
    return store.bet_to_dict(store.conn().execute("SELECT * FROM bets WHERE id=?", (cur.lastrowid,)).fetchone())


def set_bet_result(user_id, bet_id, result):
    if result not in ("won", "lost", "void", "open"):
        raise AuthError("Risultato non valido.", "invalid_input", 400)
    r = store.conn().execute("SELECT * FROM bets WHERE id=? AND user_id=?", (bet_id, user_id)).fetchone()
    if not r:
        raise AuthError("Puntata non trovata.", "not_found", 404)
    profit = round(r["stake"] * (r["odds"] - 1), 2) if result == "won" else (-r["stake"] if result == "lost" else 0.0)
    store.conn().execute("UPDATE bets SET result=?, profit=? WHERE id=?", (result, profit, bet_id))
    return store.bet_to_dict(store.conn().execute("SELECT * FROM bets WHERE id=?", (bet_id,)).fetchone())


def delete_bet(user_id, bet_id):
    cur = store.conn().execute("DELETE FROM bets WHERE id=? AND user_id=?", (bet_id, user_id))
    if cur.rowcount == 0:
        raise AuthError("Puntata non trovata.", "not_found", 404)

