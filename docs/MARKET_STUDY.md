# RGT — Market Study & Feasibility Report

_2026-06-21 · An honest assessment, not a pitch deck._

Four questions, answered straight:
1. How can RGT actually be useful?
2. Why hasn't everyone already built it?
3. Is it *really* useful?
4. Will people *actually* use it?

---

## 1. How RGT can be useful

The job-to-be-done: **"Don't make me get stuck at a closed railway gate."** RGT predicts,
*before* you commit to a route, which level crossings on it will be shut and for how long —
so you can re-route, leave later, or just not be surprised.

Who that helps, in order of how much the pain is worth money:

- **Fleets & time-critical drivers** — logistics, delivery, school buses, **ambulances**,
  cab aggregators. A blocked crossing is measurable lost time/fuel, and a dispatcher routing
  many vehicles compounds the value. This is where the pain has a price tag.
- **Daily commuters** on corridors with busy crossings — the classic "I left on time and
  still got stuck 12 minutes at the gate" frustration.
- **Traffic authorities / city planners** — aggregate closure + congestion data around
  crossings is useful for signal timing and ROB/RUB prioritisation.

Why it's *possible* at all: India runs **~18,000 manned level crossings** still in service,
**~54% interlocked with signals** (i.e. closures are deterministic from train movements),
and live train positions are now obtainable via the **RailRadar API**. The raw materials
exist; nobody has assembled them into a driver-facing predictor.

---

## 2. Why hasn't everyone already built it?

This is the most important question, because "obvious + valuable + unbuilt" usually means a
hidden barrier. Here are the real ones — and they're also RGT's moat.

### (a) The live train data was genuinely hard to get — until recently
There is **no official public API** for live Indian train data. NTES partner feeds are
limited to approved partners; IRCTC is locked behind captcha/OTP/anti-bot controls and ToS
that forbid scraping. So historically anyone attempting this hit a wall and resorted to
**brittle scraping** (exactly what RGT v1 did with Selenium — and exactly why it kept
breaking). The recent emergence of paid aggregators like **RailRadar** is what makes a
*reliable* version newly feasible. The barrier didn't disappear; it became a ₹1,000/mo
line item. Most people who tried this 3–5 years ago gave up here.

### (b) The level-crossing dataset doesn't exist as clean open data
You need precise gate coordinates, which gates are interlocked, and how each maps to the
bracketing stations. This isn't published as a tidy dataset — it's **manual, hyperlocal,
unglamorous data work**, corridor by corridor. It doesn't scale from a laptop, and it's
boring, so it rarely gets done. **Whoever builds it owns the moat.**

### (c) It's a cross-domain orphan
The problem sits **between railways and roads**. Train apps (RailYatri ~75M users, Where Is
My Train, ixigo, ConfirmTkt) serve *passengers* — tickets, PNR, "where's my train." Map apps
(Google/Apple) own *road* routing but have **no train-occupancy data**. The valuable
intersection — *train data → road gate closure → your car's ETA* — is **nobody's core
business**, so neither side prioritises it. White space exists precisely because it falls
between two big incumbents' mandates.

### (d) Incumbent incentives point elsewhere
Train apps monetise passenger intent (tickets/ads); a driver avoiding a crossing isn't their
funnel. For Google Maps it's a low-priority, single-country, hyperlocal feature competing
against global roadmap items. Rational for them to skip — leaving room for a focused player.

### (e) The government's official answer is concrete, not software
India is **physically eliminating** crossings via Rail-Over/Under-Bridges and interlocking —
a ~₹41,200 crore, multi-decade civil-engineering programme (target: 2,429 crossings on the
Golden Quadrilateral by 2025). That's the "real" fix everyone points to. But it's *slow* and
leaves **~18,000 crossings live for the next 10–20 years** — a long interim window where a
software mitigation has room to exist. (It also means the policy literature has *explicitly
proposed this exact app* — strong validation, but also a hint that the state could build it.)

### (f) Prediction is harder than a demo makes it look
Nearest-station ≠ the exact minute a specific gate shuts. Trains skip halts, gates close
5–10 min early, double-tracking and interlocking logic vary. Turning "a train is near" into
"this gate, this window, this confidence" — and *proving* it — is real engineering most
prototypes (RGT included, so far) never validate.

**Net:** it's unbuilt not because it's a bad idea, but because it requires stitching together
hard-to-get data, a dataset nobody wants to build, across two domains neither incumbent owns,
for a problem the state is "solving" on a 20-year timeline. That combination is a moat for a
focused builder.

