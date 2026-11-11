"""Builders for the /api/v1 payloads (feed rows, detail tabs, ledger, backtest summary, method, premium).

Honesty rules enforced here:
* a price is `live` only when it comes from a real feed; otherwise the pick carries the model's fair odds only;
* edge / movement / best book are null unless live;
* demo (non-football) events are always flagged `dataStatus: "demo"`;
* free-tier locked rows are redacted server side.
"""
import re
from datetime import datetime, timedelta, timezone

from engine import store

# --------------------------------------------------------------------- lookups
COUNTRY_ISO = {
    "England": "GB", "United Kingdom": "GB", "Scotland": "GB", "Spain": "ES", "Italy": "IT", "Germany": "DE",
    "France": "FR", "Netherlands": "NL", "Portugal": "PT", "Europe": "EU", "United States": "US", "Mexico": "MX",
    "Saudi Arabia": "SA", "Switzerland": "CH", "Greece": "GR", "Turkey": "TR", "Austria": "AT", "Belgium": "BE",
    "Denmark": "DK", "Norway": "NO", "Sweden": "SE", "Japan": "JP", "Australia": "AU", "Brazil": "BR",
    "Argentina": "AR", "Monaco": "MC", "Qatar": "QA", "Bahrain": "BH", "Canada": "CA", "Hungary": "HU",
}
MODELS = {
    "football": ("Dixon-Coles + Binomiale Negativa, 20.000 simulazioni", "validated"),
    "tennis": ("Catena di Markov servizio/risposta (formula chiusa)", "demo"),
    "f1": ("Punteggio passo gara + softmax (formula chiusa)", "demo"),
    "motogp": ("Punteggio passo gara + softmax (formula chiusa)", "demo"),
    "nfl": ("Yards per play e turnover verso punti attesi (formula chiusa)", "demo"),
    "basketball": ("Pace x rating offensivo/difensivo (formula chiusa)", "demo"),
    "rugby": ("Fasi statiche e disciplina (formula chiusa)", "demo"),
}
SPORT_ORDER = ["football", "tennis", "f1", "motogp", "nfl", "basketball", "rugby"]
BOOK_REGION = {
    "Bet365": "UK / Pan-Europa", "Pinnacle": "Sharp globale", "Betfair Exchange": "Exchange", "Unibet": "UE / Nordici",
    "DraftKings": "US", "FanDuel": "US", "Polymarket": "Mercato predittivo", "Winamax": "FR / ES / IT",
    "Tipico": "DE / AT", "Betsson": "Nordici / UE", "William Hill": "UK / IE / IT", "bwin": "Pan-Europa",
}
STAT_LABELS = {
    "surface": "Superficie e CPI", "serve_a": "1a di servizio (A)", "serve_b": "1a di servizio (B)",
    "bp_saved_a": "Palle break salvate (A)", "bp_saved_b": "Palle break salvate (B)", "fatigue": "Fatica nel torneo",
    "expected_games": "Giochi totali attesi", "tiebreak_risk": "Probabilita tie-break", "xg": "Gol attesi (xG)",
    "corners": "Calci d'angolo attesi", "cards": "Cartellini attesi", "shots": "Tiri e tiri in porta",
    "lineup": "Formazioni", "core_market": "Mercati gol principali", "proj_score": "Punteggio proiettato",
    "spread": "Handicap del modello", "total_points": "Punti totali stimati", "pace": "Ritmo partita",
    "b2b": "Riposo / back-to-back", "margin": "Margine di vittoria", "scrum": "Fasi statiche",
    "sin_bin": "Disciplina e sin bin", "weather": "Meteo", "epa_matchup": "Efficienza yards/play",
    "red_zone": "Efficienza red zone", "turnovers": "Differenziale turnover", "injuries": "Infortuni QB/OL",
    "winner_fav": "Favorito della gara", "podium_top": "Podio atteso", "safety_car": "Rischio safety car",
    "track_cond": "Asfalto e meteo", "tire_strategy": "Degrado gomme",
}
_IT = [
    (r" to win to nil", " vince senza subire"), (r" to win", " vince"), (r"^Draw$", "Pareggio"), (r" or draw", " o pareggio"),
    (r"Both teams to score: No", "Entrambe segnano: No"), (r"Both teams to score", "Entrambe segnano"),
    (r" clean sheet", " porta inviolata"), (r"shots on target", "tiri in porta"), (r"total shots", "tiri totali"),
    (r"\bshots\b", "tiri"), (r"\bcorners\b", "calci d'angolo"), (r"\bcards\b", "cartellini"), (r"\bgoals\b", "gol"),
    (r"1st half result:", "Esito 1T:"), (r"2nd half result:", "Esito 2T:"), (r"1st half", "1T"), (r"2nd half", "2T"),
    (r"to score in both halves", "segna in entrambi i tempi"), (r"Both halves same goals", "Stessi gol nei due tempi"),
    (r"Goal in both halves", "Gol in entrambi i tempi"), (r"Highest scoring half: 1st", "Tempo con piu gol: 1T"),
    (r"Highest scoring half: 2nd", "Tempo con piu gol: 2T"), (r"HT/FT", "1T/Finale"), (r"Correct score", "Risultato esatto"),
    (r"Exactly (\d) gol", r"Esattamente \1 gol"), (r"5\+ gol", "5+ gol"), (r"A red card shown", "Almeno un'espulsione"),
    (r"Most calci d'angolo:", "Piu calci d'angolo:"), (r"Asian over", "Asian over"), (r"Asian under", "Asian under"),
    (r"draw no bet", "pareggio rimborsato"), (r"to provide an assist", "fa un assist"), (r"goal or assist", "gol o assist"),
    (r"to be carded", "ammonito"), (r"\bto score\b", "segna"), (r"\(3-way\)", "(3 esiti)"),
]
_IT_RE = [(re.compile(a), b) for a, b in _IT]


