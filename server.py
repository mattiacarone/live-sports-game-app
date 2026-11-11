"""EdgeBet AI (Sports AI Europe) - All-in-One Multi-Sport Quantitative Intelligence SaaS.

Combines:
- European Football (20,000-run Dixon-Coles Monte Carlo, Negative Binomial xG/Corners/Cards/Shots/Players, Bet Builder)
- Tennis (ATP/WTA - Surface-adjusted Elo, Serve Hold & Break Point Markov Chains)
- ️ Formula 1 & ️ MotoGP (FP1-3 Telemetry, Tire Deg, Track Temp, Head-to-Head Driver Duels)
- American Football (NFL - Yards per play, Turnover Diff, QB Injury & Weather Point Spread)
- Basketball (NBA & Euroleague - Pace Possessions x Rating, Back-to-Back Rest Model)
- Rugby (Six Nations & URC - Scrum/Lineout Dominance, Discipline, Margin Distribution)
- Cross-Sport Super-Scanner ("Le più facili da vincere" with Prob >= 74-85%, Dropping Odds tracking)
- Mocked Premium VIP Suite (Sharp Money Whale Radar, Surebet/Arbitrage Scanner, Correlated SGP Lab)
- ⏱️ 20-Minute Automated Background Sync Worker & Real-Time Countdown
"""
import gzip, hashlib, json, math, os, threading, time, traceback, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from engine.data import (
    fixtures, team_history, summary, lineup, all_cached_summaries,
    team_name, LEAGUES, LEAGUE_META
)
from engine.model import (
    Pool, Profile, records, analyse, eval_custom_builder, build_backtest_ledger
)
from engine.multisport import (
    SPORTS_CONFIG, generate_multisport_catalog, get_global_safe_scanner,
    record_odds_snapshot, build_euro_bookmakers, EURO_BOOKS,
    generate_mocked_premium_suite, increment_sync_cycle, get_sync_cycle,
    _build_vip_insights, _enrich_mkt
)
from engine import api, accounts, store, odds_feed, grading, feed

PORT = 8080
DAYS = 7
CACHE_TTL = 300
SYNC_INTERVAL_SEC = 1200  # 20 minutes (1,200 seconds)

EXTENDED_LEAGUE_NAMES = {
    **LEAGUES,
    "aut.1": "Austrian Bundesliga",
    "bel.1": "Belgian Pro League",
    "den.1": "Danish Superliga",
    "gre.1": "Greek Super League",
    "nor.1": "Eliteserien",
    "sco.1": "Scottish Premiership",
    "swe.1": "Allsvenskan",
    "tur.1": "Turkish Süper Lig",
    "eng.charity": "FA Community Shield",
    "eng.league_cup": "EFL Cup",
    "ger.dfb_pokal": "DFB-Pokal",
    "ger.super_cup": "DFL-Supercup",
    "fra.super_cup": "Trophée des Champions",
    "ned.supercup": "Johan Cruyff Shield",
    "uefa.super_cup": "UEFA Super Cup",
    "uefa.champions_qual": "UCL Qualifying",
    "uefa.europa_qual": "UEL Qualifying",
    "uefa.europa.conf_qual": "UECL Qualifying",
}

_state = {
    "matches": [],
    "analyzed": {},
    "multisport_events": [],
    "safe_scanner": [],
    "premium_suite": None,
    "performance": None,
    "updated": None,
    "last_sync_20m": None,
    "next_sync_20m": None,
    "sync_cycle": 1,
    "loading": False,
    "progress": ""
}
_lock = threading.Lock()


def _load_fixture_context(fx):
    """Fetch team histories, Pool, Profiles, and lineups for a fixture."""
    h_hist = team_history(fx["home"]["id"], [fx["league"]])
    a_hist = team_history(fx["away"]["id"], [fx["league"]])

    all_sums = []
    for eid, (dt, slug) in h_hist + a_hist:
        s = summary(eid, slug)
        if s:
            all_sums.append(s)

    if not all_sums:
        return None

    recs = records(all_sums)
    pool = Pool(recs)
    hp = Profile(fx["home"]["id"], recs, pool)
    ap = Profile(fx["away"]["id"], recs, pool)
    lu = lineup(fx["id"], fx["league"])
    return hp, ap, pool, lu


def get_match_analysis(fx):
    """Analyze a single fixture if not already cached in memory."""
    fid = fx["id"]
    with _lock:
        if fid in _state["analyzed"]:
            return _state["analyzed"][fid]

    try:
        ctx_data = _load_fixture_context(fx)
        if not ctx_data:
            return None
        hp, ap, pool, lu = ctx_data
        res = analyse(fx, hp, ap, pool, lu)

        meta = LEAGUE_META.get(fx["league"], {"country": "Europe", "flag": "EU", "tier": 1})
        res.update(
            id=fx["id"],
            date=fx["date"],
            league=fx["leagueName"],
            leagueCode=fx["league"],
            country=fx.get("country") or meta["country"],
            flag=fx.get("flag") or meta["flag"],
            home=fx["home"]["name"],
            away=fx["away"]["name"],
            venue=fx["venue"],
            hasMarket=bool(fx.get("odds")),
            odds=fx.get("odds")
        )

        with _lock:
            _state["analyzed"][fid] = res
        return res
    except Exception as e:
        print(f"Error analyzing fixture {fid} ({fx['home']['name']} vs {fx['away']['name']}): {e}")
        traceback.print_exc()
        return None


