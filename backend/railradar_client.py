"""
RailRadar API client — replaces the old Selenium NTES_scraper.

Docs: https://railradar.in/docs   Base: https://api.railradar.in
Auth: header  X-API-Key: <key>   (read from env RAILRADAR_API_KEY)

Endpoints used:
  GET /api/v1/trains/{trainNo}        -> live status incl. liveData.currentPosition
  GET /api/v1/trains/between          -> trains between two station codes (?from=&to=)
  GET /api/v1/stations/{code}/live    -> live station board

NOTE: exact response field names are confirmed against a real response via probe.py.
Parsing below is defensive and centralised in the _extract_* helpers so it is the
only thing to adjust once we have a live sample.
"""
import os
import logging
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
    return {"X-API-Key": API_KEY, "Accept": "application/json"}


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
def get_train_status(train_no, journey_date=None):
    params = {"journeyDate": journey_date} if journey_date else None
    return _get(f"/api/v1/trains/{train_no}", params)


def get_trains_between(from_code, to_code):
    return _get("/api/v1/trains/between", {"from": from_code, "to": to_code})


def get_station_live(station_code):
    return _get(f"/api/v1/stations/{station_code}/live")


# ---------------------------------------------------------------------------
# Normalisation — the ONLY place that knows RailRadar's field names.
# Confirm/adjust these against probe.py output, then everything downstream works.
# ---------------------------------------------------------------------------
def _extract_trains_between(payload):
    """Return a list of {train_no, train_name, delay_min, last_station, next_station,
    eta_next_min} from a /trains/between response. Defensive against shape changes."""
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    rows = data.get("trains") or data.get("results") or data if isinstance(data, dict) else data
    trains = []
    for t in (rows or []):
        live = t.get("liveData") or t.get("live") or {}
        pos = live.get("currentPosition") or {}
        trains.append({
            "train_no": t.get("number") or t.get("trainNumber") or t.get("train_no"),
            "train_name": t.get("name") or t.get("trainName"),
            "delay_min": _to_int(live.get("delayMinutes") or pos.get("delay") or live.get("delay")),
            "last_station": pos.get("lastStation") or pos.get("last_station"),
            "next_station": pos.get("nextStation") or pos.get("next_station"),
            "eta_next_min": _to_int(pos.get("etaNextStationMin") or pos.get("etaMinutes")),
            "raw": t,
        })
    return trains


def _to_int(v):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Drop-in replacement for the old scraper's fetch_live_train_data(...)
# ---------------------------------------------------------------------------
def fetch_live_train_data(payload, mode="between_junctions"):
    """For each gate, fetch live trains running between its controlling junctions.

    payload = {"gates": [ {..., "junctions": {"before": {code}, "after": {code}}}, ... ]}
    Returns a list aligned with gates: [{"live_trains": [...]}, ...]
    """
    results = []
    for gate in payload.get("gates", []):
        j = gate.get("junctions") or {}
        before = (j.get("before") or {}).get("code")
        after = (j.get("after") or {}).get("code")
        live_trains = []
        if before and after:
            try:
                live_trains = _extract_trains_between(get_trains_between(before, after))
            except RailRadarError as e:
                log.warning("trains_between(%s,%s) failed: %s", before, after, e)
        results.append({"live_trains": live_trains})
    return results