def it_label(label):
    s = label
    for rx, rep in _IT_RE:
        s = rx.sub(rep, s)
    return s


def country_iso(ev):
    f = ev.get("flag")
    if isinstance(f, str) and len(f) == 2 and f.isalpha():
        return f.upper()
    return COUNTRY_ISO.get(ev.get("country", ""), "INT")


def confidence(prob, thin=False):
    p = prob - (0.03 if thin else 0)
    return "molto_alta" if p >= 0.85 else "alta" if p >= 0.74 else "media"


def _parse_dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _kickoff(ev):
    return ev.get("kickoff") or ev.get("date")


# ------------------------------------------------------------------------ rows
def _pick(ev):
    bp = ev.get("best_pick") or {}
    prob = float(bp.get("prob") or 0)
    fair = round(1.0 / prob, 2) if prob > 0 else None
    label = bp.get("label", "")
    live = ev.get("live_prices") or []
    out = dict(label=it_label(label) if ev.get("sport") == "football" else label, market=bp.get("market"),
               prob=round(prob, 3), fairOdds=fair, confidence=confidence(prob, ev.get("thin", False)),
               priceSource="live" if live else "modeled", bestOdds=None, bestBook=None, edgePct=None, movementPct=None)
    if live:
        best = live[0]
        out.update(bestOdds=round(best["price"], 2), bestBook=best["name"],
                   edgePct=round((prob * best["price"] - 1) * 100, 1), movementPct=ev.get("live_move"))
    return out


def build_rows(events, tier, now=None):
    now = now or datetime.now(timezone.utc)
    rows = []
    for ev in events:
        ko = _parse_dt(_kickoff(ev))
        if ko is None or ko < now - timedelta(minutes=5):
            continue
        sport = ev.get("sport")
        status = MODELS.get(sport, ("", "demo"))[1]
        pk = _pick(ev)
        if not pk["prob"]:
            continue
        edge = pk["edgePct"] or 0
        score = pk["prob"] + 0.5 * min(max(edge, 0), 20) / 100
        rows.append(dict(
            id=ev["id"], sport=sport, title=ev["title"],
            competitors=[ev.get("competitor_a"), ev.get("competitor_b")],
            competition=ev.get("tournament") or ev.get("league"), country=country_iso(ev),
            kickoff=ko.astimezone(timezone.utc).isoformat(timespec="seconds"), venue=ev.get("venue", ""),
            dataStatus=status, thin=bool(ev.get("thin", False)),
            form={"a": list(ev.get("form_a") or [])[:5], "b": list(ev.get("form_b") or [])[:5]},
            pick=pk, locked=False, _score=(0 if status == "validated" else 1, -score)))
    rows.sort(key=lambda r: r["_score"])
    seen_sport = set()
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        first_of_sport = r["sport"] not in seen_sport
        seen_sport.add(r["sport"])
        if tier == "free" and not (i <= 4 or first_of_sport):
            r["locked"] = True
            for k in ("label", "market", "fairOdds", "bestOdds", "bestBook", "edgePct", "movementPct"):
                r["pick"][k] = None
        del r["_score"]
    return rows


