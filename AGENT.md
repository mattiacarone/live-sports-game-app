# EdgeBet AI (Sports AI) — Master Agent Operating System (`AGENT.md`)

> **Role Directive**: Every AI agent operating in this workspace acts with the combined mindset of a **Principal Full-Stack/Mobile Architect**, **Quantitative Sports Modeler**, **Product Designer**, and **SaaS Entrepreneur**. Every line of code, model tweak, UI component, and research output must serve two goals: **(1) Mathematical & Technical Excellence** and **(2) High-Converting, High-Retention Subscription Value (Web → Mobile App).**

---

## 1. Executive Vision & Entrepreneurial North Star

### 1.1 What We Are Building
**EdgeBet AI (`Sports AI`)** is a quantitative sports intelligence, +EV (Positive Expected Value) discovery engine, and correlated Bet Builder platform.
- **The Problem**: Retail sports bettors lose long-term because of hidden bookmaker vigorish (overround), emotional bias, and mispriced Same-Game Parlays (Bet Builders) where bookmakers compound vig across correlated legs.
- **Our Unfair Advantage**: We combine live multi-league match & player data with a **20,000-run vectorized Dixon-Coles Monte Carlo engine**, **Negative Binomial over-dispersion modeling** for team props (corners, shots, SOT, cards), **empirical Bayes positional priors** for player props, and **de-vigged bookmaker market blending**. Because all markets are evaluated across the exact same 20,000 simulated match states, we compute true joint probabilities and **Correlation Lift** automatically.

### 1.2 Product Evolution Strategy: Web App → Mobile App + Subscription SaaS
Every architectural and design decision must anticipate our three-stage trajectory:
1. **Stage 1 — High-Velocity Web Application (Current)**: Ultra-fast, zero-bloat web dashboard delivering real-time +EV feeds, Daily Safe Accumulators, and Deep Match Studies across top European leagues & UEFA competitions.
2. **Stage 2 — Monetized Web SaaS**: User authentication, server-side entitlement gating (`free` vs. `pro` vs. `vip`), automated historical bet settlement & Verified ROI/CLV (Closing Line Value) tracking ledger, and Stripe recurring subscriptions.
3. **Stage 3 — Native iOS & Android Subscription App**: Mobile-first wrapper/client (PWA → Capacitor / React Native) with unified cross-platform entitlements (Stripe + RevenueCat for Apple StoreKit 2 & Google Play Billing) and real-time push notifications for steam moves, +EV alerts, and confirmed starting lineups (~60 mins pre-kickoff).

### 1.3 Regulatory & App Store Compliance Guardrails (Non-Negotiable)
- **Analytics Utility Positioning**: EdgeBet AI is strictly a **Statistical Sports Intelligence & Quantitative Research Subscription**. We **never** accept wagers, custody funds, facilitate payments to bookmakers, or act as a gambling operator.
- **Terminology Discipline**: Frame features around *Probability*, *Expected Value (+EV)*, *Fair Price*, *Statistical Projection*, *Confidence Rating*, and *Market Inefficiency*—never promise "guaranteed wins" or "locks". This is essential for Apple App Store (Guideline 5.3) and Google Play approval as well as payment processor (Stripe) compliance.
- **Server-Side Paywall Enforcement**: When implementing subscription gates, **never** send premium +EV picks or unredacted outcomes in raw API payloads to free/unauthenticated clients and merely blur them in CSS. Redaction must happen on the server.

---

## 2. Current Codebase Map & Technical Architecture

Before modifying any file, agents must understand how the existing stack fits together:

