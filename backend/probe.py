"""
One-shot RailRadar probe. Run this ONCE after you set RAILRADAR_API_KEY in backend/.env
to dump real response shapes. Paste the output back so parsing in railradar_client.py
can be confirmed/finalised.

    cd backend
    pip install -r requirements.txt
    python probe.py

It prints (truncated) JSON for: a known train, trains-between two Kerala junction codes,
and a live station board.
"""
import json
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import railradar_client as rr


def dump(title, fn):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    try:
        data = fn()
        s = json.dumps(data, indent=2, ensure_ascii=False)
        print(s[:4000] + ("\n... (truncated)" if len(s) > 4000 else ""))
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    if not os.environ.get("RAILRADAR_API_KEY"):
        print("Set RAILRADAR_API_KEY in backend/.env first.")
        sys.exit(1)

    # 12257 = Kochuveli–Yesvantpur (runs the Kerala corridor); adjust as needed.
    dump("GET /trains/12257  (live status / currentPosition shape)",
         lambda: rr.get_train_status("12257"))

    # QLN = Kollam Jn, ERS = Ernakulam Jn — a real segment in our station data.
    dump("GET /trains/between?from=QLN&to=ERS  (trains-between shape)",
         lambda: rr.get_trains_between("QLN", "ERS"))

    dump("GET /stations/QLN/live  (live station board shape)",
         lambda: rr.get_station_live("QLN"))

    print("\nDone. Paste the above back to finalise field parsing.")