def pick_oggi(rows, now=None):
    now = now or datetime.now(timezone.utc)
    horizon = now + timedelta(hours=36)
    near = [r for r in rows if not r["locked"] and _parse_dt(r["kickoff"]) <= horizon]
    pool = near if len(near) >= 3 else [r for r in rows if not r["locked"]]
    return [r["id"] for r in pool[:3]]


def build_feed(events, tier, meta):
    rows = build_rows(events, tier)
    hot = sum(1 for r in rows if r["dataStatus"] == "validated" and r["pick"]["prob"] >= 0.74)
    live = sum(1 for r in rows if r["pick"]["priceSource"] == "live")
    if live:
        text = f"Oggi {hot} selezioni di calcio con probabilita stimata almeno 74%, {live} confrontate con prezzi live."
    else:
        text = f"Oggi {hot} selezioni di calcio con probabilita stimata almeno 74%. Prezzi live non collegati: vedi la quota equa."
    sports = []
    for sid in SPORT_ORDER:
        sr = [r for r in rows if r["sport"] == sid]
        sports.append(dict(id=sid, name=meta["sportNames"].get(sid, sid), eventCount=len(sr),
                           hotCount=sum(1 for r in sr if r["pick"]["prob"] >= 0.74),
                           dataStatus=MODELS[sid][1], description=meta["sportDesc"].get(sid, "")))
    return dict(
        meta=dict(updated=meta["updated"], nextSync=meta["nextSync"], syncCycle=meta["syncCycle"], tier=tier,
                  demoMode=meta["demoMode"], priceSource="live" if live else "modeled", liveBooks=meta["liveBooks"],
                  currency="EUR", loading=meta["loading"]),
        sports=sports, finding=dict(text=text, hot=hot, live=live), oggi=pick_oggi(rows), rows=rows)


# ---------------------------------------------------------------------- detail
def _ladder(fair, prices):
    vals = [p["price"] for p in prices] + ([fair] if fair else [])
    if not vals:
        return dict(fair=fair, min=None, max=None, minOdds=None)
    lo, hi = min(vals), max(vals)
    pad = max((hi - lo) * 0.12, 0.02)
    return dict(fair=fair, min=round(lo - pad, 2), max=round(hi + pad, 2),
                minOdds=round(fair * 1.03, 2) if fair else None)


