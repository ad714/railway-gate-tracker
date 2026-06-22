"""
RailRadar API client — replaces the old Selenium NTES_scraper.

Docs: https://railradar.in/docs   Base: https://api.railradar.in
Auth: header  X-Api-Key: <key>  (or  Authorization: Bearer <key>) — read from env RAILRADAR_API_KEY

Endpoints used (confirmed against the OpenAPI spec):
  GET /v1/trains/{number}/live          -> live status incl. currentLocation.coordinates (GPS)
  GET /v1/trains/between/{from}/{to}    -> trains between two station codes (?live=true)
  GET /v1/stations/{code}/live          -> live station board (?hours=2|4|6|8)

NOTE: exact response field names are confirmed against a real response via probe.py.
Parsing below is defensive and centralised in the _extract_* helpers so it is the
only thing to adjust once we have a live sample.
"""
import os
import logging
from datetime import datetime, timezone
import requests

log = logging.getLogger(__name__)

BASE_URL = os.environ.get("RAILRADAR_BASE_URL", "https://api.railradar.in")
API_KEY = os.environ.get("RAILRADAR_API_KEY", "")
TIMEOUT = float(os.environ.get("RAILRADAR_TIMEOUT", "8"))


class RailRadarError(RuntimeError):
    pass


def _headers():
    if not API_KEY:
        raise RailRadarError(
            "RAILRADAR_API_KEY is not set. Sign up at https://railradar.in, "
            "create an API key, and put it in backend/.env"
        )
    return {"X-Api-Key": API_KEY, "Accept": "application/json"}


def _get(path, params=None):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        log.error("RailRadar HTTP %s for %s", getattr(e.response, "status_code", "?"), url)
        raise RailRadarError(str(e)) from e
    except requests.RequestException as e:
        log.error("RailRadar request failed for %s: %s", url, e)
        raise RailRadarError(str(e)) from e


# ---------------------------------------------------------------------------
# Raw endpoint wrappers
# ---------------------------------------------------------------------------
def get_train_status(train_no, date=None):
    params = {"includeCoordinates": "true"}
    if date:
        params["date"] = date
    return _get(f"/v1/trains/{train_no}/live", params)


def get_trains_between(from_code, to_code, live=True):
    params = {"live": "true"} if live else None
    return _get(f"/v1/trains/between/{from_code}/{to_code}", params)


def get_station_live(station_code, hours=4):
    return _get(f"/v1/stations/{station_code}/live", {"hours": hours})


# ---------------------------------------------------------------------------
# Normalisation — the ONLY place that knows RailRadar's field names.
# Field names below are CONFIRMED against live /v1/stations/{code}/live responses.
# ---------------------------------------------------------------------------
def _to_int(v):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)  # handles the "+05:30" offset
    except (TypeError, ValueError):
        return None


# Keep only trains relevant to an imminent closure: from just-arrived to ~90 min out.
_ETA_WINDOW_MIN = (-3, 90)


def _extract_station_board(payload, station_code, now=None):
    """Normalise /v1/stations/{code}/live -> trains approaching THIS station, each as
    {train_no, train_name, delay_min, next_station, eta_next_min, live_type}.
    Since the board is keyed on `station_code`, every train here is heading to/at it,
    so `next_station` is set to `station_code` and `eta_next_min` is the ETA to the gate."""
    now = now or datetime.now(timezone.utc)
    data = payload.get("data", payload) if isinstance(payload, dict) else {}
    out = []
    for t in (data.get("trains") or []):
        tr = t.get("train") or {}
        live = t.get("live") or {}
        eta_dt = _parse_dt(live.get("expectedArrivalTime") or live.get("expectedDepartureTime"))
        eta_min = round((eta_dt - now).total_seconds() / 60) if eta_dt else None
        if eta_min is not None and not (_ETA_WINDOW_MIN[0] <= eta_min <= _ETA_WINDOW_MIN[1]):
            continue
        out.append({
            "train_no": tr.get("number"),
            "train_name": tr.get("name"),
            "delay_min": _to_int(live.get("delayMinutes")),
            "next_station": station_code,
            "eta_next_min": eta_min,
            "live_type": live.get("type"),
        })
    return out


# ---------------------------------------------------------------------------
# Drop-in replacement for the old scraper's fetch_live_train_data(...)
# Primary signal: the live board of each gate's NEAREST station.
# (Known v1 limitation: a station board lists trains that halt at it; express trains
#  passing through without a halt may be under-counted. Revisit in the accuracy phase
#  with a trains-between / route-position fallback. Tracked in docs/HANDOFF.md.)
# ---------------------------------------------------------------------------
def fetch_live_train_data(payload, mode="station_board"):
    """For each gate, fetch live trains approaching its nearest station.

    payload = {"gates": [ {..., "nearest_station": {"code": ...}}, ... ]}
    Returns a list aligned with gates: [{"live_trains": [...]}, ...]
    """
    results = []
    for gate in payload.get("gates", []):
        code = (gate.get("nearest_station") or {}).get("code")
        live_trains = []
        if code:
            try:
                live_trains = _extract_station_board(get_station_live(code, hours=4), code)
            except RailRadarError as e:
                log.warning("station_live(%s) failed: %s", code, e)
        results.append({"live_trains": live_trains})
    return results
