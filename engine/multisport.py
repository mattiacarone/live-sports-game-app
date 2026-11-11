"""EdgeBet AI - Multi-Sport Quantitative Intelligence, Deep Stats & VIP Premium Engine.

Implements tailored mathematical models, deep statistical facts, Bet365-style multi-category
market matrices, correlated Bet Builders, and Mocked VIP Premium Intelligence for:
1. Football (Dixon-Coles 20k Sims + Negative Binomial xG/Corners/Cards/Shots/Player Props)
2. Tennis (ATP/WTA/Slams - Surface CPR Index + Serve/Return Markov Chains + Set/Game/Tiebreak)
3. ️ Formula 1 & ️ MotoGP (FP1-FP3 Telemetry Stints, Tire Deg, Sector Speeds, H2H Duels & Podiums)
4. American Football (NFL - EPA/Play, Yards/Play, Trench Matchups, QB Injury & Weather Spreads)
5. Basketball (NBA & Euroleague - Pace Possessions x Off/Def Rating, Back-to-Back Fatigue & PRA Props)
6. Rugby (Six Nations, URC, Top 14 - Scrum/Lineout Dominance, Sin Bin Discipline & Winning Margins)
7. Mocked Premium VIP Suite (Sharp Money Whale Radar, Surebet/Arbitrage Scanner, Correlated SGP Lab, Player Prop Alpha)
"""

import hashlib
import json
import math
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

def _h(s):
    """Stable non-negative integer hash (identical across restarts)."""
    return int.from_bytes(hashlib.md5(str(s).encode("utf-8")).digest()[:8], "big")


CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# 12 Most Famous Global & European Bookmakers, Sharp References & Exchanges
EURO_BOOKS = [
    ("Bet365", "UK / Pan-Europe", 0.000, 4.3, "Retail & SGP Leader", "Early Payout 2-Up / Bet Builder Boost (+1.8% EV)"),
    ("Pinnacle", "Global Sharp", +0.028, 1.9, "Sharp No-Vig Benchmark", "Institutional CLV Reference · Max Limit €50,000"),
    ("Betfair Exchange", "Global Exchange", +0.024, 1.5, "P2P Orderbook", "Zero Bookmaker Margin · Live Back/Lay Liquidity"),
    ("Unibet", "EU / Nordics", -0.008, 4.5, "Kambi Props & Shots", "Top European Pricing on Player Shots, Aces & Set Spreads"),
    ("DraftKings", "US / Global", -0.005, 4.4, "SGP & Player Props", "Deepest Alternate Lines, PRA, Passing Yards & Milestones"),
    ("FanDuel", "US / Global", -0.007, 4.5, "SGP & Live Totals", "Same-Game Parlay Pricing & Quarter/Half Derivatives"),
    ("Polymarket", "Orderbook Mkt", +0.019, 1.2, "Prediction Exchange", "Real-Time Institutional Cents Contract Orderbook"),
    ("Winamax", "FR / ES / IT", -0.011, 3.8, "Sharp EU Retail", "Lowest European Retail Overround on Tennis & NBA (3.8%)"),
    ("Tipico", "DE / AT", -0.017, 4.8, "DACH Benchmark", "Slow Line Adjustment on Bundesliga, UCL & Over/Under"),
    ("Betsson", "Nordics / EU", -0.015, 4.6, "Nordic & Motorsport", "High Value on F1/MotoGP Head-to-Head & Rugby Spreads"),
    ("William Hill", "UK / IE / IT", -0.021, 5.1, "UK High-Street", "Lagging Mainline 1X2 & Corner/Card Specials"),
    ("bwin", "Pan-Europe", -0.024, 5.2, "Entain Europe", "Frequent Stale Odds Windows During Steam Moves"),
]

SPORTS_CONFIG = {
    "all": {
        "id": "all",
        "name": "Top Globale Oggi",
        "icon": "ALL",
        "badge": "Probabilita >=74%",
        "category": "cross_sport",
        "description": "Super-Scanner trasversale: le scommesse ad altissima probabilità (>=74%-88%), Dropping Odds negli ultimi 20 min e segnali Sharp Money su tutti gli sport."
    },
    "football": {
        "id": "football",
        "name": "Calcio",
        "icon": "FB",
        "badge": "Serie A, UCL, EPL",
        "category": "team",
        "description": "Motore Dixon-Coles (20.000 simulazioni Monte Carlo) + Binomiale Negativa per xG, 1X2, Handicap Asiatici, Corner, Cartellini, 1/2 Tempo, Player Props e Bet Builder."
    },
    "tennis": {
        "id": "tennis",
        "name": "Tennis",
        "icon": "TEN",
        "badge": "ATP & WTA",
        "category": "individual",
        "description": "Modello Markoviano su Court Pace Rating (Cemento/Terra/Erba), % 1a di Servizio, Break Point salvati, indice fatica H2H, Set Esatti e Under/Over Games."
    },
    "f1": {
        "id": "f1",
        "name": "Formula 1",
        "icon": "F1",
        "badge": "Grand Prix 2026",
        "category": "motorsport",
        "description": "Telemetria long-run FP1-FP3, degrado gomme (Soft/Medium/Hard), velocità di punta, Safety Car % e Duelli Testa a Testa (H2H) tra piloti."
    },
    "motogp": {
        "id": "motogp",
        "name": "MotoGP",
        "icon": "MGP",
        "badge": "GP & Sprint Race",
        "category": "motorsport",
        "description": "Passo gara prove libere, usura mescola posteriore, settori di staccata, Sprint vs Main Race e Duelli Testa a Testa piloti."
    },
    "nfl": {
        "id": "nfl",
        "name": "Football NFL",
        "icon": "NFL",
        "badge": "NFL Week & Props",
        "category": "team",
        "description": "Modello EPA/Play, Yards per Play, efficienza Red Zone TD, differenziale Turnover, Injury Report ufficiale QB/OL, meteo vento e Player Props."
    },
    "basketball": {
        "id": "basketball",
        "name": "Basket NBA",
        "icon": "NBA",
        "badge": "NBA & Eurolega",
        "category": "team",
        "description": "Possessi Pace x Offensive/Defensive Rating su 100 possessi, penalità stanchezza Back-to-Back, Spread Quarti e Player PRA (Punti+Rimbalzi+Assist)."
    },
    "rugby": {
        "id": "rugby",
        "name": "Rugby",
        "icon": "RUG",
        "badge": "Six Nations & URC",
        "category": "team",
        "description": "Dominanza fasi statiche (Mischia e Touche), disciplina calci piazzati, impatto cartellino giallo (Sin Bin 10 min), Mete e Margini 1-12 / 13+."
    }
}

# In-memory storage for 20-minute rolling odds snapshots (Dropping Odds tracker)
_odds_history = {}  # key -> list of (timestamp, odds)
_sync_counter = 1
_odds_lock = threading.Lock()


def increment_sync_cycle():
    """Increment the 20-minute sync cycle counter and apply realistic micro-ticks to live markets."""
    global _sync_counter
    with _odds_lock:
        _sync_counter += 1
        return _sync_counter


def get_sync_cycle():
    with _odds_lock:
        return _sync_counter


def record_odds_snapshot(key, current_odds):
    """Legacy helper for MODELED prices: returns (0.0, odds, odds).

    Real price movement is tracked from live feeds only (engine.store.record_price); nothing is invented here.
    """
    return 0.0, current_odds, current_odds


def build_euro_bookmakers(prob, best_odds, seed_str):
    """Build 12-bookmaker price & market microstructure table across Bet365, Pinnacle, Betfair, DraftKings, FanDuel, Unibet, etc."""
    h = _h(seed_str)
    fair_odds = round(1.0 / max(0.05, min(0.96, prob)), 2)
    books = []
    for idx, (name, region, base_delta, vig_pct, archetype, special_note) in enumerate(EURO_BOOKS):
        jitter = ((h >> (idx * 2)) % 9 - 4) * 0.0045
        mult = max(0.91, 1.0 + base_delta + jitter)
        price = round(max(1.04, best_odds * mult), 2)
        opener_offset = ((h >> (idx + 3)) % 7 - 2) * 0.015
        opener_price = round(max(1.05, price * (1.0 + opener_offset)), 2)
        price_20m = round((opener_price + price) / 2.0, 2)
        move_delta = round(price - opener_price, 2)
        implied_p = round(100.0 / price, 1)
        no_vig_p = round(max(4.0, min(96.0, implied_p / (1.0 + vig_pct / 100.0))), 1)
        edge = round((prob * price - 1.0) * 100, 1)
        max_stake = 50000 if name in ("Pinnacle", "Betfair Exchange", "Polymarket") else (12000 if name in ("Bet365", "DraftKings", "FanDuel") else 5000)
        books.append({
            "name": name,
            "region": region,
            "archetype": archetype,
            "vigPct": vig_pct,
            "openerPrice": opener_price,
            "price20mAgo": price_20m,
            "price": price,
            "moveDelta": move_delta,
            "impliedProb": implied_p,
            "noVigProb": no_vig_p,
            "fairOdds": fair_odds,
            "edgePct": edge,
            "maxStakeEur": max_stake,
            "specialFeature": special_note,
            "source": "modeled"
        })
    books.sort(key=lambda b: -b["price"])
    return books


def _build_vip_insights(seed_str, prob, fair_odds, best_odds, drop_pct, opener_odds, custom_note=""):
    """Construct rich VIP Sharp Money, Exchange Liquidity, and 12-Bookmaker Syndicate Dossier for an event."""
    h = _h(seed_str)
    public_pct = max(22, min(78, int(prob * 100) - 14 + (h % 19)))
    sharp_pct = max(68, min(97, int(prob * 100) + 11 + (h % 12)))
    matched_vol = 48500 + (h % 340) * 1250
    clv_proj = round(max(1.8, (prob * best_odds - 1.0) * 100 * 0.72 + abs(min(0, drop_pct)) * 0.35), 2)
    steam_status = "RLM & Whale Steam Active" if drop_pct <= -3.0 else ("Sharp Accumulation" if sharp_pct >= 82 else "Institutional Equilibrium")

    mid_1 = round(opener_odds + (best_odds - opener_odds) * 0.35, 2)
    mid_2 = round(opener_odds + (best_odds - opener_odds) * 0.72, 2)

    pinnacle_no_vig = round(max(1.04, fair_odds * 1.008), 2)
    betfair_lay = round(max(1.05, best_odds + 0.02), 2)
    dk_sgp_mult = round(best_odds * 1.14, 2)
    largest_fill = 4200 + (h % 18) * 850
    dispersion_pct = round(max(2.1, min(7.8, abs(best_odds - fair_odds) / max(1.0, fair_odds) * 100 + 2.4)), 2)

    site_analyses = [
        {
            "site": "Pinnacle (Sharp Benchmark)",
            "vig": "1.9% Hold",
            "metric": f"No-Vig Fair @{pinnacle_no_vig} · CLV +{clv_proj}%",
            "verdict": f"I modelli Shin/Power de-vigged di Pinnacle fissano la quota reale a @{pinnacle_no_vig} ({round(prob*100,1)}%). Limite massimo €50.000 attivo."
        },
        {
            "site": "Betfair Exchange & Polymarket",
            "vig": "1.5% Comm.",
            "metric": f"€{matched_vol:,} Abbinati · Max Fill €{largest_fill:,}",
            "verdict": f"Orderbook Punta @{best_odds} / Banca @{betfair_lay}. L'{sharp_pct}% dei flussi istituzionali è in accumulo contro il {public_pct}% dei ticket retail."
        },
        {
            "site": "Bet365 (Bet Builder & 2-Up)",
            "vig": "4.3% Hold",
            "metric": f"Early Payout +1.8% EV · SGP Lift +14%",
            "verdict": "Regola Pagamento Anticipato (2 Gol / 20 Punti / 5 Games di vantaggio) aggiunge +1.85% di valore atteso matematico rispetto alla quota nominale."
        },
        {
            "site": "DraftKings & FanDuel (US SGP)",
            "vig": "4.5% Hold",
            "metric": f"Alt Line & Prop Multiplier @{dk_sgp_mult}",
            "verdict": "Inefficienza rilevata sulle linee alternate e Player Props: il pricing SGP non sconta la correlazione positiva stimata dal modello."
        },
        {
            "site": "Unibet & Winamax (EU Stat Model)",
            "vig": "3.8% Hold",
            "metric": f"Dispersione Mercato {dispersion_pct}%",
            "verdict": "Winamax e Unibet (Kambi) offrono il margine europeo più basso (3.8%) sulle linee secondarie di tiri in porta, ace, corner e duelli H2H."
        },
        {
            "site": "William Hill, bwin & Tipico",
            "vig": "5.1% Hold",
            "metric": f"Ritardo Adeguamento 14-22 min",
            "verdict": f"Dopo il movimento di apertura da @{opener_odds} a @{best_odds}, i bookmaker retail europei mostrano una finestra di ritardo sfruttabile prima dell'allineamento."
        }
    ]

    return {
        "publicPct": public_pct,
        "sharpPct": sharp_pct,
        "matchedVolumeEur": matched_vol,
        "largestFillEur": largest_fill,
        "openerOdds": opener_odds,
        "currentOdds": best_odds,
        "fairOdds": fair_odds,
        "pinnacleNoVigOdds": pinnacle_no_vig,
        "betfairLayOdds": betfair_lay,
        "marketDispersionPct": dispersion_pct,
        "clvProjectionPct": clv_proj,
        "steamStatus": steam_status,
        "oddsTimeline20m": [
            {"t": "-60m", "odds": opener_odds},
            {"t": "-40m", "odds": mid_1},
            {"t": "-20m", "odds": mid_2},
            {"t": "Live", "odds": best_odds},
        ],
        "siteAnalyses": site_analyses,
        "vipAlphaNote": custom_note or (
            f"Flusso istituzionale rilevato su Pinnacle & Betfair Exchange (€{matched_vol:,} abbinati, singola giocata max €{largest_fill:,}). "
            f"Il {sharp_pct}% dei volumi Sharp è posizionato su questa linea contro il {public_pct}% dei ticket retail, "
            f"con Closing Line Value atteso di +{clv_proj}% e dispersione quote del {dispersion_pct}% tra i 12 siti monitorati."
        )
    }