---

## 3. Is it *really* useful? (the honest case for and against)

**For:**
- The pain is large and quantified: a 10-min closure ≈ ~120 vehicles queued per side;
  **41% of railway accidents and 63% of railway deaths** stem from desperation at crossings;
  safety research shows waits **>3 min** trigger risky road-user behaviour.
- It's *preventive*: re-routing before you're stuck has obvious value, and predictive ETA
  beats the status quo (Google Maps routes you straight into the gate).

**Against (be honest):**
- **Low information value once you're already there** — if you can see the gate is down, the
  app told you nothing. The value is *upstream*, at route-choice time. That demands the app be
  in the navigation decision, not a thing you open at the gate.
- **Many crossings, short waits** — a lot of closures are 2–4 minutes; below the threshold
  where people re-route. The high-value cases are the busy, long-closure crossings — a subset.
- **Shrinking TAM (slowly)** — every ROB built removes a crossing. The market erodes over
  years, so this is a "win the next decade" product, not a forever one.

**Verdict:** genuinely useful for a **focused segment** (busy corridors + fleets/time-critical
drivers), oversold as a mass-market everyday consumer app. Aim at the segment where being
stuck actually costs money.

---

## 4. Will people *actually* use it?

This is where most "useful" ideas die, so separate *useful* from *used*:

- **Standalone consumer app = low frequency.** You'd only open it near a crossing — weak daily
  habit, hard retention, high cost to acquire users for a few-times-a-week utility. As a
  standalone B2C play, adoption is an uphill climb.
- **It gets used when it's ambient, not opened:**
  - **Embedded in navigation** — a gate-closure layer/alert inside the routing you already do.
    Either RGT *becomes* a lightweight nav app for its corridors, or (more realistically)
    partners/licenses the layer. This is the real consumer adoption path.
  - **Push, not pull** — "Leave 5 min later, Vikhroli gate shuts 7:45–7:55" notifications for
    saved commutes turn a low-frequency tool into a passive daily value-add.
  - **Fleet dashboards** — drivers don't adopt anything; the *dispatcher* does, once, and
    routes everyone. B2B adoption is a single decision, not a million habits. **Highest
    realistic usage with the least adoption friction.**
- **Trust gate:** people abandon a predictor that's wrong twice. Usage is gated on a published,
  measured accuracy number (the harness in the roadmap). No accuracy proof → no retention.

**Honest answer:** *Yes, but not as a standalone consumer download.* It will be used if it's
(1) a fleet/dispatch tool where one buyer onboards many users, and/or (2) a passive,
notification-first layer for saved commutes — ideally inside an existing navigation flow.
A cold standalone B2C app on the Play Store is the *least* likely path to real usage.

---

## Bottom line

- **Useful:** yes — for a focused, high-value segment, with quantified pain and a clear gap.
- **Why unbuilt:** hard-to-get data + an unbuilt dataset + a cross-domain orphan problem +
  a state solving it slowly in concrete. Those barriers are now partly lifted (RailRadar) and
  the rest (the gate dataset + proven accuracy) are exactly what a focused team can own.
- **Will it be used:** as a **fleet/B2B tool and a notification-first commute layer**, plausibly
  yes; as a **standalone consumer app**, probably not. Build for the segment that pays for time.
- **The single thing that decides it:** *proven prediction accuracy on one real corridor.*
  Everything — usefulness, defensibility, adoption, monetisation — rests on being able to say
  "X% accurate within 5 minutes." That number is the whole ballgame.

---

## Sources
- Level-crossing congestion + the proposed app — https://www.ispp.org.in/leveraging-technology-to-mitigate-traffic-congestion-at-manned-railway-crossings-in-india/
- Waiting-time / risky-behaviour research — https://www.sciencedirect.com/science/article/abs/pii/S0003687018303776
- Level-crossing statistics — https://www.indiastat.com/data/transport/manned-unmanned-railway-level-crossing
- Unmanned crossing elimination programme — https://pib.gov.in/PressReleaseIframePage.aspx?PRID=1481736
- Manned crossing elimination (ROB/RUB, cost/targets) — https://www.business-standard.com/india-news/all-unmanned-level-crossings-on-railways-broad-gauge-track-eliminated-123120601012_1.html
- No official train-data API / access barriers — https://crisapis.indianrail.gov.in/ , https://rapidapi.com/search/indian+railways
- RailRadar API & pricing — https://railradar.in/indian-railway-data-api
- Competitor landscape — https://www.similarweb.com/website/railyatri.in/competitors/
