"""Pick ledger helpers: decide whether a model label can be graded, and grade it from a final box score.

The ledger only records picks that `compile_label` understands, so every recorded pick can be settled
objectively once the match is over (no manual intervention, no ambiguity).
"""
import re
from datetime import datetime, timedelta, timezone

from engine import store
from engine.data import summary


def _cmp(op, a, x):
    return a > x if op == "over" else a < x


def compile_label(label, hn, an):
    """Return f(S)->bool for a model label, or None if the label is not gradeable.

    S keys: H, A (goals), HH, AH (half-time goals), ch, ca (corners), cardsh, cardsa, soth, sota, shh, sha.
    """
    L = label.strip()
    if L == f"{hn} to win":
        return lambda S: S["H"] > S["A"]
    if L == f"{an} to win":
        return lambda S: S["A"] > S["H"]
    if L == "Draw":
        return lambda S: S["H"] == S["A"]
    if L == f"{hn} or draw":
        return lambda S: S["H"] >= S["A"]
    if L == f"{an} or draw":
        return lambda S: S["A"] >= S["H"]
    if L == f"{hn} or {an}":
        return lambda S: S["H"] != S["A"]
    if L == "Both teams to score":
        return lambda S: S["H"] > 0 and S["A"] > 0
    if L == "Both teams to score: No":
        return lambda S: S["H"] == 0 or S["A"] == 0
    if L == f"{hn} clean sheet":
        return lambda S: S["A"] == 0
    if L == f"{an} clean sheet":
        return lambda S: S["H"] == 0

    m = re.fullmatch(r"(Over|Under) ([0-9.]+) (goals|corners|cards|shots on target|total shots)", L)
    if m:
        op, x, what = m.group(1).lower(), float(m.group(2)), m.group(3)
        tot = {"goals": lambda S: S["H"] + S["A"], "corners": lambda S: S["ch"] + S["ca"],
               "cards": lambda S: S["cardsh"] + S["cardsa"], "shots on target": lambda S: S["soth"] + S["sota"],
               "total shots": lambda S: S["shh"] + S["sha"]}[what]
        return lambda S: _cmp(op, tot(S), x)

    for name, side in ((hn, "h"), (an, "a")):
        pre = re.escape(name)
        m = re.fullmatch(pre + r" (over|under) ([0-9.]+) (goals|corners|cards|shots on target|shots)", L)
        if m:
            op, x, what = m.group(1), float(m.group(2)), m.group(3)
            keys = {"goals": ("H", "A"), "corners": ("ch", "ca"), "cards": ("cardsh", "cardsa"),
                    "shots on target": ("soth", "sota"), "shots": ("shh", "sha")}[what]
            k = keys[0] if side == "h" else keys[1]
            return lambda S, k=k, op=op, x=x: _cmp(op, S[k], x)

    m = re.fullmatch(r"1st half (over|under) ([0-9.]+) goals", L)
    if m:
        op, x = m.group(1), float(m.group(2))
        return lambda S: S["HH"] is not None and _cmp(op, S["HH"] + S["AH"], x)
    return None


def box_score(summ, hn, an):
    """Normalise a compacted ESPN summary into the S dict used by compiled labels."""
    teams = list(summ["teams"].values())
    home = next((t for t in teams if t.get("home")), None)
    away = next((t for t in teams if not t.get("home")), None)
    if not home or not away:
        return None

    def st(t, k):
        return int((t.get("stats") or {}).get(k) or 0)

    hh = home.get("ht")
    ah = away.get("ht")
    return dict(H=int(home["goals"]), A=int(away["goals"]),
                HH=int(hh) if hh is not None and ah is not None else None, AH=int(ah) if ah is not None else None,
                ch=st(home, "wonCorners"), ca=st(away, "wonCorners"),
                cardsh=st(home, "yellowCards") + st(home, "redCards"), cardsa=st(away, "yellowCards") + st(away, "redCards"),
                soth=st(home, "shotsOnTarget"), sota=st(away, "shotsOnTarget"),
                shh=st(home, "totalShots"), sha=st(away, "totalShots"))


def record_pick(event, pick):
    """Insert a football pick in the immutable ledger if it is gradeable and the match has not started."""
    try:
        ko = datetime.fromisoformat(event["kickoff"].replace("Z", "+00:00"))
    except Exception:
        return False
    if ko <= datetime.now(timezone.utc):
        return False
    if compile_label(pick["label"], event["home"], event["away"]) is None:
        return False
    pid = f"{event['original_id']}|{pick['label']}"
    return store.add_prediction(pid, event["original_id"], event["league_code"], "football", event["title"],
                                event["home"], event["away"], pick["label"], pick["market"], pick["prob"],
                                pick["fairOdds"], event["kickoff"])


def grade_pending():
    """Settle predictions whose match ended >= 3h ago and whose box score is now available."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    done = 0
    for r in store.pending_predictions(cutoff):
        fn = compile_label(r["pick"], r["home"], r["away"])
        if fn is None:
            store.grade_prediction(r["id"], "void", "non verificabile")
            continue
        summ = summary(r["event_id"], r["slug"])
        if not summ:
            # postponed / abandoned: void after 5 days without a final result
            ko = datetime.fromisoformat(r["kickoff"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - ko > timedelta(days=5):
                store.grade_prediction(r["id"], "void", "gara non conclusa")
            continue
        S = box_score(summ, r["home"], r["away"])
        if not S:
            continue
        try:
            won = bool(fn(S))
        except Exception:
            continue
        store.grade_prediction(r["id"], "won" if won else "lost", f"{S['H']}-{S['A']}")
        done += 1
    return done