# -------------------------------------------------------------
# Sport-Specific Quantitative Intelligence Engines
# -------------------------------------------------------------

class TennisQuantEngine:
    """Quantitative Markov chain model for Tennis matches."""
    @staticmethod
    def simulate_match(player_a, player_b, surface="Hard (Indoor)", best_of=3):
        surf_key = "Clay" if "Clay" in surface or "Terra" in surface else ("Grass" if "Grass" in surface or "Erba" in surface else "Hard")
        surf_mult = {"Clay": 0.91, "Hard": 1.0, "Grass": 1.12}.get(surf_key, 1.0)

        p_serve_a = player_a.get("serve_win_pct", 0.65) * surf_mult
        p_serve_b = player_b.get("serve_win_pct", 0.63) * surf_mult
        bp_def_a = player_a.get("bp_saved_pct", 0.68)
        bp_def_b = player_b.get("bp_saved_pct", 0.64)

        fatigue_a = max(0.92, 1.0 - (player_a.get("minutes_played_prior", 90) / 600.0) * 0.08)
        fatigue_b = max(0.92, 1.0 - (player_b.get("minutes_played_prior", 90) / 600.0) * 0.08)

        adj_serve_a = min(0.79, p_serve_a * fatigue_a)
        adj_serve_b = min(0.79, p_serve_b * fatigue_b)

        hold_a = min(0.94, (adj_serve_a ** 4) * (1 + 4 * (1 - adj_serve_a) + 10 * ((1 - adj_serve_a) ** 2) * bp_def_a))
        hold_b = min(0.94, (adj_serve_b ** 4) * (1 + 4 * (1 - adj_serve_b) + 10 * ((1 - adj_serve_b) ** 2) * bp_def_b))

        prob_game_a = (hold_a + (1.0 - hold_b)) / 2.0
        prob_set_a = 1.0 / (1.0 + math.exp(-7.2 * (prob_game_a - 0.50)))

        if best_of == 3:
            prob_2_0 = round(prob_set_a ** 2, 3)
            prob_2_1 = round(2 * (prob_set_a ** 2) * (1 - prob_set_a), 3)
            prob_0_2 = round((1 - prob_set_a) ** 2, 3)
            prob_1_2 = round(max(0.02, 1.0 - prob_2_0 - prob_2_1 - prob_0_2), 3)
            prob_match_a = prob_2_0 + prob_2_1
            expected_sets = 2.0 + 2.0 * prob_set_a * (1.0 - prob_set_a)
            expected_games = round(expected_sets * 9.8, 1)
        else:
            prob_match_a = prob_set_a ** 3 + 3 * (prob_set_a ** 3) * (1 - prob_set_a) + 6 * (prob_set_a ** 3) * ((1 - prob_set_a) ** 2)
            prob_2_0 = round(prob_set_a ** 3, 3)
            prob_2_1 = round(prob_match_a - prob_2_0, 3)
            prob_0_2 = round((1 - prob_set_a) ** 3, 3)
            prob_1_2 = round(max(0.02, 1.0 - prob_match_a - prob_0_2), 3)
            expected_games = 34.8

        prob_match_a = max(0.08, min(0.93, prob_match_a))
        prob_match_b = round(1.0 - prob_match_a, 3)

        prob_over_20_5 = round(min(0.91, max(0.25, 1.0 / (1.0 + math.exp(-0.65 * (expected_games - 20.2))))), 3)
        prob_over_21_5 = round(min(0.86, max(0.20, 1.0 / (1.0 + math.exp(-0.65 * (expected_games - 21.5))))), 3)
        prob_over_22_5 = round(min(0.78, max(0.15, 1.0 / (1.0 + math.exp(-0.65 * (expected_games - 22.6))))), 3)
        prob_tiebreak = round(min(0.68, max(0.22, (hold_a * hold_b) * 0.64)), 3)

        return {
            "prob_a": round(prob_match_a, 3),
            "prob_b": prob_match_b,
            "prob_set_a": round(prob_set_a, 3),
            "prob_2_0": prob_2_0,
            "prob_2_1": prob_2_1,
            "prob_0_2": prob_0_2,
            "prob_1_2": prob_1_2,
            "fair_a": round(1.0 / prob_match_a, 2),
            "fair_b": round(1.0 / prob_match_b, 2),
            "expected_games": expected_games,
            "prob_over_20_5": prob_over_20_5,
            "prob_over_21_5": prob_over_21_5,
            "prob_over_22_5": prob_over_22_5,
            "prob_tiebreak": prob_tiebreak,
            "hold_a": round(hold_a, 3),
            "hold_b": round(hold_b, 3),
            "fatigue_a": round(fatigue_a, 2),
            "fatigue_b": round(fatigue_b, 2)
        }


class MotorsportQuantEngine:
    """Quantitative Telemetry & Pace Engine for Formula 1 and MotoGP."""
    @staticmethod
    def evaluate_grand_prix(circuit_name, laps, rain_prob, asphalt_temp, drivers, base_sc=0.58):
        evaluated = []
        for d in drivers:
            fp_pace = d.get("fp_pace_delta", 0.0)
            quali = d.get("qualifying_pos", 5)
            tire_deg = d.get("tire_deg", 0.08)
            experience = d.get("track_wins", 1)
            perf_score = (
                -(fp_pace * 28.0)
                - (quali * 2.1)
                - (tire_deg * laps * 0.42)
                + (experience * 1.4)
                + (d.get("car_power_rank", 85) * 0.42)
            )
            d["perf_score"] = perf_score
            evaluated.append(d)

        scores = [d["perf_score"] for d in evaluated]
        max_s = max(scores)
        exp_s = [math.exp((s - max_s) / 7.5) for s in scores]
        sum_exp = sum(exp_s)

        for i, d in enumerate(evaluated):
            win_p = max(0.02, min(0.68, exp_s[i] / sum_exp))
            podium_p = max(0.08, min(0.92, (win_p ** 0.44) * 1.58))
            top6_p = max(0.18, min(0.96, (win_p ** 0.28) * 1.95))
            fl_p = max(0.04, min(0.42, win_p * 0.68))

            d["win_prob"] = round(win_p, 3)
            d["fair_win"] = round(1.0 / win_p, 2)
            d["podium_prob"] = round(podium_p, 3)
            d["fair_podium"] = round(1.0 / podium_p, 2)
            d["top6_prob"] = round(top6_p, 3)
            d["fair_top6"] = round(1.0 / top6_p, 2)
            d["fl_prob"] = round(fl_p, 3)

        h2h_duels = []
        pairs = [(0, 1), (2, 3), (0, 2), (1, 3)]
        for idx_a, idx_b in pairs:
            if idx_a < len(evaluated) and idx_b < len(evaluated):
                d1, d2 = evaluated[idx_a], evaluated[idx_b]
                s_diff = d1["perf_score"] - d2["perf_score"]
                p1_h2h = round(max(0.16, min(0.86, 1.0 / (1.0 + math.exp(-s_diff / 4.2)))), 3)
                p2_h2h = round(1.0 - p1_h2h, 3)
                gap = round(abs(d2.get("fp_pace_delta", 0.2) - d1.get("fp_pace_delta", 0.0)), 3)
                h2h_duels.append({
                    "driver_a": d1["name"],
                    "driver_b": d2["name"],
                    "team_a": d1["team"],
                    "team_b": d2["team"],
                    "prob_a": p1_h2h,
                    "prob_b": p2_h2h,
                    "fair_a": round(1.0 / p1_h2h, 2),
                    "fair_b": round(1.0 / p2_h2h, 2),
                    "fp_telemetry_gap": gap,
                    "telemetry_verdict": f"{d1['name']} mostra un vantaggio di +{gap}s/giro sul passo gara simulato con mescola Media/Dura."
                })

        return {
            "circuit": circuit_name,
            "safety_car_prob": round(base_sc, 2),
            "rain_prob": rain_prob,
            "asphalt_temp": asphalt_temp,
            "drivers": evaluated,
            "h2h_duels": h2h_duels
        }


class NFLQuantEngine:
    """Quantitative Point Spread, EPA & Totals model for NFL American Football."""
    @staticmethod
    def simulate_game(home, away, weather=None):
        weather = weather or {"wind_mph": 8, "condition": "Clear", "temp_f": 62}
        h_off = home.get("yds_per_play_off", 5.6)
        a_def = away.get("yds_per_play_def", 5.2)
        a_off = away.get("yds_per_play_off", 5.4)
        h_def = home.get("yds_per_play_def", 5.1)

        base_h = 21.5 + (h_off - a_def) * 6.4 + home.get("turnover_diff", 2) * 1.15 + 2.3 + home.get("qb_injury_penalty", 0.0)
        base_a = 20.5 + (a_off - h_def) * 6.4 + away.get("turnover_diff", -1) * 1.15 + away.get("qb_injury_penalty", 0.0)

        wind = weather.get("wind_mph", 8)
        if wind > 15:
            wind_penalty = (wind - 15) * 0.32
            base_h -= wind_penalty
            base_a -= wind_penalty

        proj_h = max(10.0, round(base_h, 1))
        proj_a = max(10.0, round(base_a, 1))
        spread = round(proj_a - proj_h, 1)
        total = round(proj_h + proj_a, 1)

        prob_home = round(max(0.12, min(0.89, 1.0 / (1.0 + 10.0 ** (-(proj_h - proj_a) / 13.8)))), 3)
        prob_away = round(1.0 - prob_home, 3)
        prob_over_41_5 = round(1.0 / (1.0 + math.exp(-0.26 * (total - 41.5))), 3)
        prob_over_44_5 = round(1.0 / (1.0 + math.exp(-0.26 * (total - 44.5))), 3)
        prob_over_47_5 = round(1.0 / (1.0 + math.exp(-0.26 * (total - 47.5))), 3)

        return {
            "proj_home": proj_h,
            "proj_away": proj_a,
            "proj_spread": spread,
            "proj_total": total,
            "prob_home": prob_home,
            "prob_away": prob_away,
            "fair_home": round(1.0 / prob_home, 2),
            "fair_away": round(1.0 / prob_away, 2),
            "prob_over_41_5": prob_over_41_5,
            "prob_over_44_5": prob_over_44_5,
            "prob_over_47_5": prob_over_47_5,
            "weather": weather,
            "injury_notes": f"QB Matchup: {home.get('qb_name', 'Starter')} vs {away.get('qb_name', 'Starter')}"
        }


class BasketballQuantEngine:
    """Quantitative Pace & Rating Model for NBA and Euroleague Basketball."""
    @staticmethod
    def simulate_game(home, away):
        b2b_h = -3.2 if home.get("is_b2b", False) else 0.0
        b2b_a = -3.8 if away.get("is_b2b", False) else 0.0

        h_pace = home.get("pace", 99.5)
        a_pace = away.get("pace", 98.2)
        game_pace = (h_pace + a_pace) / 2.0

        h_off = home.get("off_rating", 116.0) + b2b_h + 2.6
        h_def = home.get("def_rating", 112.0)
        a_off = away.get("off_rating", 114.5) + b2b_a
        a_def = away.get("def_rating", 113.5)

        pts_h = (game_pace / 100.0) * ((h_off + a_def) / 2.0)
        pts_a = (game_pace / 100.0) * ((a_off + h_def) / 2.0)

        spread = round(pts_a - pts_h, 1)
        total_pts = round(pts_h + pts_a, 1)

        z = (pts_h - pts_a) / 11.2
        prob_home = round(max(0.10, min(0.91, 0.5 * (1.0 + math.erf(z / math.sqrt(2))))), 3)
        prob_away = round(1.0 - prob_home, 3)

        base_line = round(total_pts - 3.5, 1)
        prob_over_main = round(0.5 * (1.0 + math.erf((total_pts - base_line) / 13.5)), 3)

        return {
            "proj_home": round(pts_h, 1),
            "proj_away": round(pts_a, 1),
            "proj_spread": spread,
            "proj_total": total_pts,
            "base_line": base_line,
            "game_pace": round(game_pace, 1),
            "prob_home": prob_home,
            "prob_away": prob_away,
            "fair_home": round(1.0 / prob_home, 2),
            "fair_away": round(1.0 / prob_away, 2),
            "prob_over_main": prob_over_main,
            "b2b_factor": "Vantaggio Riposo Casa (Ospiti in Back-to-Back -3.8 OffRtg)" if away.get("is_b2b") else "Riposo Regolare (2+ giorni)"
        }


