"""SQLite persistence for EdgeBet AI: odds snapshots, immutable prediction ledger,
users, sessions, entitlements and user bets.

One connection per thread (WAL mode). All writes are short transactions.
"""
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "edgebet.db"

_local = threading.local()
_init_lock = threading.Lock()
_ready = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS odds_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    price REAL NOT NULL,
    source TEXT NOT NULL,
    ts REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_snap_key_ts ON odds_snapshots(key, ts);

-- Immutable ledger: pick/prob/fair/kickoff are never updated after insert.
CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    slug TEXT,
    sport TEXT NOT NULL,
    title TEXT NOT NULL,
    home TEXT,
    away TEXT,
    pick TEXT NOT NULL,
    market TEXT,
    prob REAL NOT NULL,
    fair REAL NOT NULL,
    kickoff TEXT NOT NULL,
    published_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    graded_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_pred_status ON predictions(status, kickoff);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    pw_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    guest INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS entitlements (
    user_id INTEGER PRIMARY KEY,
    tier TEXT NOT NULL DEFAULT 'free',
    status TEXT NOT NULL DEFAULT 'active',
    expires_at TEXT,
    source TEXT NOT NULL DEFAULT 'none',
    stripe_customer TEXT,
    stripe_sub TEXT
);

CREATE TABLE IF NOT EXISTS bets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    title TEXT NOT NULL,
    pick TEXT NOT NULL,
    odds REAL NOT NULL,
    stake REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    sport TEXT,
    pick_id TEXT,
    result TEXT NOT NULL DEFAULT 'open',
    profit REAL NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_bets_user ON bets(user_id, id);
"""


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def conn():
    """Thread-local connection (creates the schema on first use)."""
    global _ready
    c = getattr(_local, "c", None)
    if c is None:
        c = sqlite3.connect(str(DB_PATH), timeout=15, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA foreign_keys=ON")
        _local.c = c
    if not _ready:
        with _init_lock:
            if not _ready:
                c.executescript(SCHEMA)
                _ready = True
    return c


# --------------------------------------------------------------- odds history
def record_price(key, price, source="live"):
    """Store a real price observation and return (movement_pct, first_price) over the last 6h.

    movement_pct is None until a second observation exists, so nothing is invented.
    """
    c = conn()
    ts = time.time()
    last = c.execute("SELECT price, ts FROM odds_snapshots WHERE key=? ORDER BY ts DESC LIMIT 1", (key,)).fetchone()
    # one observation per ~10 minutes is enough; avoid duplicates on rapid refreshes
    if not last or ts - last["ts"] > 600 or abs(last["price"] - price) > 1e-9:
        c.execute("INSERT INTO odds_snapshots(key, price, source, ts) VALUES (?,?,?,?)", (key, float(price), source, ts))
    first = c.execute("SELECT price FROM odds_snapshots WHERE key=? AND ts>=? ORDER BY ts ASC LIMIT 1",
                      (key, ts - 6 * 3600)).fetchone()
    n = c.execute("SELECT COUNT(*) n FROM odds_snapshots WHERE key=? AND ts>=?", (key, ts - 6 * 3600)).fetchone()["n"]
    if not first or n < 2 or first["price"] <= 0:
        return None, float(price)
    return round((price - first["price"]) / first["price"] * 100, 1), float(first["price"])


def prune_snapshots(days=14):
    conn().execute("DELETE FROM odds_snapshots WHERE ts < ?", (time.time() - days * 86400,))


# ----------------------------------------------------------------- predictions
def add_prediction(pid, event_id, slug, sport, title, home, away, pick, market, prob, fair, kickoff):
    """Insert once; an existing id is never modified (immutable ledger)."""
    cur = conn().execute(
        "INSERT OR IGNORE INTO predictions(id,event_id,slug,sport,title,home,away,pick,market,prob,fair,kickoff,published_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (pid, str(event_id), slug, sport, title, home, away, pick, market, float(prob), float(fair), kickoff, now_iso()))
    return cur.rowcount == 1


def pending_predictions(before_iso):
    return conn().execute(
        "SELECT * FROM predictions WHERE status='pending' AND kickoff < ? ORDER BY kickoff", (before_iso,)).fetchall()


def grade_prediction(pid, status, result):
    conn().execute("UPDATE predictions SET status=?, result=?, graded_at=? WHERE id=? AND status='pending'",
                   (status, result, now_iso(), pid))


def ledger_rows(limit=60):
    return conn().execute("SELECT * FROM predictions ORDER BY kickoff DESC LIMIT ?", (limit,)).fetchall()


def settled_predictions():
    return conn().execute("SELECT prob, status, sport, market, published_at FROM predictions WHERE status IN ('won','lost')").fetchall()


def pending_count():
    return conn().execute("SELECT COUNT(*) n FROM predictions WHERE status='pending'").fetchone()["n"]


def first_prediction_date():
    r = conn().execute("SELECT MIN(published_at) d FROM predictions").fetchone()
    return (r["d"] or "")[:10] or None


# ------------------------------------------------------------------------ bets
def bet_to_dict(r):
    return dict(id=r["id"], createdAt=r["created_at"], title=r["title"], pick=r["pick"], odds=r["odds"],
                stake=r["stake"], currency=r["currency"], sport=r["sport"], result=r["result"],
                profit=round(r["profit"], 2))


def bet_stats(user_id):
    rows = conn().execute("SELECT * FROM bets WHERE user_id=?", (user_id,)).fetchall()
    settled = [r for r in rows if r["result"] in ("won", "lost")]
    staked = sum(r["stake"] for r in settled)
    returned = sum(r["stake"] + r["profit"] for r in settled)
    profit = sum(r["profit"] for r in settled)
    wins = sum(1 for r in settled if r["result"] == "won")
    return dict(count=len(rows), open=sum(1 for r in rows if r["result"] == "open"),
                staked=round(staked, 2), returned=round(returned, 2), profit=round(profit, 2),
                roiPct=round(profit / staked * 100, 1) if staked else None,
                hitRatePct=round(wins / len(settled) * 100, 1) if settled else None)

