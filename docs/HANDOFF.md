# RGT — Session Handoff

_Last updated: 2026-06-21_

Pick up here. This is the single source of truth for project state.

> **Immediate next steps:** (1) user is provisioning the RailRadar key into `backend/.env`
> -> then run `backend/probe.py` and finalise B. (2) Then a **UI/UX revamp for snappiness**
> (Workstream E below).

## Canonical locations (everything else was deleted)
- **Working copy:** `H:\RGT` (the ONLY active copy)
- **GitHub (active):** https://github.com/ad714/railway-gate-tracker  (branch `master`)
- **GitHub (archived V1 reference, has the original working Flask app):** `ad714/Railway_Gate_Tracker_RGT`
- **Cold backup of all deleted copies (1.4 GB):** `H:\RGTApp\_RGT_cold_archive_2026-06\`
- Plans/docs in repo: `RGT_MASTER_PLAN.md`, `docs/MARKET_STUDY.md` (markdown source),
  `docs/RGT_Market_Study.pdf` + `docs/RGT_Market_Study.html` (styled 5-page report,
  rendered via Chrome headless), this file.

## What the project is
Mobile-first (Expo/React Native + TypeScript) app that predicts which railway level-crossing
**gates** are closed along a driving route, and for how long, from **live train positions**.
V2 frontend is polished but ran on mock data; we are wiring real data in.

## Status by workstream
- **A — Repo consolidation: DONE.** 7 copies + 4 repos -> 1 active + 1 archived. Research
  preserved in `H:\RGT\research\`.
- **B — RailRadar integration: CODE DONE, not yet live.** Selenium scraper replaced.
  - `backend/railradar_client.py` — RailRadar REST client (`X-API-Key`), drop-in for old scraper.
    The `_extract_*` helpers are the ONLY place that knows RailRadar's field names.
  - `backend/predictor.py` — heuristic that outputs the app's `GateSummary`
    (status/confidence/expectedDelayMin/timeWindow). Smoke-tested, works.
  - `backend/api/backend.py` — fixed dead hardcoded station path -> `backend/data/...`,
    loads `.env`, wires predictor into `POST /railway_data`.
  - `backend/probe.py`, `requirements.txt`, `.env.example` — setup + live-shape capture.
- **C — Production / accuracy: NOT STARTED.**
- **E — UI/UX revamp (NEW, user-requested): NOT STARTED.** Redesign the Expo app to feel
  "snappy". Independent of the RailRadar key — can run in parallel. Scope to confirm with user:
  is "snappy" mainly (i) performance/perceived responsiveness (fast nav transitions, no jank,
  skeleton loaders, optimistic UI, FlatList tuning) or (ii) a visual/UX redesign, or both?
  Current app: 2 screens (`HomeScreen`, `RouteResultScreen`) switched by boolean state in
  `App.tsx` (no real navigation library wired despite deps); theme tokens in `src/theme/tokens.ts`;
  gate list via FlatList + mock data. Likely wins: real navigation + animated transitions, loading
  skeletons while the predictor runs, micro-interactions, and a polished design pass. Consider
  skills `ui-ux-pro-max` / `frontend-design` when starting.
- **D — Market study: DONE.** Markdown at `docs/MARKET_STUDY.md`; styled PDF deliverable at
  `docs/RGT_Market_Study.pdf` (source `docs/RGT_Market_Study.html`). To re-render the PDF after
  editing the HTML: `chrome --headless --print-to-pdf=docs/RGT_Market_Study.pdf --print-to-pdf-no-header file:///H:/RGT/docs/RGT_Market_Study.html`.

## BLOCKING next action (user) to make B live
1. Sign up at https://railradar.in -> create API key -> pick tier (free to start).
2. `cp backend/.env.example backend/.env` and paste the key into `RAILRADAR_API_KEY`.
3. `cd backend && pip install -r requirements.txt && python probe.py`
4. Paste probe output back -> finalise field parsing in `railradar_client._extract_*`.

## Next work after key (Workstream C)
- **Pick ONE launch corridor** (decision needed: which city/route?).
- Build the **level-crossing dataset** for it (lat/lng, interlocked?, gate id) — source from
  OpenStreetMap `railway=level_crossing` + manual verification. This is the real bottleneck.
- **"Gates along my route" source** is still unsolved: V1 had the app detect gates via Google
  Maps + a gate dataset and POST them to the backend. Decide: app-side detection (needs Google
  Directions + spatial query) vs. backend route->gates endpoint.
- Build the **accuracy harness**: log predicted vs actual closures for ~1-2 weeks. Target a
  headline "X% accurate within 5 min" — this number gates usefulness, adoption, and funding.

## Key facts / decisions locked
- Data source = **RailRadar API** (not scraping). Verify commercial-use ToS before launch.
- Platform = **mobile-first Expo**; web later via React Native Web.
- Business model (recommended) = **open-core / freemium consumer + B2B(fleet)/B2G**; lead
  revenue with fleets. Market study concluded standalone B2C adoption is the weakest path.
- The app's data contract is `src/types/gate.ts` `GateSummary`; the predictor already matches it.

## Gotchas
- Google/Stitch key lives in gitignored `H:\RGT\.env` (`stitch_api_key`) — safe, NOT committed.
- Windows: `strftime('%-I')` fails; predictor uses a `_fmt_safe` fallback.
- `.gitignore` covers `backend/.env`, `__pycache__/`, `*.log`.