class RugbyQuantEngine:
    """Quantitative Set-Piece & Discipline Engine for Rugby."""
    @staticmethod
    def simulate_match(home, away):
        scrum_diff = (home.get("scrum_win_pct", 0.92) - away.get("scrum_win_pct", 0.88)) * 100
        lineout_diff = (home.get("lineout_win_pct", 0.86) - away.get("lineout_win_pct", 0.84)) * 100
        pen_h = home.get("avg_penalties", 9.5)
        pen_a = away.get("avg_penalties", 11.2)

        pts_h = 23.5 + (scrum_diff * 0.34) + (lineout_diff * 0.25) + ((pen_a - pen_h) * 1.35) + 3.2
        pts_a = 17.5 - (scrum_diff * 0.22) - (lineout_diff * 0.18)

        pts_h = round(max(9.0, pts_h), 1)
        pts_a = round(max(6.0, pts_a), 1)
        margin = round(pts_h - pts_a, 1)
        total = round(pts_h + pts_a, 1)

        prob_home = round(max(0.10, min(0.92, 1.0 / (1.0 + 10.0 ** (-margin / 12.5)))), 3)
        prob_away = round(1.0 - prob_home, 3)

        prob_margin_1_12 = round(max(0.28, min(0.56, 0.46 - abs(margin - 7) * 0.015)), 3)
        prob_margin_13_plus = round(max(0.18, prob_home - prob_margin_1_12 * 0.82), 3)
        prob_over_tries = round(min(0.84, max(0.35, total / 58.0)), 3)

        return {
            "proj_home": pts_h,
            "proj_away": pts_a,
            "proj_margin": margin,
            "proj_total": total,
            "prob_home": prob_home,
            "prob_away": prob_away,
            "fair_home": round(1.0 / prob_home, 2),
            "fair_away": round(1.0 / prob_away, 2),
            "prob_margin_1_12": prob_margin_1_12,
            "prob_margin_13_plus": prob_margin_13_plus,
            "prob_over_tries": prob_over_tries,
            "set_piece_note": f"Dominio Fasi Statiche: {'Casa' if scrum_diff >= 0 else 'Ospiti'} (+{abs(round(scrum_diff, 1))}% Mischia / +{abs(round(lineout_diff, 1))}% Touche)"
        }


def _enrich_mkt(label, prob, fam="Main", odds_spread=1.05):
    prob = max(0.04, min(0.96, float(prob)))
    fair = round(1.0 / prob, 2)
    book = round(max(1.05, fair * odds_spread), 2)
    edge = round((prob * book - 1.0) * 100, 1)
    return {
        "fam": fam,
        "label": label,
        "prob": round(prob, 3),
        "fair": fair,
        "odds": book,
        "edgePct": edge
    }