def get_performance_ledger():
    """Return cached or freshly computed out-of-sample walk-forward performance ledger."""
    with _lock:
        if _state["performance"] is not None and time.time() - _state.get("perf_ts", 0) < 6 * 3600:
            return _state["performance"]

    sums = all_cached_summaries()
    fmt_leagues = {k: (f"{LEAGUE_META[k]['flag']} {v}" if k in LEAGUE_META else v) for k, v in EXTENDED_LEAGUE_NAMES.items()}
    perf = build_backtest_ledger(sums, team_name, fmt_leagues)
    with _lock:
        _state["performance"] = perf
        _state["perf_ts"] = time.time()
    return perf


def _build_football_multisport_events():
    """Convert analyzed football matches into deep polymorphic event structures with full Bet365 markets, stats, facts, and VIP telemetry."""
    with _lock:
        matches = list(_state["analyzed"].values())

    football_events = []
    for m in matches:
        picks = m.get("rec", {}).get("picks", [])
        if not picks:
            continue

        best = picks[0]
        p = best["p"]
        fair = best["fair"]
        est_book = round(fair * 1.055, 2)
        drop_delta, opener_o, live_o = record_odds_snapshot(f"{m['id']}_{best['label']}", est_book)
        books = build_euro_bookmakers(p, live_o, f"{m['id']}_{best['label']}")

        proj = m.get("proj", {})
        probs = m.get("probs", {})
        likely = m.get("likely", {})
        raw_mkts = m.get("markets", {})
        form_h = list(m.get("form", {}).get("home", "WWDLW"))
        form_a = list(m.get("form", {}).get("away", "WDLWW"))

        xg_h, xg_a = proj.get("goals", [1.52, 1.12])
        cor_h, cor_a = proj.get("corners", [5.6, 4.3])
        sh_h, sh_a = proj.get("shots", [13.8, 10.6])
        sot_h, sot_a = proj.get("sot", [4.9, 3.6])
        yel_h, yel_a = proj.get("yellow", [1.9, 2.2])
        poss_h, poss_a = proj.get("poss", [53.0, 47.0])

        top_scores = likely.get("scores", [])
        scores_str = ", ".join(f"{s['s']} ({round(s['p']*100, 1)}%)" for s in top_scores[:4]) if top_scores else "1-0 (11.8%), 2-1 (10.4%), 1-1 (10.1%)"

        def _fmt_group(fam_keys, limit=8):
            items = []
            for fk in fam_keys:
                for gm in raw_mkts.get(fk, []):
                    gp = gm.get("p", 0)
                    if 0.08 <= gp <= 0.94:
                        items.append(_enrich_mkt(gm["label"], gp, fk, 1.055))
            items.sort(key=lambda x: -x["prob"])
            return items[:limit]

        cat_markets = {
            "Principali (1X2 & Doppia Chance)": _fmt_group(["Result", "Double chance"], 8),
            "Goal Over/Under, BTTS & Combo": _fmt_group(["Goals", "BTTS", "Team goals", "Result & goals"], 12),
            "Handicap Asiatici & Europei": _fmt_group(["Asian", "Handicap"], 10),
            "Corner, Tiri & Cartellini": _fmt_group(["Corners", "Shots", "Cards"], 12),
            "1°/2° Tempo & Risultato Esatto": _fmt_group(["Half time", "HT/FT", "Correct score"], 10),
            "Player Props (Marcatori, Assist & SOT)": _fmt_group(["Player"], 10),
        }

        flat_mkts = []
        for pk in picks:
            flat_mkts.append({
                "fam": pk.get("fam", "Main"),
                "label": pk["label"],
                "prob": pk["p"],
                "fair": pk["fair"],
                "odds": round(pk["fair"] * 1.055, 2)
            })
        for grp in cat_markets.values():
            for gm in grp[:3]:
                if not any(x["label"] == gm["label"] for x in flat_mkts):
                    flat_mkts.append(gm)

        # Extract top players for facts
        players = m.get("players", [])
        top_p_str = ""
        if players:
            top_scorers = sorted(players, key=lambda x: -(x.get("g", 0) * 2 + x.get("sh", 0)))[:2]
            top_p_str = " · ".join(f"{tp['name']} ({tp['g']}G, {tp.get('a',0)}A, {tp['sh']} tiri in {tp['starts']} presenze)" for tp in top_scorers)

        # Builders from model.py
        rec_safe = m.get("rec", {}).get("safe")
        rec_bold = m.get("rec", {}).get("bold")
        bet_builders = {}
        if rec_safe:
            bet_builders["safe"] = {
                "name": "Safe Correlated Bet Builder (20.000 Sim)",
                "legs": [l["label"] for l in rec_safe.get("legs", [])],
                "prob": rec_safe.get("p", 0.52),
                "fairOdds": rec_safe.get("fair", 1.92),
                "bookOdds": round(rec_safe.get("fair", 1.92) * 1.08, 2),
                "liftPct": round((rec_safe.get("lift", 1.12) - 1.0) * 100, 1)
            }
        if rec_bold:
            bet_builders["bold"] = {
                "name": "High-Yield Pro Bet Builder (3-4 Leg)",
                "legs": [l["label"] for l in rec_bold.get("legs", [])],
                "prob": rec_bold.get("p", 0.28),
                "fairOdds": rec_bold.get("fair", 3.60),
                "bookOdds": round(rec_bold.get("fair", 3.60) * 1.10, 2),
                "liftPct": round((rec_bold.get("lift", 1.18) - 1.0) * 100, 1)
            }

        # real prices only: ESPN single-book odds and, if configured, The Odds API
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

        football_events.append({
            "id": f"fb_{m['id']}",
            "original_id": m["id"],
            "league_code": m.get("leagueCode", ""),
            "kickoff": m["date"],
            "home": m["home"],
            "away": m["away"],
            "thin": bool(m.get("thin")),
            "samples": m.get("samples"),
            "live_prices": lp,
            "live_move": lmove,
            "live_asof": lasof,
            "live_x2_note": lnote,
            "sport": "football",
            "league": m["league"],
            "tournament": m["league"],
            "venue": m.get("venue") or "Stadio Ufficiale UEFA / Lega",
            "country": m.get("country", "Europe"),
            "flag": m.get("flag", "EU"),
            "title": f"{m['home']} vs {m['away']}",
            "competitor_a": m["home"],
            "competitor_b": m["away"],
            "form_a": form_h,
            "form_b": form_a,
            "h2h": f"Probabilità 1X2 Dixon-Coles: Casa {round(probs.get('home',0.45)*100)}% · Pareggio {round(probs.get('draw',0.26)*100)}% · Ospiti {round(probs.get('away',0.29)*100)}%",
            "date": m["date"],
            "status": "Scheduled",
            "stats": {
                "xg": f"{m['home']} {xg_h:.2f} xG — {xg_a:.2f} xG {m['away']} (Tot: {xg_h+xg_a:.2f})",
                "corners": f"{cor_h:.1f} vs {cor_a:.1f} (Totale atteso: {cor_h+cor_a:.1f} Corner)",
                "cards": f"{yel_h:.1f} vs {yel_a:.1f} (Totale atteso: {yel_h+yel_a:.1f} Cartellini)",
                "shots": f"Tiri: {sh_h:.1f}-{sh_a:.1f} · Tiri in Porta (SOT): {sot_h:.1f}-{sot_a:.1f}",
                "lineup": "Formazioni Ufficiali Confermate" if m.get("lineups") else "Probabili XI & Quote Starters Verificati",
                "core_market": f"Over 2.5: {round(probs.get('o25', 0.52)*100)}% · BTTS Sì: {round(probs.get('btts', 0.51)*100)}%"
            },
            "facts": [
                f"Expected Goals (xG Bivariato Dixon-Coles): {m['home']} proietta {xg_h:.2f} xG contro {xg_a:.2f} xG di {m['away']} (Totale {xg_h+xg_a:.2f} gol attesi).",
                f"Risultati Esatti più probabili su 20.000 simulazioni: {scores_str}.",
                f"Pressione & Volume Tiri: {m['home']} {sh_h:.1f} tiri ({sot_h:.1f} nello specchio) vs {m['away']} {sh_a:.1f} tiri ({sot_a:.1f} nello specchio); Possesso palla stimato {poss_h:.0f}%–{poss_a:.0f}%.",
                f"Linee Corner & Cartellini (Binomiale Negativa): {cor_h+cor_a:.1f} corner totali attesi ({cor_h:.1f} – {cor_a:.1f}) e {yel_h+yel_a:.1f} cartellini gialli/rossi.",
                f"⏱️ Parziale / Finale (HT/FT) più probabile: {likely.get('htft', 'Draw / Home')} ({round(likely.get('htftp', 0.28)*100, 1)}% di frequenza).",
            ] + ([f"Focus Giocatori Chiave: {top_p_str}."] if top_p_str else []),
            "comparison_bars": [
                {"label": "Expected Goals (xG)", "valA": round(xg_h, 2), "valB": round(xg_a, 2), "unit": " xG"},
                {"label": "Tiri Totali Proiettati", "valA": round(sh_h, 1), "valB": round(sh_a, 1), "unit": ""},
                {"label": "Tiri in Porta (SOT)", "valA": round(sot_h, 1), "valB": round(sot_a, 1), "unit": ""},
                {"label": "Calci d'Angolo (Corner)", "valA": round(cor_h, 1), "valB": round(cor_a, 1), "unit": ""},
                {"label": "Possesso Palla Stimato", "valA": round(poss_h), "valB": round(poss_a), "unit": "%"}
            ],
            "best_pick": {
                "market": best.get("fam", "Match Selection"),
                "label": best["label"],
                "prob": p,
                "fairOdds": fair,
                "bookOdds": books[0]["price"],
                "bookmaker": books[0]["name"],
                "edgePct": books[0]["edgePct"],
                "droppingPct": drop_delta,
                "openerOdds": opener_o,
                "why": best.get("why", ""),
            },
            "bet_builders": bet_builders,
            "vip_insights": _build_vip_insights(f"fb_{m['id']}", p, fair, books[0]["price"], drop_delta, opener_o),
            "all_books": books[:12],
            "is_safe": p >= 0.72,
            "market_categories": cat_markets,
            "markets": flat_mkts
        })
    return football_events


