# EdgeBet AI API v1 (contract)

All responses are JSON (UTF-8). Errors are always `{"error": "<human message>", "code": "<machine_code>"}` with a proper HTTP status.
Auth is a cookie session (`eb_session`, HttpOnly, SameSite=Lax). The effective **tier** (`free | pro | vip`) is decided **server side** from the session entitlement,
or, only when the server runs with demo mode on (`demoMode: true`), from the `eb_demo_tier` cookie set by `POST /api/v1/demo/tier`.
The client can never choose its tier with a query parameter. Locked data is **not sent** (redaction is server side).

Legacy endpoints (`/api/multisport`, `/api/value-bets`, ...) keep working; the web app uses only `/api/v1/*`.

## Conventions
- `prob`: probability 0..1. `fairOdds`: decimal, `1/prob`. Odds are decimal.
- `kickoff`, `updated`, `nextSync`: ISO 8601 UTC.
- `country`: ISO-3166 alpha-2 (`IT`, `GB`, `ES`, `DE`, `FR`, `NL`, `PT`, `US`, `AT`, `CH`, `TR`, `MX`, `SA`...) or `EU` (Europe) or `INT` (international / no country). Render a flag SVG from this code, no emoji.
- `priceSource`: `live` (fetched from a real odds feed, timestamped) or `modeled` (derived from the model, NOT a real market price). `edgePct`, `movementPct`, `bestOdds`, `bestBook` are `null` unless `priceSource == "live"`.
- `dataStatus`: `validated` (football: 20k-run Dixon-Coles with an out-of-sample backtest) or `demo` (sample fixtures + closed-form model, no backtest). Demo rows MUST be visibly badged "Dati dimostrativi".
- `confidence`: `molto_alta` (prob >= 0.85), `alta` (>= 0.74), `media` (otherwise). Never use words like "sicura", "garantita", "lock".

## GET /api/v1/feed
```json
{
  "meta": {"updated": "...", "nextSync": "...", "syncCycle": 3, "tier": "free", "demoMode": true,
           "priceSource": "modeled", "liveBooks": [], "currency": "EUR", "loading": false},
  "sports": [{"id": "football", "name": "Calcio", "eventCount": 28, "hotCount": 9,
              "dataStatus": "validated", "description": "..."}],
  "finding": {"text": "Oggi 9 selezioni con probabilita >= 74%, 3 su prezzi live.", "hot": 9, "live": 3},
  "oggi": ["fb_123", "fb_456", "fb_789"],
  "rows": [{
    "id": "fb_123", "rank": 1, "sport": "football", "title": "Inter vs Milan",
    "competitors": ["Inter", "Milan"], "competition": "Serie A", "country": "IT",
    "kickoff": "...", "venue": "San Siro", "dataStatus": "validated", "thin": false,
    "form": {"a": ["W","W","D","L","W"], "b": ["L","W","W","D","D"]},
    "locked": false,
    "pick": {"label": "Over 1.5 goals", "market": "Goals", "prob": 0.86, "fairOdds": 1.16,
             "confidence": "molto_alta", "priceSource": "modeled",
             "bestOdds": null, "bestBook": null, "edgePct": null, "movementPct": null}
  }]
}
```
- `rows` are sorted by `rank` (validated + probability + live edge). `oggi` = ids of the top 3 rows (validated first).
- Free tier: a row is unlocked if `rank <= 4` or it is the top-ranked row of its sport. Locked rows keep `title`, `competition`, `kickoff`, `prob`, `confidence`, but
  `pick.label`, `pick.market`, `pick.fairOdds`, `pick.bestOdds`, `pick.bestBook`, `pick.edgePct` are `null` and `locked` is `true`.
- While the first football analysis is still running `meta.loading` is `true` (show skeletons / "Aggiornamento in corso", never a bare zero).

## GET /api/v1/detail/<id>
`403 {"code": "upgrade_required"}` for locked rows. `404 {"code": "not_found"}` otherwise unknown.
```json
{
  "id": "fb_123", "tier": "free",
  "tabs": {
    "prezzi": {
      "priceSource": "modeled", "asOf": "...", "fairOdds": 1.16,
      "note": "Prezzi non live: quota equa del modello. Collega un feed quote per il confronto reale.",
      "ladder": {"fair": 1.16, "min": 1.08, "max": 1.22},
      "books": [{"name": "Pinnacle", "region": "Global Sharp", "price": 1.20, "vigPct": 1.9,
                 "noVigProb": 0.84, "edgePct": null, "movement": null,
                 "source": "modeled", "maxStakeEur": null}]
    },
    "perche": {
      "why": ["...", "..."],
      "stats": [{"label": "Expected goals (xG)", "value": "Inter 1.62 - 1.05 Milan"}],
      "bars": [{"label": "Tiri in porta", "valA": 5.1, "valB": 3.2, "unit": ""}],
      "facts": ["..."],
      "model": {"name": "Dixon-Coles 20.000 simulazioni", "validated": true, "samples": [12, 12], "thin": false}
    },
    "mercati": {
      "categories": [{"name": "Gol", "items": [{"label": "Over 2.5 goals", "prob": 0.58, "fair": 1.72, "odds": null}]}],
      "builders": [{"name": "Bet Builder prudente", "legs": ["..."], "prob": 0.52, "fairOdds": 1.92, "liftPct": 11.8}]
    },
    "sharp": {"available": false, "metrics": [], "note": "Richiede quote live da Pinnacle / Betfair."}
  }
}
```
- `books[].source` is `live` or `modeled`. Modeled rows must be labelled "Stima" in the UI; edge is always `null` for them.
- Free tier (unlocked row): `sharp` -> `{"locked": true}` and `mercati.builders` -> `{"locked": true}`; `books` limited to the best 3.
- `mercati.items[].label` for football are the model's labels and can be fed to the existing `GET /api/custom-builder?id=<eventId>&legs=a||b` (Pro/VIP only).

