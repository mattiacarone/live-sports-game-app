"""Prediction engine.

1. Team profiles: recency-weighted, shrunk-to-mean rates (for & against) for goals,
   first-half goals, corners, shots, shots on target, cards, possession, plus
   per-player shares of team goals / shots / SOT / cards in matches they started.
2. Fixture projection: multiplicative attack x defence model with empirical home
   factors; goals blended with the bookmaker's de-vigged 1X2 + total line.
3. Monte-Carlo simulation (20k runs) of each match: Dixon-Coles score grid,
   binomial half-time split, SOT >= goals, shots >= SOT, negative-binomial corners
   and cards with dispersion measured from the data, players drawn from team totals.
   Every market — and every combination of markets — is evaluated on the same
   simulated matches, so Bet Builder probabilities include correlation.
"""
import math
import zlib
from collections import defaultdict
from itertools import combinations
import numpy as np

N = 20000
MAXG = 10
RHO = -0.06                 # Dixon-Coles low-score correction
MARKET_W = 0.65             # weight of bookmaker-implied goals when available
STATS = {"goals": None, "corners": "wonCorners", "shots": "totalShots", "sot": "shotsOnTarget",
         "yellow": "yellowCards", "red": "redCards", "poss": "possessionPct", "fouls": "foulsCommitted"}


# ============================================================ records & pool
def records(summaries):
    """One record per team per match (perspective of that team)."""
    recs = []
    for s in summaries:
        ids = list(s["teams"])
        for tid, oid in ((ids[0], ids[1]), (ids[1], ids[0])):
            t, o = s["teams"][tid], s["teams"][oid]
            r = dict(team=tid, opp=oid, date=s["date"], league=s["league"], home=t["home"], players=t["players"],
                     gf=t["goals"], ga=o["goals"],
                     htf=t["ht"] if t["ht"] is not None else None, hta=o["ht"] if o["ht"] is not None else None)
            for k, key in STATS.items():
                if key:
                    r[k + "_f"] = t["stats"].get(key)
                    r[k + "_a"] = o["stats"].get(key)
            r["goals_f"], r["goals_a"] = r["gf"], r["ga"]
            recs.append(r)
    return recs


class Pool:
    """League-wide baselines and over-dispersion measured from all collected matches."""

    def __init__(self, recs):
        self.mean, self.home, self.away, self.disp = {}, {}, {}, {}
        by_team = defaultdict(list)
        for r in recs:
            by_team[r["team"]].append(r)
        for k in STATS:
            vals = [r[k + "_f"] for r in recs if r.get(k + "_f") is not None]
            self.mean[k] = float(np.mean(vals)) if vals else 1.0
            h = [r[k + "_f"] for r in recs if r["home"] and r.get(k + "_f") is not None]
            a = [r[k + "_f"] for r in recs if not r["home"] and r.get(k + "_f") is not None]
            self.home[k] = float(np.mean(h)) if h else self.mean[k]
            self.away[k] = float(np.mean(a)) if a else self.mean[k]
            # within-team variance / mean  -> negative binomial dispersion
            ss, n = 0.0, 0
            for rs in by_team.values():
                x = [r[k + "_f"] for r in rs if r.get(k + "_f") is not None]
                if len(x) > 2:
                    ss += np.var(x, ddof=1) * (len(x) - 1)
                    n += len(x) - 1
            self.disp[k] = max(1.0, (ss / n) / self.mean[k]) if n and self.mean[k] else 1.0
        h1 = [r["htf"] for r in recs if r["htf"] is not None]
        ft = [r["gf"] for r in recs if r["htf"] is not None]
        self.h1share = sum(h1) / sum(ft) if sum(ft) else 0.44


# ============================================================ team profile
POS_PRIOR = {"G": (0, 0, .02, 0), "D": (.05, .05, .13, .06), "M": (.10, .10, .12, .18), "F": (.26, .19, .07, .16)}  # goal, shot, card, assist


def pos_group(a):
    a = (a or "").upper()
    if a.startswith("G"):
        return "G"
    if a in ("D", "LB", "RB", "CB", "SW", "WB", "LWB", "RWB") or a.startswith("CD"):
        return "D"
    if a.startswith(("F", "CF", "ST", "LF", "RF", "LW", "RW", "SS")):
        return "F"
    return "M"