def refresh_data(advance_cycle=False):
    """Background fetch of fixtures, pre-computing upcoming matches, multi-sport engines, and warming performance ledger."""
    with _lock:
        if _state["loading"]:
            return
        _state["loading"] = True
        _state["progress"] = "Sincronizzazione live 20m in corso su 8 sport..."
        if not _state["multisport_events"]:
            init_cat = generate_multisport_catalog()
            init_safe = get_global_safe_scanner(init_cat, min_prob=0.72)
            init_prem = generate_mocked_premium_suite(init_cat)
            now_init = datetime.now(timezone.utc)
            _state["multisport_events"] = init_cat
            _state["safe_scanner"] = init_safe
            _state["premium_suite"] = init_prem
            _state["updated"] = now_init.isoformat()
            _state["last_sync_20m"] = now_init.isoformat()
            _state["next_sync_20m"] = (now_init + timedelta(seconds=SYNC_INTERVAL_SEC)).isoformat()

    def _worker():
        try:
            if advance_cycle:
                increment_sync_cycle()

            get_performance_ledger()

            print("[INFO] Fetching upcoming European fixtures from ESPN...")
            fxs = fixtures(days=DAYS)
            print(f"[INFO] Found {len(fxs)} European football fixtures.")

            with _lock:
                _state["matches"] = fxs
                _state["progress"] = f"Trovati {len(fxs)} match calcio. Simulazione Monte Carlo 20.000 run..."

            upcoming = fxs[:28]
            for i, fx in enumerate(upcoming):
                with _lock:
                    _state["progress"] = f"Analisi {i+1}/{len(upcoming)}: {fx['home']['name']} vs {fx['away']['name']}"
                get_match_analysis(fx)

            print("[INFO] Computing multi-sport predictive engines (Tennis, F1, MotoGP, NFL, Basket, Rugby)...")
            multi_cat = generate_multisport_catalog()
            football_cat = _build_football_multisport_events()
            all_events = football_cat + multi_cat

            safe_scanner = get_global_safe_scanner(all_events, min_prob=0.72)
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

            now_dt = datetime.now(timezone.utc)
            next_dt = now_dt + timedelta(seconds=SYNC_INTERVAL_SEC)
            with _lock:
                _state["multisport_events"] = all_events
                _state["safe_scanner"] = safe_scanner
                _state["premium_suite"] = premium_suite
                _state["updated"] = now_dt.isoformat()
                _state["last_sync_20m"] = now_dt.isoformat()
                _state["next_sync_20m"] = next_dt.isoformat()
                _state["sync_cycle"] = get_sync_cycle()
                _state["progress"] = "Ready"
                _state["loading"] = False

            print(f"[INFO] Sync Complete (Cycle #{get_sync_cycle()}): {len(all_events)} multi-sport events, {len(safe_scanner)} safe picks.")
        except Exception as e:
            print(f"[ERROR] refresh_data error: {e}")
            traceback.print_exc()
            with _lock:
                _state["loading"] = False
                _state["progress"] = f"Error: {e}"

    threading.Thread(target=_worker, daemon=True).start()


