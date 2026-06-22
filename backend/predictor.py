"""
Gate-closure predictor (v1, heuristic).

Turns the structured gate context (nearest station + bracketing junctions) plus the
normalised live trains between those junctions into the GateSummary fields the app
renders: status, confidence, expectedDelayMin, timeWindow.

This is intentionally a transparent heuristic — it is the thing the accuracy harness
(Workstream C) will measure and tune. Inputs come from railradar_client's normalised
train dicts, so it is independent of RailRadar's raw JSON shape.

Tunables (minutes):
  GATE_CLOSE_BEFORE  gate typically shuts this long before the train reaches the crossing
  GATE_OPEN_AFTER    gate typically reopens this long after the train clears
  IMMINENT_ETA       a train within this ETA of the gate's station -> closure likely
"""
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))  # train times are IST; pin output to IST

GATE_CLOSE_BEFORE = 5
GATE_OPEN_AFTER = 3
IMMINENT_ETA = 12


def _fmt(t):
    return t.strftime("%-I:%M %p") if hasattr(t, "strftime") else str(t)


def _fmt_safe(t):
    # Windows strftime has no %-I; fall back to %I and strip leading zero.
    try:
        return t.strftime("%-I:%M %p")
    except ValueError:
        return t.strftime("%I:%M %p").lstrip("0")


def predict_gate(gate_context, now=None):
    """gate_context = one backend result dict with keys:
        nearest_station {code,name}, live_trains [normalised], ...
    Returns dict: {status, confidence, expectedDelayMin, timeWindow}.
    """
    now = now or datetime.now(IST)
    n = gate_context.get("nearest_station") or {}
    n_code = n.get("code")
    trains = gate_context.get("live_trains") or []

    if not trains:
        # No live data for this segment -> we genuinely don't know.
        return {
            "status": "UNCERTAIN",
            "confidence": "LOW",
            "expectedDelayMin": None,
            "timeWindow": None,
        }

    # Find the train most imminently approaching this gate's nearest station.
    candidates = []
    for t in trains:
        eta = t.get("eta_next_min")
        approaching = (t.get("next_station") == n_code) if n_code else False
        if eta is not None and (approaching or n_code is None):
            candidates.append((eta, t))

    if not candidates:
        # Trains exist on the segment but none clearly heading to this station soon.
        return {
            "status": "LIKELY_OPEN",
            "confidence": "MEDIUM",
            "expectedDelayMin": None,
            "timeWindow": None,
        }

    eta, train = min(candidates, key=lambda c: c[0])
    arrival = now + timedelta(minutes=eta)
    close_at = arrival - timedelta(minutes=GATE_CLOSE_BEFORE)
    open_at = arrival + timedelta(minutes=GATE_OPEN_AFTER)
    delay_lo = GATE_CLOSE_BEFORE
    delay_hi = GATE_CLOSE_BEFORE + GATE_OPEN_AFTER + max(0, train.get("delay_min") or 0) // 2 + 2

    if eta <= IMMINENT_ETA:
        status = "CLOSURE_LIKELY"
    else:
        status = "LIKELY_OPEN"

    # Confidence: do we have both ETA and a known delay from live tracking?
    has_delay = train.get("delay_min") is not None
    confidence = "HIGH" if (eta is not None and has_delay) else "MEDIUM"

    return {
        "status": status,
        "confidence": confidence,
        "expectedDelayMin": [delay_lo, delay_hi],
        "timeWindow": [_fmt_safe(close_at), _fmt_safe(open_at)],
        "_basis": {"train_no": train.get("train_no"), "eta_next_min": eta},
    }
