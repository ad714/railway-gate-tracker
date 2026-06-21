# Railway Gate Tracker (RGT) — Master Plan

_Last updated: 2026-06-21_

A real-time app that predicts which railway level-crossing **gates** will be closed
along a road route (and for how long), using **live train positions**, so drivers can
avoid getting stuck. Mobile-first (Expo / React Native).

---

## 0. TL;DR

- **Idea is validated and largely unique.** Big, painful problem; no mainstream app
  predicts *road* gate closures from live train data. Even the Indian Railways policy
  literature explicitly calls for exactly this app.
- **The #1 technical risk is solved.** Replace the brittle NTES Selenium scraper with
  the **RailRadar REST API**, which exposes exact live train coordinates.
- **Now:** consolidate the repo sprawl, wire RailRadar in, build an accuracy-measurement
  harness (the real moat), then take the Expo app to production.
- **Business model recommendation:** **open-core / freemium consumer + B2B(govt/fleet)**.
  Launch a free public beta to gather accuracy data (which is the defensible asset),
  monetize later via fleets/logistics + premium consumer features.

---

## 1. Workstream A — Repo & File Consolidation

### 1.1 Current inventory (7 local copies, 4 GitHub repos)

| Location | Git remote | Last commit | Stack | Verdict |
|---|---|---|---|---|
| `H:\RGT` | github **RGT-V2** | 2026-04-28 | Expo + TS | **CANONICAL (V2, going forward)** |
| `H:\RGT V2\rgt-v2` | local only | 2026-01-05 | Expo + TS | Superseded by `H:\RGT` -> delete |
| `H:\RGTApp\RGT2\RGT` | github **Railway_Gate_Tracker_RGT** | 2025-05-02 | Expo + Flask | **KEEP as archived V1 reference (working backend)** |
| `H:\RGTApp\RGT` | github **RGT** | 2025-04-14 | RN CLI + Flask | Superseded -> archive repo, delete local |
| `H:\RGTApp\RGT_backup` | local only | — | RN CLI | Delete (backup of above) |
| `H:\RGTApp\Railway-Gate-Tracker\Railway-Gate-Tracker` | local only | — | expo-router starter | Abandoned -> delete |
| `H:\RGTApp\Railway-Gate-Tracker\Railway Gate Tracker - RGT` | no git | — | — | Inspect then delete |
| `I:\RGT` | local git | 2025-03-28 | RN CLI | Earliest prototype -> delete after extracting research |
| `I:\RGT backup` | **NOT git** | 2025-03/04 | research + RN snapshots | **Split: keep research, delete RN snapshots** |

GitHub repos: `RGT-V2`, `Railway_Gate_Tracker_RGT`, `RGT`, `Railway-Gate-Tracker`.

### 1.2 Target end-state

```
H:\RGT\                     <- single working dir (repo: rename RGT-V2 -> railway-gate-tracker)
   |- app/ (Expo mobile)
   |- backend/ (prediction service on top of RailRadar)
   `- research/             <- curated research assets, committed via Git LFS
GitHub:
   railway-gate-tracker     <- active (was RGT-V2)
   rgt-v1-archive           <- Railway_Gate_Tracker_RGT, set to "Archived"
   (RGT, Railway-Gate-Tracker -> delete or archive)
```

### 1.3 Research files to PRESERVE (from `I:\RGT backup`)

- `NTES.html`, `Kerala Railway Stations Tapioca.html` (+ `_files/`) — scraped reference pages
- `stations list 2023.pdf` — source station list
- `live_trains_scraper_copy_selenium.py` — original scraper (historical reference)
- `kerala_railway_stations.json` (the curated station dataset — still useful as seed data)

**Delete (superseded by git history):** `RN\` milestone snapshot folders
("After Shyama Miss Presentation", "INTER PRESENTATION", "01All set upto...", etc.),
all `*_backup` dirs, debug screenshots, `*.log` files.

### 1.4 Steps (NOTHING destructive runs without your OK)

1. Confirm `H:\RGT` builds & is fully pushed to `RGT-V2`. (working tree clean)
2. Extract research assets -> `H:\RGT\research\` (curated), commit via Git LFS.
3. Archive `Railway_Gate_Tracker_RGT` on GitHub (Settings -> Archive) as the V1 reference.
4. Delete/Archive redundant GitHub repos `RGT` and `Railway-Gate-Tracker`.
5. Delete superseded local copies (list in 1.1) **after** a single cold zip backup to
   external/Drive (`RGT_cold_archive_2026-06.zip`) — belt-and-suspenders before any rm.
6. Rename `RGT-V2` repo -> `railway-gate-tracker`; update local remote URL.

---

## 2. Workstream B — RailRadar Integration (kill the scraper)

### 2.1 Why this changes everything
RailRadar exposes a **documented REST API** (`https://api.railradar.in/api/v1/...`,
API key header, ~150 ms live responses, OpenAPI 3.1) with:
- **Live interpolated train positions (exact lat/long), updated every few seconds**
- Live running status (delays, platform)
- **Trains-between-stations** + full schedules
- Station database
- Pricing: free tier; paid from **Rs 1,000/mo for 20k requests**.