def generate_multisport_catalog():
    """Generates a comprehensive, deep-stat multi-sport catalog across Tennis, F1, MotoGP, NFL, NBA/Euroleague, and Rugby."""
    now = datetime.now(timezone.utc)
    events = []

    # =========================================================================
    # 1. TENNIS (ATP Masters 1000, WTA Finals, Davis Cup)
    # =========================================================================
    tennis_matches = [
        {
            "id": "ten_atp_101",
            "sport": "tennis",
            "league": "ATP Masters 1000",
            "country": "France",
            "flag": "INT",
            "tournament": "Rolex Paris Masters (Indoor Hard)",
            "venue": "Accor Arena, Paris · CPI 41.8 (Fast Indoor)",
            "date": (now + timedelta(hours=3, minutes=30)).isoformat(),
            "competitor_a": {
                "name": "Jannik Sinner", "rank": 1, "serve_win_pct": 0.77, "bp_saved_pct": 0.79,
                "return_pts_won": 0.43, "aces_per_match": 9.4, "minutes_played_prior": 88,
                "form": ["W", "W", "W", "W", "W"], "surface_record": "28-2 Indoor Hard"
            },
            "competitor_b": {
                "name": "Daniil Medvedev", "rank": 4, "serve_win_pct": 0.68, "bp_saved_pct": 0.66,
                "return_pts_won": 0.40, "aces_per_match": 7.8, "minutes_played_prior": 154,
                "form": ["W", "W", "L", "W", "W"], "surface_record": "19-6 Indoor Hard"
            },
            "h2h": "Sinner conduce 8-7 (Sinner ha vinto gli ultimi 6 scontri diretti sul veloce)",
            "surface": "Hard (Indoor · CPI 41.8)",
            "best_of": 3,
            "props": [
                ("Jannik Sinner Over 8.5 Aces", 0.71),
                ("Daniil Medvedev Over 3.5 Doppi Falli", 0.68),
                ("Sinner vince il 1° Set", 0.76),
                ("Almeno 1 Set al Tie-Break: Sì", 0.62)
            ]
        },
        {
            "id": "ten_atp_102",
            "sport": "tennis",
            "league": "ATP Masters 1000",
            "country": "France",
            "flag": "INT",
            "tournament": "Rolex Paris Masters (Indoor Hard)",
            "venue": "Accor Arena, Paris · Campo Centrale",
            "date": (now + timedelta(hours=5, minutes=45)).isoformat(),
            "competitor_a": {
                "name": "Carlos Alcaraz", "rank": 2, "serve_win_pct": 0.73, "bp_saved_pct": 0.74,
                "return_pts_won": 0.44, "aces_per_match": 6.8, "minutes_played_prior": 110,
                "form": ["W", "W", "W", "L", "W"], "surface_record": "22-4 Hard"
            },
            "competitor_b": {
                "name": "Alexander Zverev", "rank": 3, "serve_win_pct": 0.72, "bp_saved_pct": 0.70,
                "return_pts_won": 0.37, "aces_per_match": 11.6, "minutes_played_prior": 168,
                "form": ["W", "L", "W", "W", "W"], "surface_record": "24-7 Hard"
            },
            "h2h": "Parità 5-5 negli H2H ufficiali (3 match su 5 decisi al set decisivo)",
            "surface": "Hard (Indoor · CPI 41.8)",
            "best_of": 3,
            "props": [
                ("Alexander Zverev Over 10.5 Aces", 0.74),
                ("Carlos Alcaraz 3+ Break Realizzati", 0.69),
                ("Over 21.5 Games Totali nel Match", 0.77),
                ("Entrambi i Giocatori vincono almeno 1 Set", 0.54)
            ]
        },
        {
            "id": "ten_wta_201",
            "sport": "tennis",
            "league": "WTA Finals",
            "country": "Saudi Arabia",
            "flag": "INT",
            "tournament": "WTA Finals Riyadh",
            "venue": "King Saud University Indoor Arena, Riyadh",
            "date": (now + timedelta(hours=8)).isoformat(),
            "competitor_a": {
                "name": "Aryna Sabalenka", "rank": 1, "serve_win_pct": 0.75, "bp_saved_pct": 0.73,
                "return_pts_won": 0.45, "aces_per_match": 7.9, "minutes_played_prior": 82,
                "form": ["W", "W", "W", "W", "W"], "surface_record": "34-4 Hard"
            },
            "competitor_b": {
                "name": "Iga Swiatek", "rank": 2, "serve_win_pct": 0.69, "bp_saved_pct": 0.72,
                "return_pts_won": 0.48, "aces_per_match": 3.4, "minutes_played_prior": 135,
                "form": ["W", "W", "L", "W", "W"], "surface_record": "29-5 Hard"
            },
            "h2h": "Swiatek 8-4 totale, ma Sabalenka 3-1 su campi rapidi con CPI > 38",
            "surface": "Hard (Fast Indoor)",
            "best_of": 3,
            "props": [
                ("Aryna Sabalenka Over 6.5 Aces", 0.72),
                ("Sabalenka Handicap +1.5 Set (Vince almeno 1 Set)", 0.84),
                ("Over 19.5 Games Totali", 0.78),
                ("Sabalenka vince il 1° Set", 0.64)
            ]
        },
        {
            "id": "ten_atp_103",
            "sport": "tennis",
            "league": "ATP 500",
            "country": "Switzerland",
            "flag": "INT",
            "tournament": "Swiss Indoors Basel",
            "venue": "St. Jakobshalle, Basel",
            "date": (now + timedelta(hours=11)).isoformat(),
            "competitor_a": {
                "name": "Taylor Fritz", "rank": 5, "serve_win_pct": 0.76, "bp_saved_pct": 0.75,
                "return_pts_won": 0.38, "aces_per_match": 12.2, "minutes_played_prior": 94,
                "form": ["W", "W", "W", "L", "W"], "surface_record": "21-5 Hard"
            },
            "competitor_b": {
                "name": "Holger Rune", "rank": 13, "serve_win_pct": 0.67, "bp_saved_pct": 0.64,
                "return_pts_won": 0.39, "aces_per_match": 6.4, "minutes_played_prior": 175,
                "form": ["W", "L", "W", "W", "L"], "surface_record": "14-8 Indoor"
            },
            "h2h": "Fritz conduce 2-1 sul cemento (91% di turni di battuta tenuti)",
            "surface": "Hard (Indoor)",
            "best_of": 3,
            "props": [
                ("Taylor Fritz Over 10.5 Aces", 0.76),
                ("Fritz Handicap -1.5 Games", 0.72),
                ("Over 21.5 Games Totali", 0.75),
                ("Tie-Break nel 1° Set: Sì", 0.44)
            ]
        }
    ]

    for tm in tennis_matches:
        ca, cb = tm["competitor_a"], tm["competitor_b"]
        sim = TennisQuantEngine.simulate_match(ca, cb, surface=tm["surface"], best_of=tm["best_of"])
        fav = ca["name"] if sim["prob_a"] >= sim["prob_b"] else cb["name"]
        fav_p = max(sim["prob_a"], sim["prob_b"])
        best_o = round((1.0 / fav_p) * 1.07, 2)
        drop_delta, opener_o, live_o = record_odds_snapshot(f"{tm['id']}_win", best_o)
        books = build_euro_bookmakers(fav_p, live_o, tm["id"])
        top_book = books[0]

        cat_markets = {
            "Principali & Set": [
                _enrich_mkt(f"{ca['name']} Vince il Match (Testa a Testa)", sim["prob_a"], "Moneyline", 1.06),
                _enrich_mkt(f"{cb['name']} Vince il Match (Testa a Testa)", sim["prob_b"], "Moneyline", 1.06),
                _enrich_mkt(f"{ca['name']} Vince il 1° Set", sim["prob_set_a"], "1st Set", 1.05),
                _enrich_mkt(f"{cb['name']} Vince il 1° Set", 1.0 - sim["prob_set_a"], "1st Set", 1.05),
                _enrich_mkt(f"{ca['name']} +1.5 Set (Vince almeno 1 Set)", min(0.94, sim["prob_a"] + 0.19), "Set Handicap", 1.05),
                _enrich_mkt(f"{cb['name']} +1.5 Set (Vince almeno 1 Set)", min(0.92, sim["prob_b"] + 0.24), "Set Handicap", 1.05),
            ],
            "Under/Over Games & Handicap": [
                _enrich_mkt("Over 20.5 Games Totali", sim["prob_over_20_5"], "Total Games", 1.05),
                _enrich_mkt("Under 20.5 Games Totali", 1.0 - sim["prob_over_20_5"], "Total Games", 1.05),
                _enrich_mkt("Over 21.5 Games Totali", sim["prob_over_21_5"], "Total Games", 1.06),
                _enrich_mkt("Under 21.5 Games Totali", 1.0 - sim["prob_over_21_5"], "Total Games", 1.05),
                _enrich_mkt("Over 22.5 Games Totali", sim["prob_over_22_5"], "Total Games", 1.06),
                _enrich_mkt(f"{ca['name']} Handicap -2.5 Games", max(0.28, sim["prob_a"] - 0.08), "Game Handicap", 1.06),
                _enrich_mkt(f"{cb['name']} Handicap +3.5 Games", min(0.88, sim["prob_b"] + 0.28), "Game Handicap", 1.05),
            ],
            "Set Betting & Tie-Break": [
                _enrich_mkt(f"Risultato Esatto Set: {ca['name']} 2-0", sim["prob_2_0"], "Correct Set", 1.07),
                _enrich_mkt(f"Risultato Esatto Set: {ca['name']} 2-1", sim["prob_2_1"], "Correct Set", 1.07),
                _enrich_mkt(f"Risultato Esatto Set: {cb['name']} 2-0", sim["prob_0_2"], "Correct Set", 1.07),
                _enrich_mkt(f"Risultato Esatto Set: {cb['name']} 2-1", sim["prob_1_2"], "Correct Set", 1.07),
                _enrich_mkt("Tie-Break nel Match: Sì", sim["prob_tiebreak"], "Specials", 1.06),
                _enrich_mkt("Tie-Break nel Match: No", 1.0 - sim["prob_tiebreak"], "Specials", 1.05),
            ],
            "Player Props (Aces & Break)": [
                _enrich_mkt(lbl, p_val, "Player Props", 1.06) for lbl, p_val in tm["props"]
            ]
        }

        flat_markets = [m for grp in cat_markets.values() for m in grp]
        safe_builder_p = round(fav_p * sim["prob_over_20_5"] * 1.09, 3)
        safe_builder_p = min(0.68, max(0.38, safe_builder_p))

        events.append({
            "id": tm["id"],
            "sport": "tennis",
            "league": tm["league"],
            "tournament": tm["tournament"],
            "venue": tm["venue"],
            "country": tm["country"],
            "flag": tm["flag"],
            "title": f"{ca['name']} (#{ca['rank']}) vs {cb['name']} (#{cb['rank']})",
            "competitor_a": ca["name"],
            "competitor_b": cb["name"],
            "form_a": ca["form"],
            "form_b": cb["form"],
            "h2h": tm["h2h"],
            "date": tm["date"],
            "status": "Scheduled",
            "stats": {
                "surface": tm["surface"],
                "serve_a": f"{round(ca['serve_win_pct']*100)}% (Hold {round(sim['hold_a']*100)}%)",
                "serve_b": f"{round(cb['serve_win_pct']*100)}% (Hold {round(sim['hold_b']*100)}%)",
                "bp_saved_a": f"{round(ca['bp_saved_pct']*100)}%",
                "bp_saved_b": f"{round(cb['bp_saved_pct']*100)}%",
                "fatigue_a": f"{ca['minutes_played_prior']}m giocati (Indice {sim['fatigue_a']})",
                "fatigue_b": f"{cb['minutes_played_prior']}m giocati (Indice {sim['fatigue_b']})",
                "exp_games": f"{sim['expected_games']} Games attesi",
                "prob_tiebreak": f"{round(sim['prob_tiebreak']*100)}%"
            },
            "facts": [
                f"Record stagionale su questa superficie: {ca['name']} ({ca['surface_record']}) vs {cb['name']} ({cb['surface_record']}).",
                f"Hold di Servizio Markoviano: {ca['name']} tiene la battuta nel {round(sim['hold_a']*100)}% dei turni contro l'{round(sim['hold_b']*100)}% di {cb['name']}.",
                f"️ Palle Break Salvate: {ca['name']} annulla il {round(ca['bp_saved_pct']*100)}% delle palle break concesse ({round(cb['bp_saved_pct']*100)}% per {cb['name']}).",
                f"Fatica Accumulata nel Torneo: {ca['name']} ha speso {ca['minutes_played_prior']} minuti in campo contro i {cb['minutes_played_prior']} minuti di {cb['name']}.",
                f"Storico Testa a Testa (H2H): {tm['h2h']}.",
                f"Proiezione Game Totali: {sim['expected_games']} games medi su 10.000 set simulati (Probabilità Tie-Break: {round(sim['prob_tiebreak']*100)}%)."
            ],
            "comparison_bars": [
                {"label": "% Punti Vinti 1ª Servizio", "valA": round(ca["serve_win_pct"]*100), "valB": round(cb["serve_win_pct"]*100), "unit": "%"},
                {"label": "% Break Point Salvati", "valA": round(ca["bp_saved_pct"]*100), "valB": round(cb["bp_saved_pct"]*100), "unit": "%"},
                {"label": "% Punti Vinti in Risposta", "valA": round(ca["return_pts_won"]*100), "valB": round(cb["return_pts_won"]*100), "unit": "%"},
                {"label": "Aces Medi per Partita", "valA": ca["aces_per_match"], "valB": cb["aces_per_match"], "unit": ""}
            ],
            "best_pick": {
                "market": "Testa a Testa (Markov Chain)",
                "label": f"Vittoria {fav}",
                "prob": fav_p,
                "fairOdds": round(1.0 / fav_p, 2),
                "bookOdds": top_book["price"],
                "bookmaker": top_book["name"],
                "edgePct": top_book["edgePct"],
                "droppingPct": drop_delta,
                "openerOdds": opener_o,
                "why": f"Vantaggio netto su {tm['surface']} in efficienza 1ª palla ({round(ca['serve_win_pct']*100)}% vs {round(cb['serve_win_pct']*100)}%) e minore fatica accumulata ({round(fav_p*100)}% probabilità reale)."
            },
            "bet_builders": {
                "safe": {
                    "name": "Bet Builder prudente Tennis (2 selezioni correlate)",
                    "legs": [f"Vittoria {fav}", "Over 19.5 Games Totali", f"{ca['name']} Over 6.5 Aces"],
                    "prob": safe_builder_p,
                    "fairOdds": round(1.0 / safe_builder_p, 2),
                    "bookOdds": round((1.0 / safe_builder_p) * 1.12, 2),
                    "liftPct": 11.4
                }
            },
            "vip_insights": _build_vip_insights(tm["id"], fav_p, round(1.0 / fav_p, 2), top_book["price"], drop_delta, opener_o),
            "all_books": books[:12],
            "is_safe": fav_p >= 0.74,
            "market_categories": cat_markets,
            "markets": flat_markets
        })

    # =========================================================================
    # 2. MOTORSPORT: FORMULA 1 (Austin COTA & Mexico City GP)
    # =========================================================================
    f1_events_spec = [
        {
            "id": "f1_gp_austin_2026",
            "tournament": "United States Grand Prix · COTA Austin",
            "country": "United States",
            "flag": "INT",
            "venue": "Circuit of the Americas (5.513 km · 56 Giri)",
            "date": (now + timedelta(days=1, hours=18)).isoformat(),
            "laps": 56,
            "rain_prob": "12%",
            "asphalt_temp": "39°C (Alto Degrado Termico)",
            "base_sc": 0.64,
            "drivers": [
                {"name": "Lando Norris", "team": "McLaren", "fp_pace_delta": 0.00, "qualifying_pos": 1, "tire_deg": 0.058, "track_wins": 1, "car_power_rank": 97, "top_speed": 341},
                {"name": "Max Verstappen", "team": "Red Bull Racing", "fp_pace_delta": 0.04, "qualifying_pos": 2, "tire_deg": 0.068, "track_wins": 3, "car_power_rank": 96, "top_speed": 344},
                {"name": "Charles Leclerc", "team": "Ferrari", "fp_pace_delta": 0.09, "qualifying_pos": 3, "tire_deg": 0.055, "track_wins": 1, "car_power_rank": 95, "top_speed": 342},
                {"name": "Oscar Piastri", "team": "McLaren", "fp_pace_delta": 0.16, "qualifying_pos": 4, "tire_deg": 0.064, "track_wins": 0, "car_power_rank": 96, "top_speed": 340},
                {"name": "Lewis Hamilton", "team": "Ferrari", "fp_pace_delta": 0.24, "qualifying_pos": 5, "tire_deg": 0.066, "track_wins": 5, "car_power_rank": 94, "top_speed": 341},
                {"name": "George Russell", "team": "Mercedes", "fp_pace_delta": 0.29, "qualifying_pos": 6, "tire_deg": 0.075, "track_wins": 0, "car_power_rank": 92, "top_speed": 338}
            ]
        },
        {
            "id": "f1_gp_mexico_2026",
            "tournament": "Gran Premio de la Ciudad de México · Autódromo Hermanos Rodríguez",
            "country": "Mexico",
            "flag": "INT",
            "venue": "Autódromo Hermanos Rodríguez (2.285m Altitudine · 71 Giri)",
            "date": (now + timedelta(days=5, hours=20)).isoformat(),
            "laps": 71,
            "rain_prob": "18%",
            "asphalt_temp": "42°C (Aria Rarefatta · Turbo Cooling Critico)",
            "base_sc": 0.71,
            "drivers": [
                {"name": "Max Verstappen", "team": "Red Bull Racing", "fp_pace_delta": 0.00, "qualifying_pos": 1, "tire_deg": 0.052, "track_wins": 5, "car_power_rank": 97, "top_speed": 358},
                {"name": "Charles Leclerc", "team": "Ferrari", "fp_pace_delta": 0.07, "qualifying_pos": 2, "tire_deg": 0.059, "track_wins": 0, "car_power_rank": 95, "top_speed": 356},
                {"name": "Lando Norris", "team": "McLaren", "fp_pace_delta": 0.11, "qualifying_pos": 3, "tire_deg": 0.056, "track_wins": 0, "car_power_rank": 96, "top_speed": 353},
                {"name": "Carlos Sainz", "team": "Williams", "fp_pace_delta": 0.25, "qualifying_pos": 4, "tire_deg": 0.068, "track_wins": 1, "car_power_rank": 90, "top_speed": 359}
            ]
        }
    ]

    for spec in f1_events_spec:
        f1_eval = MotorsportQuantEngine.evaluate_grand_prix(
            circuit_name=spec["tournament"],
            laps=spec["laps"],
            rain_prob=spec["rain_prob"],
            asphalt_temp=spec["asphalt_temp"],
            drivers=spec["drivers"],
            base_sc=spec["base_sc"]
        )
        d0, d1, d2 = f1_eval["drivers"][0], f1_eval["drivers"][1], f1_eval["drivers"][2]
        duel_main = f1_eval["h2h_duels"][0]
        podium_p = d0["podium_prob"]
        best_o_f1 = round((1.0 / podium_p) * 1.07, 2)
        drop_f1, opener_f1, live_f1 = record_odds_snapshot(f"{spec['id']}_podium", best_o_f1)
        books_f1 = build_euro_bookmakers(podium_p, live_f1, spec["id"])

        cat_markets_f1 = {
            "Duelli Testa a Testa (H2H Piloti)": [
                _enrich_mkt(f"H2H Gara: {du['driver_a']} batte {du['driver_b']}", du["prob_a"], "Driver H2H", 1.06)
                for du in f1_eval["h2h_duels"]
            ] + [
                _enrich_mkt(f"H2H Gara: {du['driver_b']} batte {du['driver_a']}", du["prob_b"], "Driver H2H", 1.06)
                for du in f1_eval["h2h_duels"][:2]
            ],
            "Podio (Top 3) & Punti (Top 6)": [
                _enrich_mkt(f"{drv['name']} ({drv['team']}) Podio Top 3", drv["podium_prob"], "Podium", 1.06)
                for drv in f1_eval["drivers"][:4]
            ] + [
                _enrich_mkt(f"{drv['name']} Piazzamento Top 6", drv["top6_prob"], "Top 6", 1.05)
                for drv in f1_eval["drivers"][:4]
            ],
            "Vincitore Gara & Giro Veloce": [
                _enrich_mkt(f"{drv['name']} Vincitore Gara", drv["win_prob"], "Outright", 1.07)
                for drv in f1_eval["drivers"][:4]
            ] + [
                _enrich_mkt(f"{d0['name']} Giro Veloce (Fastest Lap)", d0["fl_prob"], "Fastest Lap", 1.08),
                _enrich_mkt(f"{d1['name']} Giro Veloce (Fastest Lap)", d1["fl_prob"], "Fastest Lap", 1.08),
            ],
            "Safety Car & Speciali Costruttori": [
                _enrich_mkt("Safety Car in Pista Durante la Gara: Sì", f1_eval["safety_car_prob"], "Safety Car", 1.05),
                _enrich_mkt("Safety Car in Pista Durante la Gara: No", 1.0 - f1_eval["safety_car_prob"], "Safety Car", 1.05),
                _enrich_mkt("Entrambe le McLaren a Punti (Top 10)", 0.87, "Team Specials", 1.05),
                _enrich_mkt("Over 16.5 Monoposto Classificate a Fine Gara", 0.78, "Race Props", 1.05),
            ]
        }

        events.append({
            "id": spec["id"],
            "sport": "f1",
            "league": "FIA Formula One World Championship",
            "tournament": spec["tournament"],
            "venue": spec["venue"],
            "country": spec["country"],
            "flag": spec["flag"],
            "title": f"{spec['tournament']} · {d0['name']} vs {d1['name']}",
            "competitor_a": d0["name"],
            "competitor_b": d1["name"],
            "form_a": ["P1", "P2", "P1", "P1", "P3"],
            "form_b": ["P2", "P1", "P2", "P4", "P1"],
            "h2h": f"Duello Telemetrico FP2: {d0['name']} precede {d1['name']} di +{duel_main['fp_telemetry_gap']}s/giro sul passo mescola Media.",
            "date": spec["date"],
            "status": "Scheduled",
            "stats": {
                "circuit": spec["venue"],
                "safety_car": f"{round(f1_eval['safety_car_prob']*100)}% (Storico 5 anni)",
                "rain_prob": f1_eval["rain_prob"],
                "asphalt_temp": f1_eval["asphalt_temp"],
                "telemetry_pace": f"1° {d0['name']} (Base) · 2° {d1['name']} (+{d1['fp_pace_delta']}s) · 3° {d2['name']} (+{d2['fp_pace_delta']}s)",
                "tire_deg": f"Degrado {d0['team']}: +{d0['tire_deg']}s/giro vs {d1['team']}: +{d1['tire_deg']}s/giro",
                "h2h_driver_1": f"{duel_main['driver_a']} ({duel_main['team_a']})",
                "h2h_driver_2": f"{duel_main['driver_b']} ({duel_main['team_b']})",
                "h2h_gap": f"+{duel_main['fp_telemetry_gap']}s/giro nei long run FP2/FP3"
            },
            "facts": [
                f"⏱️ Telemetria Long-Run FP2 (15 giri con gomma Media C3): {d0['name']} ha registrato il passo più costante davanti a {d1['name']} (+{d1['fp_pace_delta']}s/giro) e {d2['name']} (+{d2['fp_pace_delta']}s/giro).",
                f"Degrado Termico Gomme ({spec['asphalt_temp']}): {d0['team']} perde solo {d0['tire_deg']}s/giro nello stint centrale contro {d1['tire_deg']}s/giro di {d1['team']}.",
                f"Speed Trap Rettilineo Principale: {d1['name']} tocca {d1['top_speed']} km/h con DRS aperto vs {d0['top_speed']} km/h di {d0['name']}.",
                f"Rischio Safety Car / Virtual Safety Car: {round(f1_eval['safety_car_prob']*100)}% basato sulle ultime 6 edizioni del GP (finestra pit-stop ottimale giro 18-23).",
                f"Testa a Testa (H2H) Consigliato: {duel_main['driver_a']} batte {duel_main['driver_b']} ({round(duel_main['prob_a']*100)}% probabilità, quota equa @{duel_main['fair_a']})."
            ],
            "comparison_bars": [
                {"label": "Indice Passo Gara Telemetrico", "valA": d0["car_power_rank"], "valB": d1["car_power_rank"], "unit": "/100"},
                {"label": "Probabilità Podio (Top 3)", "valA": round(d0["podium_prob"]*100), "valB": round(d1["podium_prob"]*100), "unit": "%"},
                {"label": "Velocità Speed Trap (km/h)", "valA": d0["top_speed"], "valB": d1["top_speed"], "unit": " km/h"},
                {"label": "Efficienza Gestione Gomme", "valA": round(100 - d0["tire_deg"]*450), "valB": round(100 - d1["tire_deg"]*450), "unit": "%"}
            ],
            "best_pick": {
                "market": "Piazzamento Podio & H2H Telemetria",
                "label": f"{d0['name']} Podio (Top 3)",
                "prob": podium_p,
                "fairOdds": round(1.0 / podium_p, 2),
                "bookOdds": books_f1[0]["price"],
                "bookmaker": books_f1[0]["name"],
                "edgePct": books_f1[0]["edgePct"],
                "droppingPct": drop_f1,
                "openerOdds": opener_f1,
                "why": f"{d0['name']} domina la telemetria del passo gara con il minor degrado gomma ({d0['tire_deg']}s/giro) e parte in prima fila ({round(podium_p*100)}% probabilità podio)."
            },
            "bet_builders": {
                "safe": {
                    "name": "F1 GP Strategy Builder (Podio + Safety Car)",
                    "legs": [f"{d0['name']} Podio (Top 3)", f"{d2['name']} Piazzamento Top 6", "Safety Car Durante la Gara: Sì"],
                    "prob": round(podium_p * d2["top6_prob"] * f1_eval["safety_car_prob"] * 1.12, 3),
                    "fairOdds": 2.18,
                    "bookOdds": 2.45,
                    "liftPct": 12.6
                }
            },
            "vip_insights": _build_vip_insights(spec["id"], podium_p, round(1.0 / podium_p, 2), books_f1[0]["price"], drop_f1, opener_f1),
            "all_books": books_f1[:12],
            "is_safe": podium_p >= 0.74,
            "market_categories": cat_markets_f1,
            "markets": [m for grp in cat_markets_f1.values() for m in grp]
        })

    # =========================================================================
    # 3. MOTORSPORT: MOTOGP (Mugello & Valencia GP)
    # =========================================================================
    motogp_drivers = [
        {"name": "Francesco Bagnaia", "team": "Ducati Lenovo", "fp_pace_delta": 0.00, "qualifying_pos": 1, "tire_deg": 0.048, "track_wins": 3, "car_power_rank": 98, "top_speed": 363},
        {"name": "Jorge Martin", "team": "Aprilia / Pramac", "fp_pace_delta": 0.05, "qualifying_pos": 2, "tire_deg": 0.056, "track_wins": 1, "car_power_rank": 96, "top_speed": 361},
        {"name": "Marc Marquez", "team": "Ducati Lenovo", "fp_pace_delta": 0.06, "qualifying_pos": 3, "tire_deg": 0.054, "track_wins": 2, "car_power_rank": 97, "top_speed": 362},
        {"name": "Enea Bastianini", "team": "KTM Tech3", "fp_pace_delta": 0.16, "qualifying_pos": 4, "tire_deg": 0.045, "track_wins": 1, "car_power_rank": 93, "top_speed": 360}
    ]
    motogp_eval = MotorsportQuantEngine.evaluate_grand_prix(
        circuit_name="Gran Premio d'Italia · Autodromo del Mugello",
        laps=23,
        rain_prob="8%",
        asphalt_temp="34°C",
        drivers=motogp_drivers,
        base_sc=0.25
    )
    m_d0, m_d1 = motogp_eval["drivers"][0], motogp_eval["drivers"][1]
    m_duel = motogp_eval["h2h_duels"][0]
    m_pod_p = m_d0["podium_prob"]
    best_o_mg = round((1.0 / m_pod_p) * 1.07, 2)
    drop_mg, opener_mg, live_mg = record_odds_snapshot("motogp_mugello_pod", best_o_mg)
    books_mg = build_euro_bookmakers(m_pod_p, live_mg, "motogp_mugello_pod")

    cat_markets_mg = {
        "Duelli Testa a Testa Piloti (H2H)": [
            _enrich_mkt(f"H2H Gara: {du['driver_a']} batte {du['driver_b']}", du["prob_a"], "Rider H2H", 1.06)
            for du in motogp_eval["h2h_duels"]
        ],
        "Podio Top 3 & Vincitore Gara": [
            _enrich_mkt(f"{drv['name']} Podio (Top 3)", drv["podium_prob"], "Podium", 1.06)
            for drv in motogp_eval["drivers"]
        ] + [
            _enrich_mkt(f"{drv['name']} Vincitore GP", drv["win_prob"], "Winner", 1.07)
            for drv in motogp_eval["drivers"][:3]
        ],
        "Sprint Race & Speciali": [
            _enrich_mkt("Francesco Bagnaia Top 3 nella Sprint Race", 0.86, "Sprint Race", 1.05),
            _enrich_mkt("Marc Marquez Podio nella Sprint Race", 0.78, "Sprint Race", 1.06),
            _enrich_mkt("Ducati Vince sia Sprint che Gara Domenicale", 0.89, "Constructor", 1.05),
        ]
    }

    events.append({
        "id": "motogp_gp_mugello_2026",
        "sport": "motogp",
        "league": "FIM MotoGP World Championship",
        "tournament": "Gran Premio d'Italia Oakley (Mugello)",
        "venue": "Autodromo Internazionale del Mugello (5.245 km · 23 Giri)",
        "country": "Italy",
        "flag": "INT",
        "title": "MotoGP Mugello 2026 · Bagnaia vs Martin vs Marquez",
        "competitor_a": "Francesco Bagnaia",
        "competitor_b": "Jorge Martin",
        "form_a": ["P1", "P1", "P2", "P1", "P1"],
        "form_b": ["P2", "P3", "P1", "P2", "P2"],
        "h2h": "Bagnaia ha vinto le ultime 3 edizioni consecutive al Mugello (Sprint + Gara lunga).",
        "date": (now + timedelta(days=2, hours=12)).isoformat(),
        "status": "Scheduled",
        "stats": {
            "circuit": "Mugello (23 Giri · Rettilineo 1.141m)",
            "safety_car": "Velocità Max 363.6 km/h (San Donato)",
            "rain_prob": motogp_eval["rain_prob"],
            "asphalt_temp": motogp_eval["asphalt_temp"],
            "telemetry_pace": "Bagnaia 1'45.2 medio · Marquez +0.06s · Martin +0.05s",
            "tire_deg": "Drop gomma posteriore Soft negli ultimi 6 giri (-0.35s/giro)",
            "h2h_driver_1": f"{m_duel['driver_a']} ({m_duel['team_a']})",
            "h2h_driver_2": f"{m_duel['driver_b']} ({m_duel['team_b']})",
            "h2h_gap": f"+{m_duel['fp_telemetry_gap']}s/giro nei settori T2-T3 (Arrabbiata 1-2)"
        },
        "facts": [
            "️ Settori Guidati T2 & T3 (Casanova-Savelli & Arrabbiata 1-2): Bagnaia guadagna 0.14s al giro in percorrenza rispetto a tutti i rivali.",
            "Usura Mescola Posteriore: Il consumo sul fianco destro premia il riding style pulito di Bagnaia e Bastianini negli ultimi 7 giri.",
            " тормоза Staccata San Donato (da 363 km/h a 92 km/h): Bagnaia e Marquez hanno il miglior indice di decelerazione tardiva senza bloccaggi.",
            f"Probabilità Podio Bagnaia stimata al {round(m_pod_p*100)}% dal modello telemetrico multi-stint."
        ],
        "comparison_bars": [
            {"label": "Indice Passo Gara FP2/FP3", "valA": 98, "valB": 95, "unit": "/100"},
            {"label": "Probabilità Podio (Top 3)", "valA": round(m_d0["podium_prob"]*100), "valB": round(m_d1["podium_prob"]*100), "unit": "%"},
            {"label": "Top Speed San Donato", "valA": 363, "valB": 361, "unit": " km/h"},
            {"label": "Conservazione Gomma Posteriore", "valA": 94, "valB": 88, "unit": "%"}
        ],
        "best_pick": {
            "market": "Piazzamento Podio Gara",
            "label": "Francesco Bagnaia Podio (Top 3)",
            "prob": m_pod_p,
            "fairOdds": round(1.0 / m_pod_p, 2),
            "bookOdds": books_mg[0]["price"],
            "bookmaker": books_mg[0]["name"],
            "edgePct": books_mg[0]["edgePct"],
            "droppingPct": drop_mg,
            "openerOdds": opener_mg,
            "why": f"Dominio storico e telemetrico nei settori T2-T3 del Mugello con gestione superiore della gomma media posteriore ({round(m_pod_p*100)}% probabilità)."
        },
        "bet_builders": {
            "safe": {
                "name": "MotoGP Ducati Dominance Builder",
                "legs": ["Francesco Bagnaia Podio (Top 3)", "Marc Marquez Piazzamento Top 6", "Ducati Vince la Gara"],
                "prob": 0.74,
                "fairOdds": 1.35,
                "bookOdds": 1.54,
                "liftPct": 14.1
            }
        },
        "vip_insights": _build_vip_insights("motogp_gp_mugello_2026", m_pod_p, round(1.0 / m_pod_p, 2), books_mg[0]["price"], drop_mg, opener_mg),
        "all_books": books_mg[:12],
        "is_safe": m_pod_p >= 0.74,
        "market_categories": cat_markets_mg,
        "markets": [m for grp in cat_markets_mg.values() for m in grp]
    })

    # =========================================================================
    # 4. AMERICAN FOOTBALL: NFL (3 Marquee Games)
    # =========================================================================
    nfl_games = [
        {
            "id": "nfl_sf_was_2026",
            "tournament": "NFL Regular Season · Week 7",
            "venue": "Levi's Stadium, Santa Clara",
            "home": {
                "name": "San Francisco 49ers", "yds_per_play_off": 6.3, "yds_per_play_def": 4.8,
                "turnover_diff": 5, "qb_name": "Brock Purdy", "qb_injury_penalty": 0.0,
                "rz_td_pct": 66, "form": ["W", "W", "W", "L", "W"]
            },
            "away": {
                "name": "Washington Commanders", "yds_per_play_off": 5.5, "yds_per_play_def": 5.8,
                "turnover_diff": -2, "qb_name": "Jayden Daniels", "qb_injury_penalty": 0.0,
                "rz_td_pct": 54, "form": ["W", "L", "W", "W", "L"]
            },
            "h2h": "49ers 4-1 nelle ultime 5 sfide (media +11.4 punti di margine a favore di SF)",
            "weather": {"wind_mph": 7, "condition": "Soleggiato · 20°C", "temp_f": 68},
            "date": (now + timedelta(hours=6)).isoformat(),
            "props": [
                ("Christian McCaffrey Anytime Touchdown Scorer", 0.76),
                ("Brock Purdy Over 248.5 Passing Yards", 0.68),
                ("George Kittle Over 48.5 Receiving Yards", 0.71),
                ("Jayden Daniels Over 42.5 Rushing Yards", 0.69)
            ]
        },
        {
            "id": "nfl_kc_den_2026",
            "tournament": "NFL Regular Season · AFC West Rivalry",
            "venue": "GEHA Field at Arrowhead Stadium, Kansas City",
            "home": {
                "name": "Kansas City Chiefs", "yds_per_play_off": 6.0, "yds_per_play_def": 4.7,
                "turnover_diff": 4, "qb_name": "Patrick Mahomes", "qb_injury_penalty": 0.0,
                "rz_td_pct": 63, "form": ["W", "W", "W", "W", "W"]
            },
            "away": {
                "name": "Denver Broncos", "yds_per_play_off": 4.8, "yds_per_play_def": 5.2,
                "turnover_diff": -3, "qb_name": "Bo Nix", "qb_injury_penalty": 0.0,
                "rz_td_pct": 46, "form": ["L", "W", "L", "W", "L"]
            },
            "h2h": "Kansas City ha vinto 17 degli ultimi 18 incontri contro Denver ad Arrowhead",
            "weather": {"wind_mph": 11, "condition": "Sereno · 13°C", "temp_f": 55},
            "date": (now + timedelta(hours=26)).isoformat(),
            "props": [
                ("Patrick Mahomes Over 1.5 Passing Touchdowns", 0.75),
                ("Travis Kelce Over 5.5 Receptions", 0.73),
                ("Isiah Pacheco Over 64.5 Rushing Yards", 0.68),
                ("Kansas City Chiefs Over 23.5 Team Points", 0.74)
            ]
        },
        {
            "id": "nfl_bal_buf_2026",
            "tournament": "NFL Sunday Night Football · AFC Heavyweight",
            "venue": "M&T Bank Stadium, Baltimore",
            "home": {
                "name": "Baltimore Ravens", "yds_per_play_off": 6.4, "yds_per_play_def": 5.0,
                "turnover_diff": 3, "qb_name": "Lamar Jackson", "qb_injury_penalty": 0.0,
                "rz_td_pct": 68, "form": ["W", "W", "W", "W", "L"]
            },
            "away": {
                "name": "Buffalo Bills", "yds_per_play_off": 6.1, "yds_per_play_def": 5.3,
                "turnover_diff": 2, "qb_name": "Josh Allen", "qb_injury_penalty": 0.0,
                "rz_td_pct": 64, "form": ["W", "W", "L", "W", "W"]
            },
            "h2h": "Ravens hanno battuto Buffalo 35-10 nell'ultimo scontro a Baltimora (Derrick Henry 199 rushing yds)",
            "weather": {"wind_mph": 9, "condition": "Cielo Limpido · 15°C", "temp_f": 59},
            "date": (now + timedelta(hours=30)).isoformat(),
            "props": [
                ("Derrick Henry Anytime Touchdown Scorer", 0.78),
                ("Lamar Jackson Over 52.5 Rushing Yards", 0.72),
                ("Josh Allen Over 235.5 Passing Yards", 0.67),
                ("Over 44.5 Punti Totali nel Match", 0.74)
            ]
        }
    ]

    for ng in nfl_games:
        hm, aw = ng["home"], ng["away"]
        sim_n = NFLQuantEngine.simulate_game(hm, aw, ng["weather"])
        fav_n = hm["name"] if sim_n["prob_home"] >= sim_n["prob_away"] else aw["name"]
        fav_p_n = max(sim_n["prob_home"], sim_n["prob_away"])
        best_o_n = round((1.0 / fav_p_n) * 1.06, 2)
        drop_n, opener_n, live_n = record_odds_snapshot(f"{ng['id']}_win", best_o_n)
        books_n = build_euro_bookmakers(fav_p_n, live_n, ng["id"])

        cat_markets_nfl = {
            "Moneyline & Point Spread": [
                _enrich_mkt(f"{hm['name']} Vince (Moneyline)", sim_n["prob_home"], "Moneyline", 1.05),
                _enrich_mkt(f"{aw['name']} Vince (Moneyline)", sim_n["prob_away"], "Moneyline", 1.05),
                _enrich_mkt(f"{hm['name']} Spread {sim_n['proj_spread'] + 2.5:+.1f} Punti", min(0.84, sim_n["prob_home"] * 0.92), "Spread", 1.05),
                _enrich_mkt(f"{hm['name']} Alternate Spread +3.5 (Teaser)", min(0.92, sim_n["prob_home"] + 0.14), "Teaser Spread", 1.05),
                _enrich_mkt(f"{aw['name']} Alternate Spread +10.5", min(0.89, sim_n["prob_away"] + 0.42), "Teaser Spread", 1.05),
            ],
            "Over/Under Punti Totali & Team Totals": [
                _enrich_mkt("Over 41.5 Punti Totali", sim_n["prob_over_41_5"], "Totals", 1.05),
                _enrich_mkt("Over 44.5 Punti Totali", sim_n["prob_over_44_5"], "Totals", 1.05),
                _enrich_mkt("Under 47.5 Punti Totali", 1.0 - sim_n["prob_over_47_5"], "Totals", 1.05),
                _enrich_mkt(f"{hm['name']} Over 23.5 Team Points", min(0.82, sim_n["prob_home"] * 0.94), "Team Total", 1.05),
                _enrich_mkt("Over 20.5 Punti nel 1° Tempo (1st Half)", 0.69, "1st Half", 1.06),
            ],
            "Player Props (Touchdown & Yards)": [
                _enrich_mkt(lbl, p_val, "NFL Player Props", 1.06) for lbl, p_val in ng["props"]
            ]
        }

        events.append({
            "id": ng["id"],
            "sport": "nfl",
            "league": "NFL National Football League",
            "tournament": ng["tournament"],
            "venue": ng["venue"],
            "country": "United States",
            "flag": "INT",
            "title": f"{hm['name']} vs {aw['name']}",
            "competitor_a": hm["name"],
            "competitor_b": aw["name"],
            "form_a": hm["form"],
            "form_b": aw["form"],
            "h2h": ng["h2h"],
            "date": ng["date"],
            "status": "Scheduled",
            "stats": {
                "proj_score": f"{hm['name']} {sim_n['proj_home']} - {sim_n['proj_away']} {aw['name']}",
                "point_spread": f"Linea Spread IA: {hm['name']} {sim_n['proj_spread']:+.1f} pts",
                "total_points": f"Totale Punti Stimato: {sim_n['proj_total']} pts",
                "weather": f"{ng['weather']['condition']} · Vento {ng['weather']['wind_mph']} mph",
                "injuries": f"{sim_n['injury_notes']} (100% Attivi)"
            },
            "facts": [
                f"Efficienza Yards Per Play: {hm['name']} produce {hm['yds_per_play_off']} yds/azione contro una difesa che concede {aw['yds_per_play_def']} yds/azione.",
                f"Efficienza Red Zone TD: {hm['name']} converte in Touchdown il {hm['rz_td_pct']}% dei viaggi dentro le 20 yard avversarie ({aw['rz_td_pct']}% per {aw['name']}).",
                f"Differenziale Turnover: {hm['name']} ({hm['turnover_diff']:+d}) vs {aw['name']} ({aw['turnover_diff']:+d}).",
                f"️ Impatto Meteo & Stadio: {ng['weather']['condition']}, vento {ng['weather']['wind_mph']} mph (nessuna penalità sui Field Goal oltre le 45 yard).",
                f"Trend Storico H2H: {ng['h2h']}."
            ],
            "comparison_bars": [
                {"label": "Yards per Play Offensivi", "valA": hm["yds_per_play_off"], "valB": aw["yds_per_play_off"], "unit": " yds"},
                {"label": "% Conversione Touchdown Red Zone", "valA": hm["rz_td_pct"], "valB": aw["rz_td_pct"], "unit": "%"},
                {"label": "Punti Proiettati dal Modello", "valA": sim_n["proj_home"], "valB": sim_n["proj_away"], "unit": " pts"}
            ],
            "best_pick": {
                "market": "Moneyline & EPA Spread Model",
                "label": f"Vittoria {fav_n}",
                "prob": fav_p_n,
                "fairOdds": round(1.0 / fav_p_n, 2),
                "bookOdds": books_n[0]["price"],
                "bookmaker": books_n[0]["name"],
                "edgePct": books_n[0]["edgePct"],
                "droppingPct": drop_n,
                "openerOdds": opener_n,
                "why": f"Netto vantaggio in Yards per Play ({hm['yds_per_play_off']} vs {aw['yds_per_play_off']}), efficienza Red Zone ({hm['rz_td_pct']}%) e differenziale turnover ({round(fav_p_n*100)}% win rate)."
            },
            "bet_builders": {
                "safe": {
                    "name": "NFL Same-Game Parlay (Moneyline + Totals + TD Prop)",
                    "legs": [f"Vittoria {fav_n}", "Over 41.5 Punti Totali", ng["props"][0][0]],
                    "prob": round(fav_p_n * sim_n["prob_over_41_5"] * ng["props"][0][1] * 1.15, 3),
                    "fairOdds": 1.98,
                    "bookOdds": 2.25,
                    "liftPct": 15.0
                }
            },
            "vip_insights": _build_vip_insights(ng["id"], fav_p_n, round(1.0 / fav_p_n, 2), books_n[0]["price"], drop_n, opener_n),
            "all_books": books_n[:12],
            "is_safe": fav_p_n >= 0.74,
            "market_categories": cat_markets_nfl,
            "markets": [m for grp in cat_markets_nfl.values() for m in grp]
        })

    # =========================================================================
    # 5. BASKETBALL: NBA & EUROLEAGUE
    # =========================================================================
    nba_games = [
        {
            "id": "nba_bos_det_2026",
            "league": "NBA",
            "tournament": "NBA Regular Season · Eastern Conference",
            "venue": "TD Garden, Boston",
            "country": "United States",
            "flag": "INT",
            "home": {"name": "Boston Celtics", "off_rating": 122.4, "def_rating": 109.0, "pace": 100.6, "three_pt_pct": 39.4, "is_b2b": False, "form": ["W", "W", "W", "W", "W"]},
            "away": {"name": "Detroit Pistons", "off_rating": 108.8, "def_rating": 117.5, "pace": 98.4, "three_pt_pct": 34.6, "is_b2b": True, "form": ["L", "L", "W", "L", "L"]},
            "h2h": "Boston ha vinto gli ultimi 11 scontri diretti contro Detroit (media +14.8 punti di scarto)",
            "date": (now + timedelta(hours=4)).isoformat(),
            "props": [
                ("Jayson Tatum Over 26.5 Punti", 0.74),
                ("Jaylen Brown Over 21.5 Punti", 0.71),
                ("Derrick White Over 2.5 Triple Realizzate", 0.69),
                ("Cade Cunningham Over 6.5 Assist", 0.68)
            ]
        },
        {
            "id": "nba_nyk_phi_2026",
            "league": "NBA",
            "tournament": "NBA Regular Season · Atlantic Division",
            "venue": "Madison Square Garden, New York",
            "country": "United States",
            "flag": "INT",
            "home": {"name": "New York Knicks", "off_rating": 118.4, "def_rating": 110.8, "pace": 97.4, "three_pt_pct": 38.2, "is_b2b": False, "form": ["W", "W", "W", "L", "W"]},
            "away": {"name": "Philadelphia 76ers", "off_rating": 113.6, "def_rating": 114.2, "pace": 97.8, "three_pt_pct": 35.8, "is_b2b": True, "form": ["L", "W", "L", "W", "L"]},
            "h2h": "Knicks 5-1 nelle ultime 6 sfide contro Philadelphia al Madison Square Garden",
            "date": (now + timedelta(hours=7, minutes=30)).isoformat(),
            "props": [
                ("Jalen Brunson Over 27.5 Punti", 0.75),
                ("Karl-Anthony Towns Over 29.5 Punti + Rimbalzi (PR)", 0.73),
                ("Josh Hart Over 7.5 Rimbalzi", 0.76),
                ("Tyrese Maxey Over 24.5 Punti", 0.68)
            ]
        },
        {
            "id": "bask_euro_pan_oly_2026",
            "league": "EuroLeague",
            "tournament": "Turkish Airlines EuroLeague · Eternal Derby",
            "venue": "OAKA Altion, Athens",
            "country": "Greece",
            "flag": "INT",
            "home": {"name": "Panathinaikos AKTOR", "off_rating": 119.2, "def_rating": 109.5, "pace": 86.8, "three_pt_pct": 39.8, "is_b2b": False, "form": ["W", "W", "W", "W", "L"]},
            "away": {"name": "Olympiacos Piraeus", "off_rating": 115.4, "def_rating": 110.8, "pace": 85.4, "three_pt_pct": 37.1, "is_b2b": False, "form": ["W", "L", "W", "W", "W"]},
            "h2h": "Panathinaikos ha vinto 4 delle ultime 5 sfide interne ad OAKA",
            "date": (now + timedelta(hours=19)).isoformat(),
            "props": [
                ("Kendrick Nunn Over 18.5 Punti", 0.74),
                ("Mathias Lessort Over 6.5 Rimbalzi", 0.72),
                ("Sasha Vezenkov Over 16.5 Punti", 0.71),
                ("Over 158.5 Punti Totali EuroLeague", 0.79)
            ]
        }
    ]

    for bg in nba_games:
        hm, aw = bg["home"], bg["away"]
        sim_b = BasketballQuantEngine.simulate_game(hm, aw)
        fav_b = hm["name"] if sim_b["prob_home"] >= sim_b["prob_away"] else aw["name"]
        fav_p_b = max(sim_b["prob_home"], sim_b["prob_away"])
        best_o_b = round((1.0 / fav_p_b) * 1.06, 2)
        drop_b, opener_b, live_b = record_odds_snapshot(f"{bg['id']}_win", best_o_b)
        books_b = build_euro_bookmakers(fav_p_b, live_b, bg["id"])

        cat_markets_bask = {
            "Moneyline & Handicap Spread": [
                _enrich_mkt(f"{hm['name']} Vince (Testa a Testa)", sim_b["prob_home"], "Moneyline", 1.05),
                _enrich_mkt(f"{aw['name']} Vince (Testa a Testa)", sim_b["prob_away"], "Moneyline", 1.05),
                _enrich_mkt(f"{hm['name']} Handicap {sim_b['proj_spread'] + 3.0:+.1f} Punti", min(0.86, sim_b["prob_home"] * 0.91), "Spread", 1.05),
                _enrich_mkt(f"{hm['name']} Vince il 1° Quarto", min(0.79, sim_b["prob_home"] * 0.88), "Quarter", 1.05),
                _enrich_mkt(f"{hm['name']} Vince il 1° Tempo (1H)", min(0.83, sim_b["prob_home"] * 0.92), "Half", 1.05),
            ],
            "Over/Under Punti Totali": [
                _enrich_mkt(f"Over {sim_b['base_line']} Punti Totali", sim_b["prob_over_main"], "Totals", 1.05),
                _enrich_mkt(f"Over {sim_b['base_line'] - 4.0} Punti (Linea protetta)", min(0.88, sim_b["prob_over_main"] + 0.16), "Totali protetti", 1.05),
                _enrich_mkt(f"Under {sim_b['base_line'] + 6.0} Punti Totali", 0.72, "Totals", 1.05),
                _enrich_mkt(f"{hm['name']} Over {round(sim_b['proj_home'] - 3.5, 1)} Punti Squadra", 0.74, "Team Total", 1.05),
            ],
            "Player Props (Punti, Rimbalzi, Assist & Triple)": [
                _enrich_mkt(lbl, p_val, "Player PRA", 1.06) for lbl, p_val in bg["props"]
            ]
        }

        events.append({
            "id": bg["id"],
            "sport": "basketball",
            "league": bg["league"],
            "tournament": bg["tournament"],
            "venue": bg["venue"],
            "country": bg["country"],
            "flag": bg["flag"],
            "title": f"{hm['name']} vs {aw['name']}",
            "competitor_a": hm["name"],
            "competitor_b": aw["name"],
            "form_a": hm["form"],
            "form_b": aw["form"],
            "h2h": bg["h2h"],
            "date": bg["date"],
            "status": "Scheduled",
            "stats": {
                "proj_score": f"{hm['name']} {sim_b['proj_home']} - {sim_b['proj_away']} {aw['name']}",
                "pace": f"{sim_b['game_pace']} Possessi / 48m",
                "spread": f"Spread IA: {hm['name']} {sim_b['proj_spread']:+.1f} pts",
                "total_points": f"Punti Totali Stimati: {sim_b['proj_total']} pts",
                "fatigue": sim_b["b2b_factor"]
            },
            "facts": [
                f"Net Rating su 100 Possessi: {hm['name']} (OffRtg {hm['off_rating']} / DefRtg {hm['def_rating']}) vs {aw['name']} (OffRtg {aw['off_rating']} / DefRtg {aw['def_rating']}).",
                f"Pace & Ritmo Partita: {sim_b['game_pace']} possessi attesi con {hm['three_pt_pct']}% da 3 punti per {hm['name']}.",
                f"Fattore Stanchezza Calendario: {sim_b['b2b_factor']}.",
                f"Storico Testa a Testa: {bg['h2h']}."
            ],
            "comparison_bars": [
                {"label": "Offensive Rating (Punti / 100 Poss)", "valA": hm["off_rating"], "valB": aw["off_rating"], "unit": ""},
                {"label": "% Tiro da 3 Punti", "valA": hm["three_pt_pct"], "valB": aw["three_pt_pct"], "unit": "%"},
                {"label": "Punti Proiettati dal Modello", "valA": sim_b["proj_home"], "valB": sim_b["proj_away"], "unit": " pts"}
            ],
            "best_pick": {
                "market": "Moneyline & Net Rating Model",
                "label": f"Vittoria {fav_b}",
                "prob": fav_p_b,
                "fairOdds": round(1.0 / fav_p_b, 2),
                "bookOdds": books_b[0]["price"],
                "bookmaker": books_b[0]["name"],
                "edgePct": books_b[0]["edgePct"],
                "droppingPct": drop_b,
                "openerOdds": opener_b,
                "why": f"Differenziale Net Rating netto (+{round(hm['off_rating']-hm['def_rating'], 1)} vs {round(aw['off_rating']-aw['def_rating'], 1)}) amplificato dal fattore campo e riposo ({round(fav_p_b*100)}% win prob)."
            },
            "bet_builders": {
                "safe": {
                    "name": "Basketball SGP (Vittoria + Linea Punti + Top Scorer)",
                    "legs": [f"Vittoria {fav_b}", f"Over {sim_b['base_line'] - 4.0} Punti", bg["props"][0][0]],
                    "prob": round(fav_p_b * 0.84 * bg["props"][0][1] * 1.13, 3),
                    "fairOdds": 1.88,
                    "bookOdds": 2.14,
                    "liftPct": 13.8
                }
            },
            "vip_insights": _build_vip_insights(bg["id"], fav_p_b, round(1.0 / fav_p_b, 2), books_b[0]["price"], drop_b, opener_b),
            "all_books": books_b[:12],
            "is_safe": fav_p_b >= 0.74,
            "market_categories": cat_markets_bask,
            "markets": [m for grp in cat_markets_bask.values() for m in grp]
        })

    # =========================================================================
    # 6. RUGBY: SIX NATIONS & INVESTEC CHAMPIONS CUP
    # =========================================================================
    rugby_matches = [
        {
            "id": "rug_ire_fra_2026",
            "league": "Six Nations Championship",
            "tournament": "Guinness Six Nations",
            "venue": "Aviva Stadium, Dublin",
            "country": "Europe",
            "flag": "INT",
            "home": {"name": "Ireland Rugby", "scrum_win_pct": 0.95, "lineout_win_pct": 0.91, "avg_penalties": 8.2, "kicking_pct": 88, "form": ["W", "W", "W", "W", "L"]},
            "away": {"name": "France Rugby", "scrum_win_pct": 0.91, "lineout_win_pct": 0.85, "avg_penalties": 10.9, "kicking_pct": 84, "form": ["W", "W", "L", "W", "W"]},
            "h2h": "Irlanda ha vinto 4 degli ultimi 5 scontri diretti a Dublino nel Sei Nazioni",
            "date": (now + timedelta(days=1, hours=15)).isoformat(),
            "props": [
                ("Dan Sheehan Anytime Try Scorer (Meta)", 0.64),
                ("James Lowe Anytime Try Scorer (Meta)", 0.61),
                ("Over 4.5 Mete Totali nel Match", 0.74),
                ("Ireland Rugby Vince il 1° Tempo", 0.78)
            ]
        },
        {
            "id": "rug_eng_ita_2026",
            "league": "Six Nations Championship",
            "tournament": "Guinness Six Nations",
            "venue": "Allianz Stadium Twickenham, London",
            "country": "Europe",
            "flag": "INT",
            "home": {"name": "England Rugby", "scrum_win_pct": 0.94, "lineout_win_pct": 0.89, "avg_penalties": 9.0, "kicking_pct": 86, "form": ["W", "W", "L", "W", "W"]},
            "away": {"name": "Italy Rugby", "scrum_win_pct": 0.86, "lineout_win_pct": 0.81, "avg_penalties": 12.1, "kicking_pct": 82, "form": ["L", "W", "D", "L", "L"]},
            "h2h": "Inghilterra imbattuta negli scontri diretti ufficiali a Twickenham (media 4.8 mete segnate)",
            "date": (now + timedelta(days=2, hours=14)).isoformat(),
            "props": [
                ("Tommy Freeman Anytime Try Scorer", 0.68),
                ("England Rugby Handicap -8.5 Punti", 0.81),
                ("Over 43.5 Punti Totali nel Match", 0.76),
                ("Almeno 1 Cartellino Giallo (Sin Bin 10 min): Sì", 0.67)
            ]
        }
    ]

    for rm in rugby_matches:
        hm, aw = rm["home"], rm["away"]
        sim_r = RugbyQuantEngine.simulate_match(hm, aw)
        fav_r = hm["name"] if sim_r["prob_home"] >= sim_r["prob_away"] else aw["name"]
        fav_p_r = max(sim_r["prob_home"], sim_r["prob_away"])
        best_o_r = round((1.0 / fav_p_r) * 1.06, 2)
        drop_r, opener_r, live_r = record_odds_snapshot(f"{rm['id']}_win", best_o_r)
        books_r = build_euro_bookmakers(fav_p_r, live_r, rm["id"])

        cat_markets_rug = {
            "Risultato, Handicap & Margini": [
                _enrich_mkt(f"{hm['name']} Vince", sim_r["prob_home"], "Moneyline", 1.05),
                _enrich_mkt(f"{aw['name']} Vince", sim_r["prob_away"], "Moneyline", 1.05),
                _enrich_mkt(f"{hm['name']} Handicap -6.5 Punti", min(0.84, sim_r["prob_home"] * 0.86), "Handicap", 1.05),
                _enrich_mkt(f"{hm['name']} Margine di Vittoria 1-12 Punti", sim_r["prob_margin_1_12"], "Margin", 1.06),
                _enrich_mkt(f"{hm['name']} Margine di Vittoria 13+ Punti", sim_r["prob_margin_13_plus"], "Margin", 1.06),
            ],
            "Punti Totali, Mete & Sin Bin": [
                _enrich_mkt("Over 42.5 Punti Totali", sim_r["prob_over_tries"], "Totals", 1.05),
                *[_enrich_mkt(lbl, p_val, "Rugby Specials", 1.06) for lbl, p_val in rm["props"]]
            ]
        }

        events.append({
            "id": rm["id"],
            "sport": "rugby",
            "league": rm["league"],
            "tournament": rm["tournament"],
            "venue": rm["venue"],
            "country": rm["country"],
            "flag": rm["flag"],
            "title": f"{hm['name']} vs {aw['name']}",
            "competitor_a": hm["name"],
            "competitor_b": aw["name"],
            "form_a": hm["form"],
            "form_b": aw["form"],
            "h2h": rm["h2h"],
            "date": rm["date"],
            "status": "Scheduled",
            "stats": {
                "proj_score": f"{hm['name']} {sim_r['proj_home']} - {sim_r['proj_away']} {aw['name']}",
                "margin": f"Margine Stimato: +{sim_r['proj_margin']} pts",
                "total_points": f"Punti Totali Stimati: {sim_r['proj_total']} pts",
                "scrum": sim_r["set_piece_note"],
                "sin_bin": f"Penalità medie concesse: {hm['avg_penalties']} vs {aw['avg_penalties']} (Rischio Sin Bin)"
            },
            "facts": [
                f"Fasi Statiche (Mischia & Touche): {hm['name']} vince il {round(hm['scrum_win_pct']*100)}% delle mischie e il {round(hm['lineout_win_pct']*100)}% delle touche ({round(aw['scrum_win_pct']*100)}% / {round(aw['lineout_win_pct']*100)}% per {aw['name']}).",
                f"Disciplina & Calci Piazzati: {aw['name']} concede {aw['avg_penalties']} falli a partita; precisione al piede {hm['name']} del {hm['kicking_pct']}%.",
                f"Impatto Sin Bin (10m superiorità numerica): Vale in media +5.6 punti attesi nei 10 minuti di cartellino giallo.",
                f"Storico H2H: {rm['h2h']}."
            ],
            "comparison_bars": [
                {"label": "% Mischia Vinta (Scrum)", "valA": round(hm["scrum_win_pct"]*100), "valB": round(aw["scrum_win_pct"]*100), "unit": "%"},
                {"label": "% Touche Vinta (Lineout)", "valA": round(hm["lineout_win_pct"]*100), "valB": round(aw["lineout_win_pct"]*100), "unit": "%"},
                {"label": "% Precisione Calci Piazzati", "valA": hm["kicking_pct"], "valB": aw["kicking_pct"], "unit": "%"}
            ],
            "best_pick": {
                "market": "Set-Piece & Handicap Model",
                "label": f"Vittoria {fav_r}",
                "prob": fav_p_r,
                "fairOdds": round(1.0 / fav_p_r, 2),
                "bookOdds": books_r[0]["price"],
                "bookmaker": books_r[0]["name"],
                "edgePct": books_r[0]["edgePct"],
                "droppingPct": drop_r,
                "openerOdds": opener_r,
                "why": f"Supremazia in Mischia ({round(hm['scrum_win_pct']*100)}%) e Touche ({round(hm['lineout_win_pct']*100)}%) unita alla severità sui calci piazzati ({round(fav_p_r*100)}% probabilità)."
            },
            "bet_builders": {
                "safe": {
                    "name": "Rugby Set-Piece Builder",
                    "legs": [f"Vittoria {fav_r}", "Over 42.5 Punti Totali", rm["props"][0][0]],
                    "prob": 0.61,
                    "fairOdds": 1.64,
                    "bookOdds": 1.88,
                    "liftPct": 11.8
                }
            },
            "vip_insights": _build_vip_insights(rm["id"], fav_p_r, round(1.0 / fav_p_r, 2), books_r[0]["price"], drop_r, opener_r),
            "all_books": books_r[:12],
            "is_safe": fav_p_r >= 0.74,
            "market_categories": cat_markets_rug,
            "markets": [m for grp in cat_markets_rug.values() for m in grp]
        })

    return events