## Auth, tier, demo
- `GET /api/v1/me` -> `{"user": null | {"email": "...", "guest": false, "tier": "free", "status": "active", "expiresAt": null, "source": "demo|stripe|apple|google|none"}, "tier": "free", "demoMode": true}`
- `POST /api/v1/auth/register` `{email, password}` (password >= 8) -> `{"user": {...}}` + session cookie. `409 email_taken`, `400 invalid_input`.
- `POST /api/v1/auth/login` `{email, password}` -> `{"user": {...}}`. `401 invalid_credentials`.
- `POST /api/v1/auth/guest` (demo mode only) -> creates an anonymous guest user + session. `403 demo_disabled` otherwise.
- `POST /api/v1/auth/logout` -> `{"ok": true}`.
- `POST /api/v1/demo/tier` `{"tier": "free|pro|vip"}` (demo mode only) -> `{"tier": "pro"}`. `403 demo_disabled`.
- `POST /api/v1/billing/checkout` `{"plan": "pro_monthly|pro_annual|vip_monthly|vip_annual"}` -> `{"url": "https://checkout.stripe.com/..."}`; `501 billing_not_configured` when Stripe keys are not set (UI then offers the demo switch if `demoMode`); `401 auth_required`.
- `POST /api/v1/billing/webhook` Stripe webhook (signature verified server side).

## My bets (auth required, `401 auth_required`)
- `GET /api/v1/bets` -> `{"bets": [Bet], "stats": {"count": 12, "open": 3, "staked": 120.0, "returned": 131.4, "profit": 11.4, "roiPct": 9.5, "hitRatePct": 58.3}, "limit": 10, "tier": "free"}`
- `POST /api/v1/bets` `{"title", "pick", "odds", "stake", "currency", "sport", "pickId"?}` -> `{"bet": Bet}`. Free tier is limited to 10 bets in total: `402 {"code": "limit_reached"}`.
- `PATCH /api/v1/bets/<id>` `{"result": "won|lost|void|open"}` -> `{"bet": Bet, "stats": {...}}`
- `DELETE /api/v1/bets/<id>` -> `{"ok": true, "stats": {...}}`
- `Bet` = `{"id", "createdAt", "title", "pick", "odds", "stake", "currency", "sport", "result": "open|won|lost|void", "profit": 0.0}`

## Proof (public)
- `GET /api/v1/ledger` -> picks recorded **before kickoff**, graded automatically after the match (football only):
  `{"summary": {"settled": 40, "pending": 22, "hitRatePct": 74.5, "avgProbPct": 73.1, "brier": 0.171, "logLoss": 0.52, "since": "2026-10-01"},
    "calibration": [{"bin": "70-80%", "n": 18, "predictedPct": 74.2, "actualPct": 77.8}],
    "rows": [{"id": "...", "publishedAt": "...", "kickoff": "...", "title": "...", "pick": "...", "prob": 0.78, "fairOdds": 1.28, "status": "pending|won|lost|void", "result": "2-1"}],
    "basis": "Probabilita registrate prima del calcio d'inizio; nessun ROI senza quote storiche reali."}`
- `GET /api/v1/backtest` -> walk-forward out-of-sample over cached completed matches (football):
  `{"n": 435, "hitRatePct": 80.9, "avgProbPct": 73.4, "brier": 0.157, "logLoss": 0.47, "calibration": [...same shape...], "byMarket": [{"market": "Goals", "n": 90, "hitRatePct": 78.9, "avgProbPct": 72.0}], "note": "..."}`
  (No ROI: ROI needs real historical bookmaker prices.)
- `GET /api/v1/method` -> `{"sports": [{"id", "name", "dataStatus", "model", "sources": ["..."], "validation": "..."}], "priceFeed": {"configured": false, "provider": "The Odds API", "books": []}, "disclaimers": ["..."], "responsibleGambling": [{"label": "Gioco Responsabile (IT)", "url": "..."}]}`

## Premium sandbox
`GET /api/v1/premium` -> free: `{"locked": true, "demo": true, "teaser": {"arbitrage": 4, "flows": 4, "props": 6}}`; pro/vip: `{"demo": true, "arbitrage": [...], "flows": [...], "props": [...]}`.
All content is simulated and MUST be labelled "Dati dimostrativi" in the UI. Fields mirror the legacy `/api/premium-suite` (`arbitrage`, `whaleSteam` -> `flows`, `vipPlayerProps` -> `props`).