This removes Selenium, NTES screen-scraping, the debug-screenshot fragility, and the
`railway_gate.log` churn entirely. **Verify before building:** exact endpoint for live
position, ToS allowing commercial use, and tier limits.

### 2.2 New architecture
```
Expo app --HTTPS--> RGT Prediction Service --> RailRadar API
                       |  (our IP / the moat)
                       |- gate dataset (curated level crossings + lat/long)
                       |- route->gate matcher (haversine, reuse from V1 backend.py)
                       |- train->gate occupancy predictor (ETA + speed + direction)
                       `- response cache (protect rate limits / cost)
```
- **Reuse from V1** (`RGTApp/RGT2/RGT/backend/backend.py`): haversine, nearest-station/
  adjacents, controlling-junction logic — it's sound; just swap the data source from
  scraper -> RailRadar, and generalize the hardcoded Kerala junction dicts into a data file.
- **Predictor v1:** for each gate, find trains whose interpolated position + heading +
  speed will cross that gate within the user's ETA window -> emit `{status, confidence,
  timeWindow, expectedDelayMin}` — the exact shape the V2 UI already consumes
  (`src/types/gate.ts`, `mockGates.ts`).
- **Caching is mandatory** (cost + rate limits): cache live positions ~10-15s, gate
  geometry forever, route matches per-session.

### 2.3 Steps
1. Sign up, get API key, read OpenAPI spec; confirm live-position endpoint + ToS.
2. Build a thin service (FastAPI or a serverless edge function) wrapping RailRadar +
   the ported prediction logic. Keep the API key server-side (never in the app bundle).
3. Replace `MOCK_GATES` in the Expo app with a real `GET /route-gates` call.
4. Build the **gate dataset** properly (see 3.2) — the predictor is only as good as
   the level-crossing coordinates.

---

## 3. Workstream C — Production + Mobile (Expo) Readiness

### 3.1 The validation gap (do this early — it's the moat)
Today the app *predicts* but never *proves* accuracy. Build an **accuracy harness**:
log `predicted closure` vs `actual` for a few real corridors over 1-2 weeks; target a
headline like *"80% accurate within a 5-min window."* This both de-risks the product and
becomes the defensible dataset competitors can't copy.

### 3.2 Data: the real bottleneck
- Need a trustworthy **level-crossing dataset** (lat/long, manned/unmanned, gate id).
  Sources: OpenStreetMap (`railway=level_crossing`), Indian Railways/state RTI data,
  manual survey of launch corridor. Start with **one city/corridor**, do it well.

### 3.3 Engineering hardening
- Server-side config & secrets; environment separation (dev/prod).
- Backend hosting: Railway/Render/Fly/AWS; cache layer (Redis/edge KV).
- App: error/empty/offline states, location-permission UX, background-safe polling,
  analytics + crash reporting (Sentry), EAS Build + OTA updates.
- Tests: keep/extend the existing `RouteResultScreen.test.tsx`; add predictor unit tests
  against recorded RailRadar fixtures.

### 3.4 Release path (mobile first, web later)
1. Internal build (EAS) -> 2. Closed beta on launch corridor (gather accuracy data) ->
3. Play Store open beta -> 4. iOS -> 5. **Web app later** via Expo Router + React Native
   Web (the V2 stack already supports this), or a thin Next.js marketing+web client
   reusing the same prediction API.

---

## 4. Workstream D — Market Study, Feasibility & Monetization

### 4.1 Problem size (India) — large and quantified
- **31,846 level crossings** (18,316 manned, 13,530 unmanned); ~49 per 100 km of track.
- A 10-min closure on a busy road ~= ~120 vehicles queued per side.
- **41% of accidents and 63% of deaths** on Indian Railways stem from desperation/risk-
  taking at crossings. Safety research: waiting >3 min drives risky behavior.
- **Policy literature explicitly proposes this exact app** (real-time crossing status +
  next-2-hours open/close, synced to timetables, integrated with Google Maps). Strong
  third-party validation of demand.

### 4.2 Competitive landscape — the white space is real
- Big players (RailYatri ~75M users, Where Is My Train, ixigo, Trainman, ConfirmTkt,
  etrain.info) all do **train tracking / ticketing for passengers**.
- **None predict road-side gate closures for drivers.** That intersection
  (live train data -> level-crossing closure -> your car's ETA) is unoccupied.
- **Adjacency risk:** any of them — or the Railways/govt itself — *could* add this.
  Moats = the curated gate dataset + proven prediction accuracy + first-mover UX.

### 4.3 Feasibility verdict
- **Technical:** feasible now that RailRadar replaces the scraper. Main effort = gate
  dataset + prediction accuracy, not plumbing.
- **Market:** demand is real and documented; differentiation is clear.
- **Risk:** data licensing/ToS (RailRadar commercial terms), crowd-sourced position
  accuracy, govt/incumbent entering, and the cost of building the gate dataset at scale.

### 4.4 Monetization — recommendation
**Recommended: Open-core / freemium consumer + B2B/B2G revenue.** Rationale:
- Launch **free consumer app** (open beta) to win adoption and — crucially — generate the
  accuracy dataset that is the actual moat. Optionally open-source the *client* to build
  trust/community while keeping the **prediction service + gate dataset proprietary**
  (open-core).
- **Revenue, in order of realism:**
  1. **B2B fleets / logistics / school-bus / ambulance ops** — route gate-closure
     avoidance has hard value (time, fuel). Sell API/dashboard subscriptions. _Best first revenue._
  2. **B2G / municipal traffic & police** — congestion analytics around crossings.
     High value, long sales cycles.
  3. **Premium consumer** (freemium): ad-free, multi-route alerts, predictive notifications.
  4. **Data/API licensing** to navigation apps once the dataset is proven.
- **Avoid** leading with consumer ads only — low ARPU, needs huge scale.
- **Pure open-source** is viable as a portfolio/public-good play, but forfeits the B2B
  upside; open-core captures both.

### 4.5 Go-to-market wedge
One corridor -> prove accuracy -> publish the "X% accurate" number -> expand corridor by
corridor. Lead every pitch with the *problem* (deaths/congestion) and the *proof*
(accuracy), not the tech.

---

## 5. Sequenced execution order

1. **A (cleanup)** — safe-archive + consolidate to one repo. _(Needs your go-ahead on deletes.)_
2. **B (RailRadar)** — verify API/ToS, build prediction service, swap mock data.
3. **C (data + accuracy)** — gate dataset for one corridor + accuracy harness.
4. **C (hardening + beta)** — ship closed beta on that corridor.
5. **D (GTM)** — use beta accuracy numbers to drive B2B/B2G conversations.

---

## 6. Open questions / to verify
- RailRadar: exact live-position endpoint, **commercial-use ToS**, real rate limits/cost
  at scale.
- Level-crossing dataset source for the first launch corridor (which city?).
- Confirm the `Railway-Gate-Tracker` GitHub repo + the no-git local folder contents before
  deletion.
- Cold-backup destination before any local deletes.

## Sources
- RailRadar API & pricing — https://railradar.in/indian-railway-data-api , https://railradar.in/docs
- Level-crossing stats & app proposal — https://www.ispp.org.in/leveraging-technology-to-mitigate-traffic-congestion-at-manned-railway-crossings-in-india/
- Crossing safety / waiting-time research — https://www.sciencedirect.com/science/article/abs/pii/S0003687018303776
- Level-crossing statistics — https://www.indiastat.com/data/transport/manned-unmanned-railway-level-crossing
- Competitor landscape — https://www.similarweb.com/website/railyatri.in/competitors/