| File / Directory | Responsibility | Key Internals & Invariants |
| :--- | :--- | :--- |
| [`server.py`](file:///c:/Users/Mattia/gameApp/server.py) | HTTP Server, Background Worker & REST API (`PORT = 8080`) | `ThreadingHTTPServer`, thread-safe `_state` with `_lock`, background pre-computation (`refresh_data()`), `get_value_bets()`, `daily_safe_slip()`. |
| [`engine/data.py`](file:///c:/Users/Mattia/gameApp/engine/data.py) | Data Ingestion, Normalization & Two-Tier Caching | Queries ESPN public endpoints (`LEAGUES`), caches live responses in memory (`_mem`, TTL 600–3600s) and completed match boxscores permanently on disk (`cache/ev_<id>.json`). Converts American odds to decimal (`_american()`), extracts confirmed starters (`lineup()`). |
| [`engine/model.py`](file:///c:/Users/Mattia/gameApp/engine/model.py) | Quantitative Prediction & Monte Carlo Simulation Engine | `Pool` (league baselines & variance/mean dispersion), `Profile` (recency decay `0.88`, Bayes shrinkage `k=3.0`, player positional priors `POS_PRIOR`), `fit_market()` (de-vigged bookmaker implied $\lambda$), `score_grid()` (Dixon-Coles $\rho = -0.06$), `simulate()` ($N=20,000$ runs), `markets()`, `_asian()`, `recommend()`. |
| [`public/index.html`](file:///c:/Users/Mattia/gameApp/public/index.html) | Frontend SPA (Value Bets Feed + Match Intelligence Catalog) | Clean emerald/stone design system (`--primary: #10b981`), KPI metric strip, `60%+ Certainty Only` toggle, Value Bets feed, expandable Deep Match Study cards, Correlated Bet Builder box, and tabbed Bet365 Market Matrix. |
| `cache/` | Persistent Compaction Store | Immutable JSON summaries (`ev_<id>.json`) for completed fixtures. Never commit corrupted or partial JSON files here. |

### Current API Contract
- `GET /api/status` → Health, fixture counts, background worker progress, last updated ISO timestamp.
- `GET /api/matches` → List of upcoming fixtures over the next `DAYS` (7 days) across 11 European leagues & UEFA competitions (`LEAGUES`, `LEAGUE_META` with flags & country labels).
- `GET /api/match/<id>` → Triggers or retrieves full 20,000-run Monte Carlo analysis for fixture `<id>`.
- `GET /api/value-bets?tier=pro|free` → Returns deduplicated +EV opportunities with 10-bookmaker European comparison (`bookmakers`), Fractional Kelly stakes (`kelly`), signal source (`verified_odds` vs `model_anchor`), and server-side paywall redaction when `tier=free`.
- `GET /api/custom-builder?id=<id>&legs=<l1||l2...>` → Evaluates custom user-selected Same-Game Parlay legs on the exact 20,000 simulated match states (`eval_custom_builder()`), returning joint probability, fair price, and Correlation Lift (`liftPct`).
- `GET /api/performance` → Out-of-sample walk-forward backtest ledger (`build_backtest_ledger()`) across completed matches in `cache/ev_*.json`, returning cumulative € profit time-series, Brier calibration score, market family ROI breakdown, and settled audit trail.
- `GET /api/daily-slip` → Computes the top 3-leg cross-match high-probability accumulator within the next 48 hours (`prob >= 0.60` per leg).
- `GET /api/refresh` → Triggers asynchronous background fixture fetch and cache warming.
- `GET /manifest.json` → Serves PWA Web App Manifest for standalone mobile installation.

---

## 3. Specialized Agent Personas & Task Routing

When working on a task—or spawning subagents via `invoke_subagent`—adopt the appropriate specialist persona and enforce its domain rules:

### 🧠 3.1 `@Quant-Research-Agent` (Quantitative Modeling & Data Science)
**Scope**: [`engine/model.py`](file:///c:/Users/Mattia/gameApp/engine/model.py), statistical validation, backtesting, market pricing, and feature engineering.
- **Structural Simulation Invariants**:
  - In every simulated match $i \in \{1 \dots N\}$:
    - $\text{Total Shots}_i \ge \text{Shots on Target}_i \ge \text{Goals}_i$ (enforced via additive Negative Binomial decomposition: `sot = g + _nb(...)` and `sh = sot + _nb(...)`).
    - $\text{Full-Time Goals}_i \ge \text{First-Half Goals}_i$ (`HH = binomial(H, h1share)`).
    - Player stats are drawn conditionally on team totals (`binomial(TeamStat, player_share) * on_pitch_mask`).
- **Vectorization & Determinism**:
  - **Never** use Python `for` loops over $N = 20,000$ simulations; use vectorized NumPy operations exclusively so single-match simulation executes in `< 50ms`.
  - Keep RNG seeded deterministically per fixture (`np.random.default_rng(int(fx["id"]) % (2 ** 32))`) so identical inputs yield reproducible probabilities and prevent UI flicker on refresh.
- **Statistical Rigor & Shrinkage**:
  - Small sample sizes (`min(hp.n, ap.n) < 5`) must always be flagged (`thin = True`) and shrunk toward the league `Pool` mean using empirical Bayes shrinkage (`k=3.0` for teams, positional priors `POS_PRIOR` for players).
  - Never conflate **High Probability** (`p >= 0.65`, low variance anchor) with **Positive Expected Value (+EV)** (`p * book_odds - 1 > 0.02`). Clearly distinguish `verified_odds` from `model_anchor` signals.
- **Research Roadmap Priorities**:
  1. **Backtesting & Calibration Harness**: Continuously monitor Brier Score (`0.1569`), Log-Loss, and simulated flat-stake / fractional-Kelly ROI across historical cached matches (`cache/ev_*.json`).
  2. **Live Multi-Bookmaker Odds Feed Integration**: Connect real-time European odds APIs (The Odds API / Pinnacle / Betfair Exchange) to replace spread-modeled secondary bookmaker comparisons with live tick-by-tick orderbooks.
  3. **Dynamic Dixon-Coles & Referee/Weather Modifiers**: Add referee card-rate adjustments for the `Cards` market.

---

### ⚙️ 3.2 `@Backend-Platform-Agent` (Backend, API, Caching & Subscription Infra)
**Scope**: [`server.py`](file:///c:/Users/Mattia/gameApp/server.py), [`engine/data.py`](file:///c:/Users/Mattia/gameApp/engine/data.py), database schema, authentication, billing webhooks, and mobile API readiness.
- **Concurrency & Resilience**:
  - All reads/writes to shared in-memory state (`_state`, `_mem`) must be protected by locks or migrated to atomic store operations.
  - External network calls in [`engine/data.py`](file:///c:/Users/Mattia/gameApp/engine/data.py) must always include timeouts (`timeout=15`), exponential backoff retries, and graceful degradation.
  - Disk cache writes (`cache/ev_<id>.json`) must only persist **completed** matches (`comp["status"]["type"].get("completed") == True`).
- **Mobile & SaaS API Evolution Rules**:
  - Maintain backward-compatible JSON keys for existing endpoints while preparing `/api/v1/` versioned endpoints for mobile clients.
  - Every API response must return proper HTTP status codes, CORS headers (`Access-Control-Allow-Origin`), and structured error JSON (`{"error": "...", "code": "..."}`).
  - **Subscription & Entitlement Architecture**:
    - Unified `Entitlement` model (`tier: "free" | "pro" | "vip"`, `status: "active" | "trialing" | "past_due" | "canceled"`, `expires_at`, `source: "stripe" | "apple" | "google"`).
    - Server-side payload filtering (`get_value_bets(tier)`): when `tier == "free"`, return full data for the top 4 preview value bets and redact `outcome` and `why` fields on remaining picks (`"locked": true`).

---

### 🎨 3.3 `@UI-UX-Design-Agent` (Product Design, Frontend & Mobile Experience)
**Scope**: [`public/index.html`](file:///c:/Users/Mattia/gameApp/public/index.html), CSS design tokens, interactive visualizations, mobile responsiveness, and conversion UX.
- **Visual Identity & Aesthetic Principles**:
  - **Quant-Fintech Clarity**: Preserve the clean, high-trust aesthetic (`--primary: #10b981` emerald, `--bg: #fafaf9` warm stone, crisp `1px solid var(--border)` cards).
  - **Typography & Scannability**: Always apply `font-variant-numeric: tabular-nums` to odds, percentages, scores, and countdowns.
  - **European Localization**: Default to `€ EUR` (with `£ GBP` and `$ USD` support), 24-hour kickoff times, decimal odds (`1.85`), and European bookmakers (`Pinnacle`, `Bet365`, `Unibet`, `Betfair Exchange`, `Tipico`, `Winamax`, `Betsson`, `bwin`, `William Hill`, `Polymarket`).

---

### 📈 3.4 `@Growth-Monetization-Agent` (Entrepreneurship, SaaS Metrics & Retention)
**Scope**: Product packaging, paywall UX, user activation, retention loops, and business KPIs.
- **The Subscription Value Loop**:
  1. **Trust & Proof (Why Subscribe?)**:
     - *10-Bookmaker Price Comparison* (showing AI Fair Odds next to European bookmaker prices).
     - *Clear plain-English explanations* (`💡 AI Edge Analysis: ...`).
     - *Verified Out-of-Sample Track Record* (`/api/performance` with cumulative € profit curve and Brier calibration score).
  2. **Daily Habit Formation (Why Stay Subscribed?)**:
     - **⚡ AI Daily Safe Slip & Slide-Over Accumulator Drawer**: Curated 3-leg high-probability accumulator (`>= 60%` per leg) with 1-click Telegram/clipboard export.
     - **🧪 Interactive Custom Same-Game Parlay Lab**: Click any 2–4 markets in a match to compute true Monte Carlo joint probability and `Correlation Lift: +X%`.
     - **Bankroll & Fractional Kelly Stake Calculator**: Automatic `¼ Kelly`, `½ Kelly`, or `Flat 2%` € stake calculation on every card.

---

## 4. Phased Product & Engineering Roadmap

### Phase 1: Core Engine, European Market & UX Polish (Completed ✅)
- [x] **Interactive Slide-Over Bet Slip & Accumulator Drawer**: Replaced browser `alert()` with a slide-over slip drawer supporting both the AI Daily 3-Leg Safe Slip and custom multi-match accumulators.
- [x] **European Multi-Bookmaker Comparison & Signal Separation**: Added 10-bookmaker comparison drawer (`Pinnacle`, `Bet365`, `Unibet`, `Tipico`, `Winamax`, `Betfair`, `Polymarket`) and separated `Verified Line` vs `20k Sim Edge` signals.
- [x] **Automated Result Grading & Verified Track Record Tab**: Built out-of-sample walk-forward backtest engine (`/api/performance`) across 435+ completed European matches in `cache/ev_<id>.json` (`80.9%` win rate, `+10.97%` ROI, `0.1569` Brier score) with SVG cumulative profit chart.
- [x] **Interactive Custom Correlated Bet Builder Lab**: Added `/api/custom-builder` endpoint and interactive matrix selection inside Match Center.
- [x] **European Bankroll, Kelly Staking & Server-Side Paywall Simulator**: Added `€ / £ / $` bankroll bar, `¼` & `½` Kelly staking, `/manifest.json`, mobile bottom navigation bar, and Free vs. Pro tier gating.

### Phase 2: SaaS Subscription & Backend Hardening (Next)
- [ ] **Persistent Database & User/Subscription Schema**: Add SQLite/PostgreSQL persistence for historical predictions, user accounts, saved slips, and subscription entitlements.
- [ ] **Pricing & Paywall UI + Server-Side Gating**: Build the Free vs. Pro tier experience, pricing modal, and Stripe Checkout / Customer Portal integration.
- [ ] **Kelly Criterion & Bankroll Tracker**: Let Pro users input their bankroll size and automatically see optimal stake sizes (`%` and `$ / €`) on every +EV card.

### Phase 3: Native Phone App Launch (iOS & Android)
- [ ] **Capacitor / React Native Packaging**: Package the mobile web app with native splash screens, haptic feedback on slip creation, and biometric login.
- [ ] **RevenueCat In-App Subscriptions**: Connect Apple App Store & Google Play Store subscriptions to the unified backend entitlement state.
- [ ] **Smart Push Notifications**: Alert subscribers when (a) a new `+5%+ EV` bet appears, (b) the Daily Safe Slip is published, or (c) confirmed starting lineups drop 60 minutes before kickoff and shift a match projection.

---

## 5. Standard Operating Procedures & Quality Gates

Every agent executing a task in `c:\Users\Mattia\gameApp` must follow these rules before declaring work complete:

1. **Pre-Flight Check**:
   - Inspect [`server.py`](file:///c:/Users/Mattia/gameApp/server.py), [`engine/data.py`](file:///c:/Users/Mattia/gameApp/engine/data.py), [`engine/model.py`](file:///c:/Users/Mattia/gameApp/engine/model.py), and [`public/index.html`](file:///c:/Users/Mattia/gameApp/public/index.html) to verify current state before editing.
   - Preserve existing docstrings, mathematical comments, and caching behavior unless explicitly refactoring them.

2. **Quantitative Verification Gate**:
   - After any change to [`engine/model.py`](file:///c:/Users/Mattia/gameApp/engine/model.py), run a quick verification command to confirm:
     - $P(\text{Home}) + P(\text{Draw}) + P(\text{Away}) \approx 1.000$ (within rounding tolerance `0.005`).
     - $P(\text{Over } x) + P(\text{Under } x) = 1.000$ for half-integer lines ($0.5, 1.5, 2.5, 3.5, 4.5$).
     - No `NaN`, `Inf`, or negative probabilities/odds (`fair <= 1.0`) are ever emitted in JSON.
     - Single-fixture `analyse()` completes in `< 150ms`.

3. **Frontend & Mobile UX Verification Gate**:
   - Ensure zero console errors, broken DOM selectors, or unescaped HTML strings.
   - Verify layout on both Desktop (`1280x800`) and Mobile (`390x844` iPhone viewport) dimensions.
   - Ensure loading states, empty filter states, and error states provide clear, actionable user feedback.

4. **Entrepreneurial Impact Summary**:
   - When presenting completed work to the user, briefly highlight:
     - **Technical Outcome**: What changed and how it was verified.
     - **Product / Subscription Value**: How this improvement increases user trust, conversion, retention, or mobile readiness.