class Profile:
    def __init__(self, tid, recs, pool, k=3.0, decay=0.88):
        rs = sorted([r for r in recs if r["team"] == tid], key=lambda r: r["date"])
        self.n = len(rs)
        w = np.array([decay ** (len(rs) - 1 - i) for i in range(len(rs))])
        self.rate = {}
        for st in STATS:
            for side in ("f", "a"):
                vals = [(wi, r[f"{st}_{side}"]) for wi, r in zip(w, rs) if r.get(f"{st}_{side}") is not None]
                sw = sum(v[0] for v in vals)
                self.rate[f"{st}_{side}"] = (sum(wi * x for wi, x in vals) + k * pool.mean[st]) / (sw + k)
        h1 = sum(r["htf"] for r in rs if r["htf"] is not None)
        ft = sum(r["gf"] for r in rs if r["htf"] is not None)
        self.h1share = (h1 + 8 * pool.h1share) / (ft + 8)
        self.form = "".join("W" if r["gf"] > r["ga"] else "D" if r["gf"] == r["ga"] else "L" for r in rs[-5:])
        self.last = [dict(date=r["date"][:10], gf=int(r["gf"]), ga=int(r["ga"]), home=r["home"]) for r in rs[-5:]]
        self.players = self._players(rs)

    def _players(self, rs):
        agg = {}
        recent = rs[-4:]
        for r in rs:
            team = dict(g=r["gf"], sh=r.get("shots_f") or 0, sot=r.get("sot_f") or 0, y=r.get("yellow_f") or 0)
            for p in r["players"]:
                if not p["start"]:
                    continue
                a = agg.setdefault(p["id"], dict(id=p["id"], name=p["name"], pos=pos_group(p["pos"]), starts=0,
                                                 g=0, sh=0, sot=0, y=0, a=0, T=dict(g=0, sh=0, sot=0, y=0)))
                a["starts"] += 1
                for key in ("g", "sh", "sot", "y", "a"):
                    a[key] += p[key]
                for key in team:
                    a["T"][key] += team[key]
        wts = [0.1, 0.2, 0.3, 0.4][-len(recent):] if recent else []
        out = []
        for a in agg.values():
            started = [any(p["id"] == a["id"] and p["start"] for p in r["players"]) for r in recent]
            a["avail"] = sum(wi for wi, s in zip(wts, started) if s) / (sum(wts) or 1)
            pg, ps, pc, pa = POS_PRIOR[a["pos"]]
            a["s_g"] = (a["g"] + 2 * pg) / (a["T"]["g"] + 2)
            a["s_a"] = (a["a"] + 2 * pa) / (a["T"]["g"] + 2)
            a["s_sh"] = (a["sh"] + 5 * ps) / (a["T"]["sh"] + 5)
            a["s_sot"] = (a["sot"] + 3 * ps) / (a["T"]["sot"] + 3)
            a["s_y"] = (a["y"] + 2 * pc) / (a["T"]["y"] + 2)
            if a["starts"] >= 2 and a["pos"] != "G":
                out.append(a)
        return out


# ============================================================ goals model
_LAM = np.arange(0.15, 4.5, 0.02)
_K = np.arange(MAXG)
_PMF = np.exp(-_LAM[:, None]) * _LAM[:, None] ** _K / np.array([math.factorial(int(k)) for k in _K])


def fit_market(odds):
    """Find home/away goal expectancy that reproduces the bookmaker's de-vigged prices."""
    ih, idr, ia = 1 / odds["h"], 1 / odds["d"], 1 / odds["a"]
    s = ih + idr + ia
    mh, ma = ih / s, ia / s
    low = np.tril(np.ones((MAXG, MAXG)), -1)                       # i > j
    ph = _PMF @ low @ _PMF.T                                       # [home_lam, away_lam]
    pa = _PMF @ low.T @ _PMF.T
    err = (ph - mh) ** 2 + (pa - ma) ** 2
    if odds.get("line") and odds.get("over") and odds.get("under"):
        io, iu = 1 / odds["over"], 1 / odds["under"]
        mo = io / (io + iu)
        L = odds["line"]
        tot = _K[:, None] + _K[None, :]
        over = (tot > L).astype(float)
        po = _PMF @ over @ _PMF.T
        err = err + (po - mo) ** 2
    i, j = np.unravel_index(np.argmin(err), err.shape)
    return float(_LAM[i]), float(_LAM[j]), dict(h=mh, d=idr / s, a=ma)


def score_grid(lh, la):
    ph = np.exp(-lh) * lh ** _K / np.array([math.factorial(int(k)) for k in _K])
    pa = np.exp(-la) * la ** _K / np.array([math.factorial(int(k)) for k in _K])
    g = np.outer(ph, pa)
    g[0, 0] *= 1 - lh * la * RHO
    g[0, 1] *= 1 + lh * RHO
    g[1, 0] *= 1 + la * RHO
    g[1, 1] *= 1 - RHO
    return g / g.sum()


# ============================================================ simulation
def _nb(rng, mu, r):
    mu = max(mu, 0.05)
    if r <= 1.05:
        return rng.poisson(mu, N)
    n = mu / (r - 1)
    return rng.negative_binomial(n, n / (n + mu), N)


def project(fx, hp, ap, pool):
    P = {}
    for st in STATS:
        m = pool.mean[st] or 1
        P[st] = [pool.home[st] * hp.rate[f"{st}_f"] / m * ap.rate[f"{st}_a"] / m,
                 pool.away[st] * ap.rate[f"{st}_f"] / m * hp.rate[f"{st}_a"] / m]
    ph = 50 + (hp.rate["poss_f"] - ap.rate["poss_f"]) / 2
    P["poss"] = [float(np.clip(ph, 25, 75)), float(np.clip(100 - ph, 25, 75))]
    stats_lam = list(P["goals"])
    mk = None
    if fx.get("odds"):
        mlh, mla, mk = fit_market(fx["odds"])
        P["goals"] = [mlh ** MARKET_W * stats_lam[0] ** (1 - MARKET_W), mla ** MARKET_W * stats_lam[1] ** (1 - MARKET_W)]
        # market sees cross-league strength the stats can't: carry it into volume stats
        for i in (0, 1):
            ratio = P["goals"][i] / max(stats_lam[i], .1)
            P["shots"][i] *= ratio ** 0.5
            P["sot"][i] *= ratio ** 0.5
            P["corners"][i] *= ratio ** 0.3
    return P, stats_lam, mk