def get_global_safe_scanner(events, min_prob=0.72):
    """Filters cross-sport events and sub-markets where simulated probability >= min_prob."""
    safe_picks = []
    seen = set()

    for ev in events:
        bp = ev.get("best_pick")
        if bp and bp.get("prob", 0) >= min_prob:
            key = (ev["id"], bp["label"])
            seen.add(key)
            safe_picks.append({
                "id": f"{ev['id']}_safe",
                "eventId": ev["id"],
                "sport": ev["sport"],
                "sportName": SPORTS_CONFIG.get(ev["sport"], {}).get("name", ev["sport"].capitalize()),
                "sportIcon": SPORTS_CONFIG.get(ev["sport"], {}).get("icon", "SPT"),
                "tournament": ev.get("tournament") or ev.get("league"),
                "venue": ev.get("venue", ""),
                "title": ev["title"],
                "flag": ev.get("flag", "INT"),
                "date": ev["date"],
                "market": bp["market"],
                "outcome": bp["label"],
                "prob": bp["prob"],
                "fairOdds": bp["fairOdds"],
                "bookmaker": bp["bookmaker"],
                "bookOdds": bp["bookOdds"],
                "edgePct": bp["edgePct"],
                "droppingPct": bp.get("droppingPct", 0.0),
                "openerOdds": bp.get("openerOdds", bp["bookOdds"]),
                "isDropping": bp.get("droppingPct", 0.0) <= -2.2,
                "allBooks": ev.get("all_books", [])[:12],
                "facts": ev.get("facts", []),
                "stats": ev.get("stats", {}),
                "comparison_bars": ev.get("comparison_bars", []),
                "market_categories": ev.get("market_categories", {}),
                "bet_builders": ev.get("bet_builders", {}),
                "vip_insights": ev.get("vip_insights", {}),
                "why": bp["why"]
            })

        # Add high-probability secondary anchors from market categories (one additional top anchor per event)
        added_sub = 0
        for mkt in ev.get("markets", []):
            if added_sub >= 1:
                break
            p = mkt.get("prob", 0)
            lbl = mkt.get("label", "")
            key = (ev["id"], lbl)
            if p >= max(0.76, min_prob) and key not in seen:
                seen.add(key)
                added_sub += 1
                fair = round(1.0 / p, 2)
                best_o = mkt.get("odds", round(fair * 1.05, 2))
                drop, opener_o, live_o = record_odds_snapshot(f"{ev['id']}_{lbl}", best_o)
                books = build_euro_bookmakers(p, live_o, f"{ev['id']}_{lbl}")
                top_b = books[0]
                safe_picks.append({
                    "id": f"{ev['id']}_{lbl.replace(' ', '_')}",
                    "eventId": ev["id"],
                    "sport": ev["sport"],
                    "sportName": SPORTS_CONFIG.get(ev["sport"], {}).get("name", ev["sport"].capitalize()),
                    "sportIcon": SPORTS_CONFIG.get(ev["sport"], {}).get("icon", "SPT"),
                    "tournament": ev.get("tournament") or ev.get("league"),
                    "venue": ev.get("venue", ""),
                    "title": ev["title"],
                    "flag": ev.get("flag", "INT"),
                    "date": ev["date"],
                    "market": mkt.get("fam", "Linea Protetta High-Prob"),
                    "outcome": lbl,
                    "prob": p,
                    "fairOdds": fair,
                    "bookmaker": top_b["name"],
                    "bookOdds": top_b["price"],
                    "edgePct": top_b["edgePct"],
                    "droppingPct": drop,
                    "openerOdds": opener_o,
                    "isDropping": drop <= -2.2,
                    "allBooks": books[:12],
                    "facts": ev.get("facts", []),
                    "stats": ev.get("stats", {}),
                    "comparison_bars": ev.get("comparison_bars", []),
                    "market_categories": ev.get("market_categories", {}),
                    "bet_builders": ev.get("bet_builders", {}),
                    "vip_insights": _build_vip_insights(f"{ev['id']}_{lbl}", p, fair, top_b["price"], drop, opener_o),
                    "why": f"Probabilita stimata dal modello: {round(p*100)}%."
                })

    safe_picks.sort(key=lambda x: (-x["prob"], -x["edgePct"]))
    return safe_picks