def build_detail(ev, tier):
    pk = _pick(ev)
    prob, fair = pk["prob"], pk["fairOdds"]
    sport = ev.get("sport")
    football = sport == "football"
    live = ev.get("live_prices") or []
    asof = ev.get("live_asof")

    if live:
        books = []
        for i, b in enumerate(live):
            books.append(dict(name=b["name"], region=BOOK_REGION.get(b["name"], ""), price=round(b["price"], 2),
                              vigPct=b.get("vigPct"), noVigProb=b.get("noVigProb"),
                              edgePct=round((prob * b["price"] - 1) * 100, 1),
                              movement=ev.get("live_move") if i == 0 else None, source="live", maxStakeEur=None))
        note = f"Prezzi live da {len(books)} bookmaker per questo mercato. Quota minima con vantaggio: {round(fair * 1.03, 2) if fair else '-'}."
    else:
        books = []
        mn = round(fair * 1.03, 2) if fair else None
        note = ("Nessun prezzo live per questo mercato: mostriamo solo la quota equa del modello"
                + (f" ({fair}). Una quota di mercato sotto {mn} non offre un vantaggio statistico." if fair else ".")
                + " Collega un feed quote (ODDS_API_KEY) per il confronto tra bookmaker.")
    shown = books if tier != "free" else books[:3]
    prezzi = dict(priceSource="live" if live else "modeled", asOf=asof, fairOdds=fair, note=note,
                  ladder=_ladder(fair, live), books=shown)

    why = [w for w in [(ev.get("best_pick") or {}).get("why")] if w]
    why = [re.sub(r"\s*[—-]\s*Modello 20\.000 run.*$", "", w).strip() for w in why]
    stats = [dict(label=STAT_LABELS.get(k, k.replace("_", " ").capitalize()), value=str(v))
             for k, v in (ev.get("stats") or {}).items()]
    facts = list(ev.get("facts") or [])
    if ev.get("live_x2_note"):
        facts.append(ev["live_x2_note"])
    model_name, status = MODELS.get(sport, ("", "demo"))
    perche = dict(
        why=why, stats=stats, bars=list(ev.get("comparison_bars") or []), facts=facts,
        model=dict(name=model_name, validated=status == "validated", samples=ev.get("samples"),
                   thin=bool(ev.get("thin", False))))

    cats = []
    for name, items in (ev.get("market_categories") or {}).items():
        its = []
        for m in items:
            lab = m.get("label", "")
            its.append(dict(key=lab, label=it_label(lab) if football else lab, prob=m.get("prob"),
                            fair=m.get("fair"), odds=None))
        cats.append(dict(name=name, items=its))
    if tier == "free":
        builders = {"locked": True}
    else:
        builders = []
        for bb in (ev.get("bet_builders") or {}).values():
            builders.append(dict(name=bb.get("name"), legs=[it_label(x) if football else x for x in bb.get("legs", [])],
                                 prob=bb.get("prob"), fairOdds=bb.get("fairOdds"), liftPct=bb.get("liftPct")))
    mercati = dict(categories=cats, builders=builders)

    if tier == "free":
        sharp = {"locked": True}
    elif len(live) >= 2:
        prices = [b["price"] for b in live]
        avg_vig = round(sum(b["vigPct"] for b in live if b.get("vigPct") is not None) / max(1, sum(1 for b in live if b.get("vigPct") is not None)), 1)
        nv = [b["noVigProb"] for b in live if b.get("noVigProb")]
        cons = sum(nv) / len(nv) if nv else None
        metrics = [dict(label="Bookmaker confrontati", value=str(len(live))),
                   dict(label="Miglior prezzo / peggiore", value=f"{max(prices):.2f} / {min(prices):.2f}"),
                   dict(label="Dispersione prezzi", value=f"{round((max(prices) - min(prices)) / min(prices) * 100, 1)}%"),
                   dict(label="Margine medio (vig)", value=f"{avg_vig}%")]
        if cons:
            metrics.append(dict(label="Probabilita di mercato (no-vig)", value=f"{round(cons * 100, 1)}%"))
            metrics.append(dict(label="Probabilita del modello", value=f"{round(prob * 100, 1)}%"))
        sharp = dict(available=True, metrics=metrics,
                     note="Calcolato dai prezzi live: nessun volume o flusso di denaro viene stimato.")
    else:
        sharp = dict(available=False, metrics=[],
                     note="Servono almeno due bookmaker con prezzi live per misurare margine e dispersione.")
    return dict(id=ev["id"], tier=tier, tabs=dict(prezzi=prezzi, perche=perche, mercati=mercati, sharp=sharp))