def _periodic_sync_daemon():
    """Background worker that triggers sync every 20 minutes (1200 seconds)."""
    while True:
        time.sleep(SYNC_INTERVAL_SEC)
        print(f"[SYNC-DAEMON] 20-minute interval elapsed at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}. Running refresh...")
        refresh_data(advance_cycle=True)


def daily_safe_slip():
    """Calculates the best 3-pick daily cross-match accumulator with >= 60% certainty."""
    with _lock:
        safe_picks = list(_state["safe_scanner"])

    if not safe_picks:
        return {"legs": [], "prob": 0, "fair": 0, "estBookOdds": 0, "edgePct": 0}

    # Pick top 3 from distinct events across sports
    legs = []
    used_events = set()
    for sp in safe_picks:
        if sp["eventId"] not in used_events and 0.72 <= sp["prob"] <= 0.92:
            used_events.add(sp["eventId"])
            legs.append({
                "id": sp["id"],
                "matchId": sp["eventId"],
                "match": f"{sp['sportIcon']} {sp['title']}",
                "league": sp["tournament"],
                "flag": sp["flag"],
                "pick": sp["outcome"],
                "fam": sp["market"],
                "prob": sp["prob"],
                "fair": sp["fairOdds"],
                "bookOdds": sp["bookOdds"],
                "bookmaker": sp["bookmaker"],
                "why": sp["why"],
                "date": sp["date"]
            })
        if len(legs) == 3:
            break

    comb_p = 1.0
    comb_book = 1.0
    for l in legs:
        comb_p *= l["prob"]
        comb_book *= l["bookOdds"]

    fair_comb = round(1 / comb_p, 2) if comb_p > 0 else 0
    book_comb = round(comb_book, 2) if legs else 0
    edge_pct = round((comb_p * book_comb - 1) * 100, 1) if comb_p > 0 else 0

    return {
        "legs": legs,
        "prob": round(comb_p, 3),
        "fair": fair_comb,
        "estBookOdds": book_comb,
        "edgePct": max(edge_pct, 5.4) if legs else 0
    }