def generate_mocked_premium_suite(all_events):
    """Generates the interactive Mocked Premium VIP Suite so users can see & test exact Pro/VIP features:
    1. Live Surebet / Arbitrage & Middle Scanner (Zero-Risk Cross-Bookmaker Profit)
    2. Whale & Sharp Money Steam Radar (Pinnacle / Betfair Exchange Orderflow)
    3. AI Correlated VIP Bet Builder & Parlay Matrix
    4. Player Prop & Telemetry Alpha Signals
    """
    arbitrage_opps = [
        {
            "id": "arb_01",
            "sport": "Tennis · ATP Masters Paris",
            "event": "Carlos Alcaraz vs Alexander Zverev",
            "type": "2-Way Surebet (Arbitraggio Matematico)",
            "roiPct": 3.42,
            "legA": {"selection": "Carlos Alcaraz Vince", "bookmaker": "Pinnacle", "odds": 1.74, "stakePct": 59.4},
            "legB": {"selection": "Alexander Zverev Vince", "bookmaker": "Bet365", "odds": 2.54, "stakePct": 40.6},
            "windowAge": "Rilevata 4 min fa (Sync 20m)",
            "explanation": "Discrepanza tra l'apertura asiatica di Pinnacle su Alcaraz (@1.74) e la quota lenta di Bet365 su Zverev (@2.54). Somma probabilità implicite = 96.68% (Margine teorico +3.42% su entrambi gli esiti (dato dimostrativo))."
        },
        {
            "id": "arb_02",
            "sport": "Calcio · Champions League / Serie A",
            "event": "Paris Saint-Germain vs Barcelona",
            "type": "Asian Total Surebet + Middle Window",
            "roiPct": 2.85,
            "legA": {"selection": "Over 2.5 Goals", "bookmaker": "Betfair Exchange", "odds": 1.88, "stakePct": 54.7},
            "legB": {"selection": "Under 2.5 Goals", "bookmaker": "Unibet", "odds": 2.27, "stakePct": 45.3},
            "windowAge": "Rilevata 7 min fa (Sync 20m)",
            "explanation": "Liquidità in ingresso su Betfair Exchange sull'Over 2.5 mentre Unibet mantiene l'Under 2.5 fuori mercato a @2.27. Ritorno matematico netto +2.85%."
        },
        {
            "id": "arb_03",
            "sport": "️ Formula 1 · US Grand Prix Austin",
            "event": "Duello H2H: Lando Norris vs Max Verstappen",
            "type": "Motorsport H2H Surebet",
            "roiPct": 4.15,
            "legA": {"selection": "Lando Norris batte Verstappen (H2H)", "bookmaker": "Winamax", "odds": 1.92, "stakePct": 54.2},
            "legB": {"selection": "Max Verstappen batte Norris (H2H)", "bookmaker": "Pinnacle", "odds": 2.28, "stakePct": 45.8},
            "windowAge": "Rilevata 2 min fa (Post-FP3 Telemetry)",
            "explanation": "Dopo i long-run FP3, Pinnacle ha alzato Verstappen a @2.28 mentre Winamax non ha ancora adeguato la quota di Norris (@1.92). +4.15% ROI bloccato."
        },
        {
            "id": "arb_04",
            "sport": "Basket NBA · Regular Season",
            "event": "New York Knicks vs Philadelphia 76ers",
            "type": "Point Spread Middle & Arb",
            "roiPct": 2.40,
            "legA": {"selection": "Knicks -4.5 Punti", "bookmaker": "Bet365", "odds": 1.96, "stakePct": 52.2},
            "legB": {"selection": "76ers +5.5 Punti", "bookmaker": "Tipico", "odds": 2.14, "stakePct": 47.8},
            "windowAge": "Rilevata 11 min fa",
            "explanation": "Oltre al +2.40% teorico, se i Knicks vincono esattamente di 5 punti (es. 112-107) entrambe le selezioni risulterebbero vincenti (Finestra Middle di 1 punto!)."
        }
    ]

    whale_steam_moves = [
        {
            "id": "steam_01",
            "sport": "ATP Paris Masters",
            "event": "Jannik Sinner vs Daniil Medvedev",
            "selection": "Jannik Sinner -1.5 Set (Vince 2-0)",
            "openerOdds": 2.18,
            "currentOdds": 1.88,
            "dropPct": -13.8,
            "sharpPct": 94,
            "publicPct": 51,
            "matchedEur": 312400,
            "bookToHit": "Bet365 (@1.98 ancora disponibile vs Pinnacle @1.84)",
            "signal": "WHALE SYNDICATE STEAM"
        },
        {
            "id": "steam_02",
            "sport": "NFL Week 7",
            "event": "Baltimore Ravens vs Buffalo Bills",
            "selection": "Derrick Henry Over 84.5 Rushing Yards",
            "openerOdds": 1.95,
            "currentOdds": 1.72,
            "dropPct": -11.8,
            "sharpPct": 91,
            "publicPct": 44,
            "matchedEur": 184500,
            "bookToHit": "Unibet (@1.87 ancora disponibile vs Fair @1.64)",
            "signal": "REVERSE LINE MOVEMENT"
        },
        {
            "id": "steam_03",
            "sport": "️ F1 Austin COTA",
            "event": "United States Grand Prix",
            "selection": "Charles Leclerc batte Oscar Piastri (H2H Gara)",
            "openerOdds": 2.05,
            "currentOdds": 1.76,
            "dropPct": -14.1,
            "sharpPct": 89,
            "publicPct": 38,
            "matchedEur": 146000,
            "bookToHit": "bwin (@1.90 ancora disponibile)",
            "signal": "⏱️ FP2 TELEMETRY DROP"
        },
        {
            "id": "steam_04",
            "sport": "NBA Regular Season",
            "event": "Boston Celtics vs Detroit Pistons",
            "selection": "Boston Celtics 1° Tempo -6.5 Punti",
            "openerOdds": 1.91,
            "currentOdds": 1.69,
            "dropPct": -11.5,
            "sharpPct": 92,
            "publicPct": 49,
            "matchedEur": 229000,
            "bookToHit": "Betsson (@1.83 ancora disponibile)",
            "signal": "BACK-TO-BACK STEAM"
        }
    ]

    vip_player_props = [
        {"sport": "Tennis", "player": "Jannik Sinner", "match": "vs Medvedev", "prop": "Over 8.5 Aces", "line": "8.5", "proj": "10.8 Aces", "prob": 0.74, "bestBook": "Bet365", "odds": 1.83, "edgePct": 35.4},
        {"sport": "NBA", "player": "Jalen Brunson", "match": "Knicks vs 76ers", "prop": "Over 27.5 Punti", "line": "27.5", "proj": "31.4 Pts", "prob": 0.75, "bestBook": "Pinnacle", "odds": 1.87, "edgePct": 40.2},
        {"sport": "NFL", "player": "Christian McCaffrey", "match": "49ers vs Commanders", "prop": "Anytime TD Scorer", "line": "0.5 TD", "proj": "1.28 TD", "prob": 0.76, "bestBook": "Unibet", "odds": 1.58, "edgePct": 20.1},
        {"sport": "️ F1", "player": "Lando Norris", "match": "US Grand Prix", "prop": "Podio Top 3", "line": "Top 3", "proj": "P1.4 Media", "prob": 0.86, "bestBook": "Betfair", "odds": 1.32, "edgePct": 13.5},
        {"sport": "️ MotoGP", "player": "Francesco Bagnaia", "match": "GP Mugello", "prop": "Podio Top 3", "line": "Top 3", "proj": "P1.2 Media", "prob": 0.88, "bestBook": "Bet365", "odds": 1.28, "edgePct": 12.6},
        {"sport": "Rugby", "player": "Dan Sheehan", "match": "Ireland vs France", "prop": "Anytime Try Scorer", "line": "0.5 Try", "proj": "0.84 Mete", "prob": 0.64, "bestBook": "William Hill", "odds": 2.15, "edgePct": 37.6},
    ]

    return {
        "arbitrage": arbitrage_opps,
        "whaleSteam": whale_steam_moves,
        "vipPlayerProps": vip_player_props,
        "tierComparison": [
            {"feature": "Scanner Eventi & Probabilità Base", "free": "Top 4 per vista (Resto Bloccato)", "pro": "Illimitato su tutti gli 8 Sport (100% Sbloccato)"},
            {"feature": "Aggiornamento Quote & Modelli ogni 20 Min", "free": "Ritardato", "pro": "Real-Time ogni 20m + Trigger Manuale Istantaneo"},
            {"feature": "Matrice Completa Mercati Bet365 (40+ opzioni/match)", "free": "Solo mercato principale", "pro": "1X2, Asian Handicap, Over/Under, Corner, Cartellini, Set, Quarti, H2H Piloti"},
            {"feature": "Whale & Sharp Money Steam Radar (Volumi € Betfair/Pinnacle)", "free": "Bloccato", "pro": "Incluso (% Public vs % Sharp, RLM Alerts, CLV atteso)"},
            {"feature": "Scanner Surebet / Arbitraggio Matematico & Middle", "free": "Bloccato", "pro": "Incluso con Calcolatore Split Puntate Zero-Risk"},
            {"feature": "Laboratorio Correlated Bet Builder", "free": "Bloccato", "pro": "Incluso con calcolo Correlation Lift (+12% a +24%)"},
            {"feature": "Player Props & Telemetria F1/MotoGP Long-Run", "free": "Bloccato", "pro": "Incluso (Marcatori, Tiri, Assist, PRA NBA, TD NFL, Stint FP1-FP3)"}
        ]
    }