# ---------------------------------------------------------------------- proof
def build_ledger():
    rows = store.ledger_rows(60)
    settled = store.settled_predictions()
    n = len(settled)
    summary = dict(settled=n, pending=store.pending_count(), hitRatePct=None, avgProbPct=None, brier=None,
                   logLoss=None, since=store.first_prediction_date())
    calibration = []
    if n:
        import math
        wins = sum(1 for r in settled if r["status"] == "won")
        summary.update(
            hitRatePct=round(wins / n * 100, 1), avgProbPct=round(sum(r["prob"] for r in settled) / n * 100, 1),
            brier=round(sum((r["prob"] - (1 if r["status"] == "won" else 0)) ** 2 for r in settled) / n, 4),
            logLoss=round(sum(-(math.log(max(r["prob"], 1e-9)) if r["status"] == "won" else math.log(max(1 - r["prob"], 1e-9))) for r in settled) / n, 4))
        bins = {}
        for r in settled:
            k = min(int(r["prob"] * 10), 9)
            b = bins.setdefault(k, [0, 0.0, 0])
            b[0] += 1
            b[1] += r["prob"]
            b[2] += 1 if r["status"] == "won" else 0
        calibration = [dict(bin=f"{k * 10}-{k * 10 + 10}%", n=v[0], predictedPct=round(v[1] / v[0] * 100, 1),
                            actualPct=round(v[2] / v[0] * 100, 1)) for k, v in sorted(bins.items())]
    out_rows = [dict(id=r["id"], publishedAt=r["published_at"], kickoff=r["kickoff"], title=r["title"],
                     pick=it_label(r["pick"]), prob=r["prob"], fairOdds=r["fair"], status=r["status"],
                     result=r["result"]) for r in rows]
    return dict(summary=summary, calibration=calibration, rows=out_rows,
                basis="Probabilita registrate prima del calcio d'inizio e liquidate in automatico. Nessun ROI senza quote storiche reali.")


def build_method(price_status, backtest):
    sports = []
    names = {"football": "Calcio", "tennis": "Tennis", "f1": "Formula 1", "motogp": "MotoGP", "nfl": "Football NFL",
             "basketball": "Basket", "rugby": "Rugby"}
    sources = {
        "football": ["ESPN (calendari e statistiche pubbliche)", "Quote: ESPN (singolo bookmaker) e The Odds API se configurata"],
        "tennis": ["Eventi di esempio (nessun feed collegato)"], "f1": ["Eventi di esempio (nessun feed collegato)"],
        "motogp": ["Eventi di esempio (nessun feed collegato)"], "nfl": ["Eventi di esempio (nessun feed collegato)"],
        "basketball": ["Eventi di esempio (nessun feed collegato)"], "rugby": ["Eventi di esempio (nessun feed collegato)"],
    }
    for sid in SPORT_ORDER:
        model, status = MODELS[sid]
        if sid == "football" and backtest and backtest.get("n"):
            val = (f"Backtest walk-forward su {backtest['n']} partite: tasso di successo {backtest['hitRatePct']}% "
                   f"contro probabilita media {backtest['avgProbPct']}%, Brier {backtest['brier']}.")
        else:
            val = "Nessun backtest: eventi dimostrativi, non usare per decisioni reali." if status == "demo" else "Backtest in corso."
        sports.append(dict(id=sid, name=names[sid], dataStatus=status, model=model, sources=sources[sid], validation=val))
    return dict(
        sports=sports,
        priceFeed=dict(configured=price_status["configured"], provider=price_status.get("provider"),
                       books=price_status.get("books", []), lastOk=price_status.get("lastOk"),
                       lastError=price_status.get("lastError")),
        disclaimers=[
            "EdgeBet AI e un servizio di analisi statistica: non accetta scommesse e non e un operatore di gioco.",
            "La probabilita stimata non e certezza: anche una selezione al 90% perde una volta su dieci.",
            "Le quote equa e il vantaggio statistico dipendono dal modello e possono essere sbagliati.",
            "Servizio riservato ai maggiorenni. Gioca solo cio che puoi permetterti di perdere."],
        responsibleGambling=[
            dict(label="Gioco Responsabile (Italia)", url="https://www.giocoresponsabile.it"),
            dict(label="BeGambleAware (UK)", url="https://www.begambleaware.org"),
            dict(label="GamCare (UK)", url="https://www.gamcare.org.uk")])


def build_premium(suite, tier):
    demo_teaser = dict(arbitrage=len(suite.get("arbitrage", [])), flows=len(suite.get("whaleSteam", [])),
                       props=len(suite.get("vipPlayerProps", [])))
    if tier == "free":
        return dict(locked=True, demo=True, teaser=demo_teaser)
    return dict(demo=True, arbitrage=suite.get("arbitrage", []), flows=suite.get("whaleSteam", []),
                props=suite.get("vipPlayerProps", []))