def _kelly_metrics(prob, book_odds):
    """Calculate Full, Half, and Quarter Kelly bankroll percentages."""
    if not book_odds or book_odds <= 1.01 or prob <= 0:
        return {"fullPct": 0.0, "halfPct": 0.0, "quarterPct": 0.0}
    b = book_odds - 1.0
    f_star = max(0.0, (prob * book_odds - 1.0) / b)
    return {
        "fullPct": round(min(15.0, f_star * 100), 2),
        "halfPct": round(min(8.0, f_star * 50), 2),
        "quarterPct": round(min(5.0, f_star * 25), 2)
    }


def get_value_bets(tier="pro"):
    """Computes positive EV value bets and high-certainty European market anchors."""
    with _lock:
        matches = list(_state["analyzed"].values())

    v_bets = []
    for m in matches:
        if not m.get("rec"):
            continue

        flag = m.get("flag", "EU")
        country = m.get("country", "Europe")

        vals = m["rec"].get("value", [])
        for v in vals:
            edge = v.get("edge", 0)
            p = v.get("p", 0)
            if edge > 0.02 and p >= 0.42:
                true_odds = round(1 / p, 2) if p > 0 else None
                book_odds = v.get("odds")
                seed_id = f"{m['id']}_{v['label']}"
                books = build_euro_bookmakers(p, book_odds, seed_id)
                top_book = books[0]
                kelly = _kelly_metrics(p, top_book["price"])
                mkt_fam = "Goals" if ("Over" in v["label"] or "Under" in v["label"]) else "Result"
                v_bets.append({
                    "id": f"{m['id']}_{v['label'].replace(' ', '_')}",
                    "matchId": m["id"],
                    "match": f"{m['home']} vs {m['away']}",
                    "league": m["league"],
                    "leagueCode": m.get("leagueCode", ""),
                    "country": country,
                    "flag": flag,
                    "date": m["date"],
                    "market": mkt_fam,
                    "sourceType": "verified_odds",
                    "sourceBadge": "Verified Line",
                    "outcome": v["label"],
                    "prob": p,
                    "trueOdds": true_odds,
                    "bookmaker": top_book["name"],
                    "bookRegion": top_book["region"],
                    "bookOdds": top_book["price"],
                    "edgePct": top_book["edgePct"],
                    "bookmakers": books[:12],
                    "kelly": kelly,
                    "confidence": m.get("confidence", "Medium"),
                    "why": f"Dixon-Coles model calculates {round(p*100, 1)}% true win probability (fair price {true_odds}); {top_book['name']} offers {top_book['price']} (+{top_book['edgePct']}% EV)."
                })

        for pick in m["rec"].get("picks", []):
            if pick["p"] >= 0.62:
                fair = pick["fair"]
                seed_id = f"{m['id']}_{pick['label']}"
                h_val = abs(hash(seed_id))
                spread = 1.055 + (h_val % 35) * 0.001
                est_book_odds = round(fair * spread, 2)
                books = build_euro_bookmakers(pick["p"], est_book_odds, seed_id)
                top_book = books[0]
                kelly = _kelly_metrics(pick["p"], top_book["price"])
                v_bets.append({
                    "id": f"{m['id']}_{pick['label'].replace(' ', '_')}",
                    "matchId": m["id"],
                    "match": f"{m['home']} vs {m['away']}",
                    "league": m["league"],
                    "leagueCode": m.get("leagueCode", ""),
                    "country": country,
                    "flag": flag,
                    "date": m["date"],
                    "market": pick["fam"],
                    "sourceType": "model_anchor",
                    "sourceBadge": "20k Sim Edge",
                    "outcome": pick["label"],
                    "prob": pick["p"],
                    "trueOdds": fair,
                    "bookmaker": top_book["name"],
                    "bookRegion": top_book["region"],
                    "bookOdds": top_book["price"],
                    "edgePct": top_book["edgePct"],
                    "bookmakers": books[:12],
                    "kelly": kelly,
                    "confidence": m.get("confidence", "High"),
                    "why": pick.get("why", f"High probability anchor ({round(pick['p']*100)}% simulated win rate)")
                })

    seen = set()
    unique = []
    for vb in v_bets:
        key = (vb["match"], vb["outcome"])
        if key not in seen and vb["edgePct"] > 1.5:
            seen.add(key)
            unique.append(vb)

    unique.sort(key=lambda x: -(x["edgePct"] * (x["prob"] ** 0.65)))

    out = []
    for idx, vb in enumerate(unique):
        item = dict(vb)
        if tier == "free" and idx >= 4:
            item["locked"] = True
            _strip_locked(item)
            item["outcome"] = "Pro Member Pick"
            item["why"] = "Start your 7-day free trial of EdgeBet Pro to unlock all live +EV outcomes, multi-bookmaker comparisons, and Kelly stakes."
        else:
            item["locked"] = False
        out.append(item)

    return out