def simulate(fx, hp, ap, pool, P, lineups):
    rng = np.random.default_rng(int(fx["id"]) % (2 ** 32))
    lh, la = P["goals"]
    grid = score_grid(lh, la)
    idx = rng.choice(MAXG * MAXG, size=N, p=grid.ravel())
    S = dict(H=idx // MAXG, A=idx % MAXG)
    S["HH"] = rng.binomial(S["H"], hp.h1share)
    S["AH"] = rng.binomial(S["A"], ap.h1share)
    for side, i, lam in (("h", 0, lh), ("a", 1, la)):
        g = S["H" if side == "h" else "A"]
        S["sot" + side] = g + _nb(rng, P["sot"][i] - lam, pool.disp["sot"])
        S["sh" + side] = S["sot" + side] + _nb(rng, P["shots"][i] - P["sot"][i], pool.disp["shots"])
        S["c" + side] = _nb(rng, P["corners"][i], pool.disp["corners"])
        S["y" + side] = _nb(rng, P["yellow"][i], pool.disp["yellow"])
        S["r" + side] = rng.poisson(max(P["red"][i], 0.01), N)
    players = []
    for side, prof in (("h", hp), ("a", ap)):
        lu = lineups.get(prof_id(fx, side))
        for p in prof.players:
            avail = (0.97 if p["id"] in lu else 0.0) if lu else p["avail"]
            if avail < 0.5:
                continue
            on = rng.random(N) < avail
            G = S["H" if side == "h" else "A"]
            players.append(dict(
                name=p["name"], side=side, pos=p["pos"], starts=p["starts"], g=int(p["g"]), a=int(p.get("a", 0)), sh=int(p["sh"]),
                sot=int(p["sot"]), avail=round(avail, 2), confirmed=bool(lu),
                G=rng.binomial(G, min(p["s_g"], .95)) * on,
                A=rng.binomial(G, min(p.get("s_a", 0.1), .85)) * on,
                SH=rng.binomial(S["sh" + side], min(p["s_sh"], .95)) * on,
                SOT=rng.binomial(S["sot" + side], min(p["s_sot"], .95)) * on,
                Y=rng.binomial(S["y" + side], min(p["s_y"], .95)) * on))
    return S, grid, players


def prof_id(fx, side):
    return fx["home" if side == "h" else "away"]["id"]


# ============================================================ markets
def markets(fx, S, players):
    H, A, HH, AH = S["H"], S["A"], S["HH"], S["AH"]
    hn, an = fx["home"]["name"], fx["away"]["name"]
    T, D = H + A, H - A
    H2, A2 = H - HH, A - AH
    C, Y, SOT, SH = S["ch"] + S["ca"], S["yh"] + S["ya"] + S["rh"] + S["ra"], S["soth"] + S["sota"], S["shh"] + S["sha"]
    out = []

    def add(fam, label, mask, builder=True, player=None):
        out.append(dict(fam=fam, label=label, m=mask, builder=builder, player=player))

    add("Result", f"{hn} to win", D > 0); add("Result", "Draw", D == 0); add("Result", f"{an} to win", D < 0)
    add("Double chance", f"{hn} or draw", D >= 0); add("Double chance", f"{an} or draw", D <= 0)
    add("Double chance", f"{hn} or {an}", D != 0)
    for x in (0.5, 1.5, 2.5, 3.5, 4.5):
        add("Goals", f"Over {x} goals", T > x); add("Goals", f"Under {x} goals", T < x)
    add("BTTS", "Both teams to score", (H > 0) & (A > 0)); add("BTTS", "Both teams to score: No", (H == 0) | (A == 0))
    for n, G in ((hn, H), (an, A)):
        for x in (0.5, 1.5, 2.5):
            add("Team goals", f"{n} over {x} goals", G > x)
        add("Team goals", f"{n} under 1.5 goals", G < 1.5)
    add("Team goals", f"{hn} clean sheet", A == 0); add("Team goals", f"{an} clean sheet", H == 0)
    add("Result & goals", f"{hn} to win to nil", (D > 0) & (A == 0)); add("Result & goals", f"{an} to win to nil", (D < 0) & (H == 0))
    for n, m in ((hn, D > 0), (an, D < 0), ("Draw", D == 0)):
        add("Result & goals", f"{n} & BTTS", m & (H > 0) & (A > 0))
        add("Result & goals", f"{n} & over 2.5", m & (T > 2.5)); add("Result & goals", f"{n} & under 3.5", m & (T < 3.5))
    for k in range(6):
        add("Exact goals", f"Exactly {k} goals" if k < 5 else "5+ goals", T == k if k < 5 else T >= 5, False)
    # halves
    for n, m in ((hn, HH > AH), ("Draw", HH == AH), (an, HH < AH)):
        add("Half time", f"1st half result: {n}", m)
    add("Half time", "1st half over 0.5 goals", HH + AH > 0); add("Half time", "1st half under 0.5 goals", HH + AH == 0)
    add("Half time", "1st half over 1.5 goals", HH + AH > 1); add("Half time", "1st half under 1.5 goals", HH + AH < 2)
    add("Half time", "1st half both teams to score", (HH > 0) & (AH > 0))
    for n, s in ((hn, HH), (an, AH)):
        add("Half time", f"1st half {n} over 0.5 goals", s > 0)
        add("Half time", f"1st half {n} clean sheet", (AH if n == hn else HH) == 0)

    # 2nd half markets
    for n, m in ((hn, H2 > A2), ("Draw", H2 == A2), (an, H2 < A2)):
        add("Half time", f"2nd half result: {n}", m)
    add("Half time", "2nd half over 0.5 goals", H2 + A2 > 0); add("Half time", "2nd half under 0.5 goals", H2 + A2 == 0)
    add("Half time", "2nd half over 1.5 goals", H2 + A2 > 1); add("Half time", "2nd half under 1.5 goals", H2 + A2 < 2)
    add("Half time", "2nd half both teams to score", (H2 > 0) & (A2 > 0))
    for n, s in ((hn, H2), (an, A2)):
        add("Half time", f"2nd half {n} over 0.5 goals", s > 0)

    add("Half time", "Highest scoring half: 2nd", H2 + A2 > HH + AH); add("Half time", "Highest scoring half: 1st", H2 + A2 < HH + AH)
    add("Half time", "Both halves same goals", H2 + A2 == HH + AH)
    add("Half time", "Goal in both halves", (HH + AH > 0) & (H2 + A2 > 0))
    add("Half time", f"{hn} to score in both halves", (HH > 0) & (H2 > 0)); add("Half time", f"{an} to score in both halves", (AH > 0) & (A2 > 0))
    for hl, hm in ((hn, HH > AH), ("Draw", HH == AH), (an, HH < AH)):
        for fl, fm in ((hn, D > 0), ("Draw", D == 0), (an, D < 0)):
            add("HT/FT", f"HT/FT {hl} / {fl}", hm & fm, False)
    for i in range(6):
        for j in range(6):
            add("Correct score", f"Correct score {i}-{j}", (H == i) & (A == j), False)
    # 3-way (European) handicap
    for l in (1, 2):
        add("Handicap", f"{hn} -{l} (3-way)", D - l > 0); add("Handicap", f"{an} +{l} (3-way)", D - l < 0)
        add("Handicap", f"{an} -{l} (3-way)", -D - l > 0); add("Handicap", f"{hn} +{l} (3-way)", -D - l < 0)
    # corners / cards / shots
    for x in (7.5, 8.5, 9.5, 10.5, 11.5, 12.5):
        add("Corners", f"Over {x} corners", C > x); add("Corners", f"Under {x} corners", C < x)
    for n, s in ((hn, "h"), (an, "a")):
        for x in (2.5, 3.5, 4.5, 5.5, 6.5):
            add("Corners", f"{n} over {x} corners", S["c" + s] > x)
    add("Corners", f"Most corners: {hn}", S["ch"] > S["ca"]); add("Corners", f"Most corners: {an}", S["ch"] < S["ca"])
    for x in (1.5, 2.5, 3.5, 4.5, 5.5, 6.5):
        add("Cards", f"Over {x} cards", Y > x); add("Cards", f"Under {x} cards", Y < x)
    for n, s in ((hn, "h"), (an, "a")):
        for x in (0.5, 1.5, 2.5):
            add("Cards", f"{n} over {x} cards", S["y" + s] + S["r" + s] > x)
    add("Cards", "A red card shown", S["rh"] + S["ra"] > 0, False)
    for x in (5.5, 6.5, 7.5, 8.5, 9.5, 10.5):
        add("Shots", f"Over {x} shots on target", SOT > x); add("Shots", f"Under {x} shots on target", SOT < x)
    for x in (19.5, 21.5, 23.5, 25.5, 27.5):
        add("Shots", f"Over {x} total shots", SH > x); add("Shots", f"Under {x} total shots", SH < x)
    for n, s in ((hn, "h"), (an, "a")):
        for x in (2.5, 3.5, 4.5, 5.5, 6.5):
            add("Shots", f"{n} over {x} shots on target", S["sot" + s] > x)
            add("Shots", f"{n} under {x} shots on target", S["sot" + s] < x)
        for x in (8.5, 10.5, 12.5, 14.5, 16.5):
            add("Shots", f"{n} over {x} shots", S["sh" + s] > x)
            add("Shots", f"{n} under {x} shots", S["sh" + s] < x)
    for p in players:
        nm = p["name"]
        add("Player", f"{nm} to score", p["G"] > 0)
        add("Player", f"{nm} to provide an assist", p["A"] > 0)
        add("Player", f"{nm} goal or assist", (p["G"] > 0) | (p["A"] > 0))
        add("Player", f"{nm} 2+ goals", p["G"] > 1, False)
        add("Player", f"{nm} 1+ shot on target", p["SOT"] > 0); add("Player", f"{nm} 2+ shots on target", p["SOT"] > 1)
        add("Player", f"{nm} 2+ shots", p["SH"] > 1); add("Player", f"{nm} 3+ shots", p["SH"] > 2)
        add("Player", f"{nm} to be carded", p["Y"] > 0)
    for m in out:
        m["p"] = float(m["m"].mean())
    # Asian lines (refund-aware fair odds)
    asian = []
    for L in np.arange(-2.5, 2.75, 0.25):
        asian.append(_asian(f"{hn} {L:+.2f}", D, L)); asian.append(_asian(f"{an} {-L:+.2f}", -D, -L))
    for L in np.arange(1.5, 4.25, 0.25):
        asian.append(_asian(f"Asian over {L:.2f} goals", T, -L)); asian.append(_asian(f"Asian under {L:.2f} goals", -T, L))
    asian.append(_asian(f"{hn} draw no bet", D, 0)); asian.append(_asian(f"{an} draw no bet", -D, 0))
    return out, asian


def _asian(label, x, L):
    """x + L > 0 wins; quarter lines split stake. Returns win/push and fair odds."""
    subs = [L] if (L * 2) % 1 == 0 else [L - 0.25, L + 0.25]
    a = np.mean([((x + l) > 0).mean() for l in subs])
    b = np.mean([((x + l) == 0).mean() for l in subs])
    return dict(fam="Asian", label=label, p=float(a), push=float(b), fair=round((1 - b) / a, 2) if a > 0 else None)


# ============================================================ recommendations
REL = {"Result": 1, "Double chance": 1, "Goals": 1, "BTTS": .95, "Team goals": .95, "Result & goals": .95,
       "Half time": .85, "Handicap": 1, "Corners": .8, "Shots": .8, "Cards": .7, "Player": .7}


def why(m, ctx):
    f, P, hn, an = m["fam"], ctx["P"], ctx["hn"], ctx["an"]
    g = P["goals"]
    if f in ("Result", "Double chance", "Handicap"):
        return f"Probabilita 1 / X / 2: {ctx['p1']:.0%} / {ctx['px']:.0%} / {ctx['p2']:.0%}" + (" (combinata con le quote di mercato)" if ctx["mk"] else "")
    if f in ("Goals", "Result & goals", "Team goals"):
        return f"Gol attesi {g[0]:.2f} - {g[1]:.2f} (totale {sum(g):.2f})"
    if f == "BTTS":
        return f"{hn} segna nel {ctx['hs']:.0%} delle simulazioni, {an} nel {ctx['as']:.0%}"
    if f == "Half time":
        return f"Quota di gol segnati nel primo tempo: {ctx['h1'][0]:.0%} / {ctx['h1'][1]:.0%}"
    if f == "Corners":
        return f"Calci d'angolo attesi {P['corners'][0]:.1f} - {P['corners'][1]:.1f} (totale {sum(P['corners']):.1f})"
    if f == "Cards":
        return f"Cartellini attesi {P['yellow'][0]:.1f} - {P['yellow'][1]:.1f} (arbitro non modellato)"
    if f == "Shots":
        return f"Tiri in porta attesi {P['sot'][0]:.1f} - {P['sot'][1]:.1f}, tiri totali {P['shots'][0]:.0f} - {P['shots'][1]:.0f}"
    if f == "Player":
        lab = m["label"]
        raw_name = lab.split(" to ")[0].split(" goal or assist")[0].split(" 1+")[0].split(" 2+")[0].split(" 3+")[0]
        p = ctx["players"].get(raw_name)
        if p:
            parts = []
            if "assist" in lab:
                parts.append(f"{p.get('a', 0)} assist nelle ultime {p['starts']} da titolare")
            if "score" in lab or "goal" in lab:
                parts.append(f"{p['g']} gol nelle ultime {p['starts']} da titolare")
            if "shot" in lab:
                parts.append(f"{p['sh']} tiri ({p['sot']} in porta) nelle ultime {p['starts']} da titolare")
            if "card" in lab:
                parts.append(f"Titolare in {p['starts']} delle ultime gare ufficiali")
            desc = " · ".join(parts) if parts else f"{p['g']} gol, {p.get('a', 0)} assist, {p['sh']} tiri nelle ultime {p['starts']} da titolare"
            if p.get("confirmed"):
                desc += " · titolare confermato"
            return desc
    return ""


def pub(m, ctx):
    return dict(fam=m["fam"], label=m["label"], p=round(m["p"], 3), fair=round(1 / m["p"], 2) if m["p"] else None, why=why(m, ctx))


def recommend(mkts, ctx, odds):
    rel = dict(REL)
    if not ctx["mk"]:
        for k in ("Result", "Double chance", "Goals", "BTTS", "Team goals", "Result & goals", "Handicap"):
            rel[k] *= 0.9
    scored = [m for m in mkts if m["fam"] in rel]
    # Top picks: safest meaningful prices (fair odds 1.22 - 1.80), one per family
    picks, used = [], set()
    for m in sorted([m for m in scored if 0.555 <= m["p"] <= 0.82], key=lambda m: -m["p"] * rel[m["fam"]]):
        if m["fam"] not in used:
            used.add(m["fam"]); picks.append(m)
        if len(picks) == 5:
            break
    # Bet builders
    cands = []
    for fam in rel:
        fm = sorted([m for m in scored if m["fam"] == fam and m["builder"] and 0.55 <= m["p"] <= 0.92],
                    key=lambda m: -m["p"] * rel[fam])
        cands += fm[:3 if fam == "Player" else 2]
    group = lambda f: "result" if f in ("Result", "Double chance", "Handicap") else f

    def best(sizes, min_odds):
        top = None
        for k in sizes:
            for combo in combinations(cands, k):
                gs = [group(m["fam"]) for m in combo]
                if len(set(gs)) < k:
                    continue
                mask = combo[0]["m"].copy()
                for m in combo[1:]:
                    mask &= m["m"]
                jp = float(mask.mean())
                if jp <= 0 or 1 / jp < min_odds or jp >= 0.97 * min(m["p"] for m in combo):
                    continue
                score = jp * np.prod([rel[m["fam"]] for m in combo]) ** (1 / k)
                if not top or score > top[0]:
                    top = (score, combo, jp)
        if not top:
            return None
        _, combo, jp = top
        ind = float(np.prod([m["p"] for m in combo]))
        return dict(legs=[pub(m, ctx) for m in combo], p=round(jp, 3), fair=round(1 / jp, 2), lift=round(jp / ind, 2))

    value = []
    if odds:
        for lab, key, p in ((f"{ctx['hn']} to win", "h", ctx["p1"]), ("Draw", "d", ctx["px"]), (f"{ctx['an']} to win", "a", ctx["p2"])):
            e = p * odds[key] - 1
            if e > 0.03:
                value.append(dict(label=lab, p=round(p, 3), odds=round(odds[key], 2), edge=round(e, 3)))
        if odds.get("line") and odds.get("over"):
            po = next((m["p"] for m in mkts if m["label"] == f"Over {odds['line']} goals"), None)
            if po:
                for lab, p, o in ((f"Over {odds['line']} goals", po, odds["over"]), (f"Under {odds['line']} goals", 1 - po, odds["under"])):
                    if o and p * o - 1 > 0.03:
                        value.append(dict(label=lab, p=round(p, 3), odds=round(o, 2), edge=round(p * o - 1, 3)))
    return dict(picks=[pub(m, ctx) for m in picks], safe=best((2, 3), 1.8), bold=best((3, 4), 3.5), value=value,
                book=odds["book"] if odds else None)


def analyse(fx, hp, ap, pool, lineups):
    P, stats_lam, mk = project(fx, hp, ap, pool)
    S, grid, players = simulate(fx, hp, ap, pool, P, lineups)
    mkts, asian = markets(fx, S, players)
    D = S["H"] - S["A"]
    ctx = dict(P=P, mk=mk, hn=fx["home"]["name"], an=fx["away"]["name"], p1=float((D > 0).mean()), px=float((D == 0).mean()),
               p2=float((D < 0).mean()), hs=float((S["H"] > 0).mean()), **{"as": float((S["A"] > 0).mean())},
               h1=(hp.h1share, ap.h1share), players={p["name"]: p for p in players})
    rec = recommend(mkts, ctx, fx.get("odds"))
    scores = sorted(((i, j, grid[i, j]) for i in range(7) for j in range(7)), key=lambda t: -t[2])[:4]
    htft = sorted([m for m in mkts if m["fam"] == "HT/FT"], key=lambda m: -m["p"])[0]
    res = max((("home", ctx["p1"]), ("draw", ctx["px"]), ("away", ctx["p2"])), key=lambda x: x[1])
    thin = min(hp.n, ap.n) < 5
    groups = defaultdict(list)
    for m in mkts:
        mp = round(m["p"], 3)
        groups[m["fam"]].append(dict(
            label=m["label"],
            p=mp,
            fair=round(1 / m["p"], 2) if m["p"] >= 0.01 else None,
            builder=bool(m.get("builder", True))
        ))
    groups["Asian"] = [dict(label=a["label"], p=round(a["p"], 3), push=round(a["push"], 3), fair=a["fair"], builder=False) for a in asian]
    for p in players:
        for k in ("G", "A", "SH", "SOT", "Y"):
            p.pop(k, None)
    return dict(
        probs=dict(home=round(ctx["p1"], 3), draw=round(ctx["px"], 3), away=round(ctx["p2"], 3),
                   o25=round(float((S["H"] + S["A"] > 2).mean()), 3), btts=round(float(((S["H"] > 0) & (S["A"] > 0)).mean()), 3)),
        likely=dict(result=res[0], p=round(res[1], 3), scores=[dict(s=f"{i}-{j}", p=round(float(p), 3)) for i, j, p in scores],
                    htft=htft["label"].replace("HT/FT ", ""), htftp=round(htft["p"], 3)),
        proj={k: [round(v[0], 2), round(v[1], 2)] for k, v in P.items() if k != "fouls"},
        statsGoals=[round(x, 2) for x in stats_lam],
        market={k: round(v, 3) for k, v in mk.items()} if mk else None,
        form=dict(home=hp.form, away=ap.form), last=dict(home=hp.last, away=ap.last), samples=[hp.n, ap.n],
        thin=thin, lineups=bool(lineups), rec=rec, markets=groups, players=players,
        confidence=_confidence(rec, mk, thin),
    )


def _confidence(rec, mk, thin):
    top = rec["picks"][0]["p"] if rec["picks"] else 0
    score = top * (1 if mk else 0.9) * (0.85 if thin else 1)
    return "High" if score >= 0.72 else "Medium" if score >= 0.64 else "Low"


def eval_custom_builder(fx, hp, ap, pool, lineups, leg_labels):
    """Evaluate user-selected Same-Game Parlay legs on the exact 20,000 Monte Carlo match states."""
    P, _, mk = project(fx, hp, ap, pool)
    S, _, players = simulate(fx, hp, ap, pool, P, lineups)
    mkts, _ = markets(fx, S, players)
    D = S["H"] - S["A"]
    ctx = dict(P=P, mk=mk, hn=fx["home"]["name"], an=fx["away"]["name"], p1=float((D > 0).mean()), px=float((D == 0).mean()),
               p2=float((D < 0).mean()), hs=float((S["H"] > 0).mean()), **{"as": float((S["A"] > 0).mean())},
               h1=(hp.h1share, ap.h1share), players={p["name"]: p for p in players})
    by_label = {m["label"]: m for m in mkts}
    chosen = [by_label[lbl] for lbl in leg_labels if lbl in by_label]
    if not chosen:
        return None
    mask = chosen[0]["m"].copy()
    for m in chosen[1:]:
        mask &= m["m"]
    jp = float(mask.mean())
    ind = float(np.prod([m["p"] for m in chosen]))
    lift = round(jp / ind, 3) if ind > 0 else 1.0
    fair = round(1 / jp, 2) if jp > 0.002 else 99.0
    return dict(
        legs=[pub(m, ctx) for m in chosen],
        p=round(jp, 3),
        indP=round(ind, 3),
        fair=fair,
        minBookOdds=round(fair * 1.04, 2),
        lift=lift,
        liftPct=round((lift - 1.0) * 100, 1),
        contradictory=(jp < 0.001)
    )


def build_backtest_ledger(summaries, team_name_fn, league_names):
    """Walk-forward out-of-sample evaluation across historical completed matches in cache/."""
    if not summaries:
        return {"totalBetsAllTime": 0, "roiAllTime": 0, "cumulativeProfitByDay": [], "latestBets": [], "byMarket": []}

    all_recs = records(summaries)
    pool = Pool(all_recs)
    by_team = defaultdict(list)
    for r in all_recs:
        by_team[r["team"]].append(r)
    for tid in by_team:
        by_team[tid].sort(key=lambda x: x["date"])

    settled = []
    brier_sum = 0.0
    ll_sum = 0.0
    prob_sum = 0.0
    euro_books = ["Pinnacle", "Bet365", "Unibet", "Betfair Exchange", "Tipico", "Winamax", "Betsson", "bwin"]

    for s in summaries:
        dt = s.get("date", "")
        tids = list(s["teams"].keys())
        if len(tids) != 2:
            continue
        hid = tids[0] if s["teams"][tids[0]].get("home") else tids[1]
        aid = tids[1] if hid == tids[0] else tids[0]
        ht_data, at_data = s["teams"][hid], s["teams"][aid]

        # Strictly prior records (zero look-ahead bias; empirical Bayes k=3.0 handles small samples)
        h_prior = [r for r in by_team[hid] if r["date"] < dt][-12:]
        a_prior = [r for r in by_team[aid] if r["date"] < dt][-12:]
        if len(h_prior) < 1 and len(a_prior) < 1:
            continue

        hp = Profile(hid, h_prior, pool)
        ap = Profile(aid, a_prior, pool)
        hn = ht_data.get("name") or team_name_fn(hid)
        an = at_data.get("name") or team_name_fn(aid)
        fx_stub = {"id": int(s["id"]) if str(s["id"]).isdigit() else hash(s["id"]),
                   "home": {"id": hid, "name": hn}, "away": {"id": aid, "name": an}, "odds": None}

        P, _, _ = project(fx_stub, hp, ap, pool)
        lh, la = P["goals"]
        grid = score_grid(lh, la)
        p_home = float(np.tril(grid, -1).sum())
        p_draw = float(np.trace(grid))
        p_away = float(np.triu(grid, 1).sum())
        tot_idx = _K[:, None] + _K[None, :]
        p_o15 = float(grid[tot_idx > 1.5].sum())
        p_o25 = float(grid[tot_idx > 2.5].sum())
        p_u35 = float(grid[tot_idx < 3.5].sum())

        c_tot = sum(P["corners"])
        sot_tot = sum(P["sot"])
        sh_tot = sum(P["shots"])
        y_tot = sum(P["yellow"])
        pois_over = lambda lam, line: float(1.0 - sum(math.exp(-lam) * (lam ** k) / math.factorial(k) for k in range(int(line) + 1))) if lam > 0 else 0.5
        p_c75 = pois_over(c_tot, 7.5)
        p_sot65 = pois_over(sot_tot, 6.5)
        p_sh205 = pois_over(sh_tot, 20.5)
        p_y25 = pois_over(y_tot, 2.5)

        # Actual outcome values
        act_h, act_a = int(ht_data.get("goals") or 0), int(at_data.get("goals") or 0)
        act_tot = act_h + act_a
        act_c = (ht_data["stats"].get("wonCorners") or 0) + (at_data["stats"].get("wonCorners") or 0)
        act_sot = (ht_data["stats"].get("shotsOnTarget") or 0) + (at_data["stats"].get("shotsOnTarget") or 0)
        act_sh = (ht_data["stats"].get("totalShots") or 0) + (at_data["stats"].get("totalShots") or 0)
        act_y = (ht_data["stats"].get("yellowCards") or 0) + (at_data["stats"].get("yellowCards") or 0)

        cands = [
            ("Goals", "Over 1.5 goals", p_o15, 1.02, act_tot > 1.5),
            ("Shots", "Over 6.5 shots on target", p_sot65, 1.01, act_sot > 6.5),
            ("Shots", "Over 20.5 total shots", p_sh205, 1.00, act_sh > 20.5),
            ("Double chance", f"{hn} or draw", p_home + p_draw, 0.99, act_h >= act_a),
            ("Corners", "Over 7.5 corners", p_c75, 0.98, act_c > 7.5),
            ("Result", f"{hn} to win", p_home, 0.98, act_h > act_a),
            ("Double chance", f"{an} or draw", p_away + p_draw, 0.96, act_a >= act_h),
            ("Cards", "Over 2.5 cards", p_y25, 0.95, act_y > 2.5),
            ("Result", f"{an} to win", p_away, 0.95, act_a > act_h),
            ("Goals", "Over 2.5 goals", p_o25, 0.94, act_tot > 2.5),
            ("Goals", "Under 3.5 goals", p_u35, 0.93, act_tot < 3.5),
        ]
        valid = [c for c in cands if 0.62 <= c[2] <= 0.82]
        if not valid:
            continue
        valid.sort(key=lambda c: -c[2] * c[3])
        fam, label, prob, _, won = valid[0]

        fair_odds = round(1.0 / prob, 2)
        # NOTE: no bookmaker price is simulated here. ROI needs real historical closing odds,
        # so this backtest only measures probability quality (hit rate, calibration, Brier, log-loss).
        y = 1.0 if won else 0.0
        brier_sum += (prob - y) ** 2
        ll_sum += -(y * math.log(max(prob, 1e-9)) + (1 - y) * math.log(max(1 - prob, 1e-9)))
        prob_sum += prob

        lg_slug = s.get("league", "")
        settled.append(dict(
            id=s["id"],
            date=dt[:10],
            fullDate=dt,
            match=f"{hn} vs {an}",
            score=f"{act_h}-{act_a}",
            league=league_names.get(lg_slug, lg_slug.upper()),
            fam=fam,
            pick=label,
            prob=round(prob, 3),
            fairOdds=fair_odds,
            status="WON" if won else "LOST",
        ))

    if not settled:
        return {"n": 0, "totalBetsAllTime": 0, "roiAllTime": None, "cumulativeProfitByDay": [],
                "latestBets": [], "byMarket": [], "calibration": []}

    settled.sort(key=lambda x: x["fullDate"])
    n = len(settled)
    wins = sum(1 for b in settled if b["status"] == "WON")
    bins = defaultdict(lambda: {"n": 0, "p": 0.0, "w": 0})
    by_mkt = defaultdict(lambda: {"n": 0, "w": 0, "p": 0.0})
    for b in settled:
        k = min(int(b["prob"] * 10), 9)
        bins[k]["n"] += 1
        bins[k]["p"] += b["prob"]
        bins[k]["w"] += 1 if b["status"] == "WON" else 0
        m = by_mkt[b["fam"]]
        m["n"] += 1
        m["w"] += 1 if b["status"] == "WON" else 0
        m["p"] += b["prob"]

    calibration = [dict(bin=f"{k * 10}-{k * 10 + 10}%", n=v["n"], predictedPct=round(v["p"] / v["n"] * 100, 1),
                        actualPct=round(v["w"] / v["n"] * 100, 1)) for k, v in sorted(bins.items())]
    by_market = [dict(market=k, n=v["n"], hitRatePct=round(v["w"] / v["n"] * 100, 1),
                      avgProbPct=round(v["p"] / v["n"] * 100, 1))
                 for k, v in sorted(by_mkt.items(), key=lambda kv: -kv[1]["n"])]

    return dict(
        n=n,
        hitRatePct=round(wins / n * 100, 1),
        avgProbPct=round(prob_sum / n * 100, 1),
        brier=round(brier_sum / n, 4),
        logLoss=round(ll_sum / n, 4),
        calibration=calibration,
        byMarket=by_market,
        range=f"{settled[0]['date']} - {settled[-1]['date']}",
        note="Backtest walk-forward senza look-ahead su partite concluse. Nessun ROI: richiede quote storiche reali.",
        # legacy keys kept for backward compatibility (no simulated money values)
        totalBetsAllTime=n, winsAllTime=wins, lossesAllTime=n - wins, winRatePct=round(wins / n * 100, 1),
        totalProfitEur=None, totalStakeEur=None, roiAllTime=None, brierScore=round(brier_sum / n, 4),
        cumulativeProfitByDay=[], latestBets=list(reversed(settled[-30:])),
    )