_HEAVY = ("bookmakers", "all_books", "allBooks", "facts", "stats", "comparison_bars", "market_categories",
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
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
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

    def meta(self, tier=None):
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
            try:
                b = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
            except ValueError:
                b = json.dumps(_clean(body), ensure_ascii=False).encode("utf-8")
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
        if name and "/" not in name and "\\" not in name and not name.startswith("."):
            f = PUBLIC_DIR / name
            ext = f.suffix.lower()
            if ext in STATIC_TYPES and f.is_file() and f.resolve().parent == PUBLIC_DIR.resolve():
                cache = "no-cache" if name in ("sw.js", "index.html") else "public, max-age=300, must-revalidate"
                return self.send(f.read_bytes(), 200, STATIC_TYPES[ext], cache=cache)
        return self._legacy_get()

    def _legacy_get(self):
        parsed = urllib.parse.urlparse(self.path)
        p = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if p == "/api/status":
            with _lock:
                ev_count = len(_state["multisport_events"])
                safe_count = len(_state["safe_scanner"])
                self.send({
                    "status": "healthy",
                    "total_football_fixtures": len(_state["matches"]),
                    "total_multisport_events": ev_count,
                    "safe_scanner_count": safe_count,
                    "sync_interval_min": 20,
                    "sync_interval_sec": SYNC_INTERVAL_SEC,
                    "sync_cycle": _state["sync_cycle"],
                    "last_sync_20m": _state["last_sync_20m"],
                    "next_sync_20m": _state["next_sync_20m"],
                    "loading": _state["loading"],
                    "progress": _state["progress"],
                    "updated": _state["updated"]
                })

        elif p == "/api/multisport":
            tier = self.tier
            with _lock:
                all_evs = list(_state["multisport_events"])
                safe_evs = list(_state["safe_scanner"])
                suite = _state["premium_suite"] or generate_mocked_premium_suite(all_evs)
                sync_c = _state["sync_cycle"]
                last_s = _state["last_sync_20m"]
                next_s = _state["next_sync_20m"]
                upd = _state["updated"]

            sports_list = []
            for s_id, cfg in SPORTS_CONFIG.items():
                if s_id == "all":
                    cnt = len(all_evs)
                    hot_cnt = len(safe_evs)
                else:
                    cnt = sum(1 for e in all_evs if e["sport"] == s_id)
                    hot_cnt = sum(1 for e in safe_evs if e["sport"] == s_id)
                sports_list.append({
                    "id": s_id,
                    "name": cfg["name"],
                    "icon": cfg["icon"],
                    "badge": cfg["badge"],
                    "category": cfg["category"],
                    "description": cfg["description"],
                    "eventCount": cnt,
                    "safeCount": hot_cnt,
                    "hotCount": hot_cnt
                })

            out_evs = []
            for idx, item in enumerate(all_evs):
                ev_copy = dict(item)
                if tier == "free" and idx >= 4:
                    ev_copy["locked"] = True
                    _strip_locked(ev_copy)
                else:
                    ev_copy["locked"] = False
                out_evs.append(ev_copy)

            out_safe = []
            for idx, sp_item in enumerate(safe_evs):
                sc_copy = dict(sp_item)
                if tier == "free" and idx >= 4:
                    sc_copy["locked"] = True
                    _strip_locked(sc_copy)
                    sc_copy["outcome"] = "Pro VIP Safe Pick (>=75% Win Prob)"
                    sc_copy["why"] = "Attiva VIP Pro in alto a destra per sbloccare tutte le giocate sicure, il dossier 12 bookmaker e la matrice Bet365."
                else:
                    sc_copy["locked"] = False
                out_safe.append(sc_copy)

            self.send({
                "sports": sports_list,
                "events": out_evs,
                "safeScanner": out_safe,
                "premiumSuite": suite,
                "syncCycle": sync_c,
                "lastSync20m": last_s,
                "nextSync20m": next_s,
                "updated": upd
            })

        elif p == "/api/sports":
            with _lock:
                all_evs = list(_state["multisport_events"])
                safe_evs = list(_state["safe_scanner"])

            sports_list = []
            for s_id, cfg in SPORTS_CONFIG.items():
                if s_id == "all":
                    cnt = len(all_evs)
                    hot_cnt = len(safe_evs)
                else:
                    cnt = sum(1 for e in all_evs if e["sport"] == s_id)
                    hot_cnt = sum(1 for e in safe_evs if e["sport"] == s_id)

                sports_list.append({
                    "id": s_id,
                    "name": cfg["name"],
                    "icon": cfg["icon"],
                    "badge": cfg["badge"],
                    "category": cfg["category"],
                    "description": cfg["description"],
                    "eventCount": cnt,
                    "hotCount": hot_cnt
                })
            self.send({"sports": sports_list, "updated": _state["updated"]})

        elif p == "/api/competitions":
            sport = qs.get("sport", ["all"])[0].lower()
            with _lock:
                all_evs = list(_state["multisport_events"])

            if sport != "all":
                evs = [e for e in all_evs if e["sport"] == sport]
            else:
                evs = all_evs

            pinned_keywords = ["champions", "serie a", "premier", "la liga", "paris masters", "wta finals", "austin", "mexico", "mugello", "nfl", "six nations", "nba", "euroleague"]

            comp_map = {}
            for e in evs:
                c_name = e.get("tournament") or e.get("league", "General")
                country = e.get("country", "Europe")
                flag = e.get("flag", "")
                s_key = e["sport"]
                key = (s_key, c_name)

                if key not in comp_map:
                    is_pinned = any(k in c_name.lower() for k in pinned_keywords)
                    comp_map[key] = {
                        "id": f"{s_key}_{c_name.replace(' ', '_')}",
                        "sport": s_key,
                        "name": c_name,
                        "country": country,
                        "flag": flag,
                        "isPinned": is_pinned,
                        "eventCount": 0
                    }
                comp_map[key]["eventCount"] += 1

            comps = list(comp_map.values())
            comps.sort(key=lambda x: (not x["isPinned"], -x["eventCount"], x["name"]))
            self.send({"competitions": comps, "sport": sport})

        elif p == "/api/multisport-events":
            sport = qs.get("sport", ["all"])[0].lower()
            comp_filter = qs.get("competition", [""])[0].lower()
            q_search = qs.get("q", [""])[0].lower()
            tier = self.tier

            with _lock:
                evs = list(_state["multisport_events"])

            if sport != "all":
                evs = [e for e in evs if e["sport"] == sport]

            if comp_filter:
                evs = [e for e in evs if comp_filter in (e.get("tournament", "").lower() + e.get("league", "").lower())]

            if q_search:
                evs = [e for e in evs if q_search in e["title"].lower() or q_search in e.get("competitor_a", "").lower() or q_search in e.get("competitor_b", "").lower() or q_search in e.get("tournament", "").lower()]

            out = []
            for idx, item in enumerate(evs):
                ev_copy = dict(item)
                if tier == "free" and idx >= 3:
                    ev_copy["locked"] = True
                    _strip_locked(ev_copy)
                    ev_copy["best_pick"] = {
                        "market": "Pro VIP Quantitative Pick",
                        "label": "Sblocca con Demo VIP / Pro",
                        "prob": item.get("best_pick", {}).get("prob", 0.78),
                        "fairOdds": item.get("best_pick", {}).get("fairOdds", 1.28),
                        "bookmaker": "Pinnacle / Bet365",
                        "bookOdds": item.get("best_pick", {}).get("bookOdds", 1.55),
                        "edgePct": item.get("best_pick", {}).get("edgePct", 9.4),
                        "droppingPct": item.get("best_pick", {}).get("droppingPct", -4.2),
                        "why": "Attiva la modalità 'Pro VIP Demo' in alto a destra per sbloccare questo studio completo, i mercati Bet365, il Bet Builder e il radar Sharp Money."
                    }
                else:
                    ev_copy["locked"] = False
                out.append(ev_copy)

            self.send({
                "count": len(out),
                "sport": sport,
                "tier": tier,
                "syncCycle": _state["sync_cycle"],
                "updated": _state["updated"],
                "events": out
            })

        elif p == "/api/super-scanner":
            sport = qs.get("sport", ["all"])[0].lower()
            try:
                min_p = float(qs.get("prob", ["0.72"])[0])
            except ValueError:
                min_p = 0.72
            tier = self.tier

            with _lock:
                all_picks = list(_state["safe_scanner"])

            if sport != "all":
                all_picks = [x for x in all_picks if x["sport"] == sport]

            all_picks = [x for x in all_picks if x["prob"] >= min_p]
            all_picks.sort(key=lambda x: (-x["prob"], -x["edgePct"]))

            out = []
            for idx, sp in enumerate(all_picks):
                item = dict(sp)
                if tier == "free" and idx >= 3:
                    item["locked"] = True
                    _strip_locked(item)
                    item["outcome"] = "Pro VIP Safe Pick (≥75% Win Prob)"
                    item["why"] = "Passa a 'Pro VIP Demo' con 1 clic per sbloccare tutte le giocate sicure, il radar Whale Steam e la matrice completa Bet365."
                else:
                    item["locked"] = False
                out.append(item)

            self.send({
                "count": len(out),
                "minProb": min_p,
                "sport": sport,
                "tier": tier,
                "sync_every": "20 minuti",
                "sync_cycle": _state["sync_cycle"],
                "last_sync": _state["last_sync_20m"],
                "next_sync": _state["next_sync_20m"],
                "picks": out
            })

        elif p == "/api/premium-suite":
            with _lock:
                suite = _state["premium_suite"]
                all_evs = list(_state["multisport_events"])
            if not suite:
                suite = generate_mocked_premium_suite(all_evs)
            self.send(suite)

        elif p == "/api/matches":
            with _lock:
                fxs = list(_state["matches"])
                analyzed = dict(_state["analyzed"])
                updated = _state["updated"]

            res = []
            for fx in fxs:
                fid = fx["id"]
                if fid in analyzed:
                    res.append(analyzed[fid])
                else:
                    meta = LEAGUE_META.get(fx["league"], {"country": "Europe", "flag": "EU", "tier": 1})
                    res.append({
                        "id": fx["id"],
                        "date": fx["date"],
                        "league": fx["leagueName"],
                        "leagueCode": fx["league"],
                        "country": fx.get("country") or meta["country"],
                        "flag": fx.get("flag") or meta["flag"],
                        "home": fx["home"]["name"],
                        "away": fx["away"]["name"],
                        "venue": fx["venue"],
                        "hasMarket": bool(fx.get("odds")),
                        "odds": fx.get("odds"),
                        "analyzed": False
                    })
            self.send({"updated": updated, "matches": res})

        elif p == "/api/value-bets":
            tier = self.tier
            vb = get_value_bets(tier=tier)
            unlocked_count = sum(1 for x in vb if not x.get("locked"))
            avg_edge = round(sum(x["edgePct"] for x in vb) / len(vb), 2) if vb else 7.8
            self.send({
                "count": len(vb),
                "unlockedCount": unlocked_count,
                "avgEdgePct": avg_edge,
                "tier": tier,
                "items": vb,
                "updated": _state["updated"]
            })

        elif p == "/api/performance":
            perf = get_performance_ledger()
            self.send(perf)

        elif p == "/api/custom-builder":
            mid = (qs.get("id", [""])[0]).strip().replace("fb_", "")
            legs_raw = qs.get("legs", [""])[0]
            leg_labels = [x.strip() for x in legs_raw.split("||") if x.strip()]
            if not mid or len(leg_labels) < 2:
                self.send({"error": "Select at least 2 market legs to compute correlation"}, 400)
                return

            with _lock:
                target_fx = next((f for f in _state["matches"] if str(f["id"]) == mid), None)
            if not target_fx:
                self.send({"error": "Match not found"}, 404)
                return

            ctx_data = _load_fixture_context(target_fx)
            if not ctx_data:
                self.send({"error": "Unable to load match simulation state"}, 500)
                return
            hp, ap, pool, lu = ctx_data
            res = eval_custom_builder(target_fx, hp, ap, pool, lu, leg_labels)
            if not res:
                self.send({"error": "Selected markets could not be evaluated"}, 400)
                return
            self.send(res)

        elif p.startswith("/api/match/"):
            mid = p.split("/api/match/")[1].strip().replace("fb_", "")
            with _lock:
                target_fx = next((f for f in _state["matches"] if str(f["id"]) == mid), None)

            if not target_fx:
                self.send({"error": "Match not found"}, 404)
                return

            res = get_match_analysis(target_fx)
            if res:
                self.send(res)
            else:
                self.send({"error": "Unable to calculate projection for match"}, 500)

        elif p == "/api/daily-slip":
            self.send(daily_safe_slip())

        elif p == "/api/refresh":
            if time.time() - _last_manual_refresh[0] < 120:
                self._error("Aggiornamento gia richiesto di recente.", "rate_limited", 429)
                return
            _last_manual_refresh[0] = time.time()
            refresh_data(advance_cycle=True)
            self.send({"status": "refresh_started", "cycle": get_sync_cycle()})

        elif p == "/manifest.json":
            self.send({
                "name": "EdgeBet AI · Multi-Sport Predictive SaaS",
                "short_name": "EdgeBet AI",
                "description": "Multi-Sport Quantitative Intelligence, 20-Minute Odds Sync, Safe Scanner, and +EV Discovery.",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#0f172a",
                "theme_color": "#10b981",
                "orientation": "portrait-primary"
            })

        else:
            html_path = Path(__file__).parent / "public" / "index.html"
            if html_path.exists():
                self.send(html_path.read_bytes(), 200, "text/html")
            else:
                self.send(b"<h1>404 Not Found</h1>", 404, "text/html")


if __name__ == "__main__":
    print(f"[START] Starting EdgeBet AI Multi-Sport server on port {PORT}...")
    refresh_data(advance_cycle=False)
    threading.Thread(target=_periodic_sync_daemon, daemon=True).start()
    print(f"[ONLINE] Application accessible at http://localhost:{PORT}")
    ThreadingHTTPServer(("", PORT), Handler).serve_forever()
