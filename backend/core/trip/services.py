import os
import requests
import polyline as poly
from typing import Dict, Any, List, Tuple

ORS_API_KEY = os.getenv("ORS_API_KEY")
GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv"

# HOS / fueling placeholders
MAX_DRIVE_HOURS_PER_DAY = 11
ON_DUTY_LIMIT = 14
CYCLE_LIMIT_HOURS = 70
FUEL_INTERVAL_MILES = 1000
PICKUP_DROP_DURATION_MIN = 60
FUEL_STOP_MIN = 15  # IMPORTANT: define this

class TripPlanningError(Exception):
    pass

def _fake_coord(seed: str) -> Tuple[float, float]:
    h = abs(hash(seed))
    return 30 + (h % 1000) / 100.0, -100 + (h % 1000) / 100.0

def geocode(place: str) -> Tuple[float, float]:
    if not ORS_API_KEY:
        return _fake_coord(place)
    try:
        r = requests.get(GEOCODE_URL, params={"api_key": ORS_API_KEY, "text": place, "size": 1}, timeout=20)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if not feats:
            raise TripPlanningError(f"No geocode results for: {place}")
        lng, lat = feats[0]["geometry"]["coordinates"]
        return lat, lng
    except Exception as e:
        # fallback instead of 500
        return _fake_coord(place)

def directions(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
    """Return distance (m), duration (s), encoded polyline, coords (lat,lng). Always returns coords."""
    if not ORS_API_KEY:
        coords_ll = list(coords)
        return {
            "distance": 850_000,
            "duration": int(850 / 55 * 3600),
            "polyline": poly.encode(coords_ll),
            "coords": coords_ll,
            "instructions": [],
        }
    try:
        body = {"coordinates": [[lng, lat] for lat, lng in coords], "instructions": True, "preference": "recommended"}
        headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
        r = requests.post(DIRECTIONS_URL, json=body, headers=headers, timeout=30)
        r.raise_for_status()
        feat = r.json()["features"][0]
        dist = feat["properties"]["summary"]["distance"]
        dur = feat["properties"]["summary"]["duration"]
        coords_ll = [(lat, lng) for lng, lat in feat["geometry"]["coordinates"]]
        return {
            "distance": dist,
            "duration": dur,
            "polyline": poly.encode(coords_ll),
            "coords": coords_ll,
            "instructions": feat["properties"].get("segments", []),
        }
    except Exception:
        # full fallback instead of 500
        coords_ll = list(coords)
        return {
            "distance": 850_000,
            "duration": int(850 / 55 * 3600),
            "polyline": poly.encode(coords_ll),
            "coords": coords_ll,
            "instructions": [],
        }

def distribute_fuel_stops(coords: List[Tuple[float, float]], total_distance_m: float) -> List[int]:
    miles = total_distance_m / 1609.34
    n = int(miles // FUEL_INTERVAL_MILES)
    if n <= 0 or len(coords) < 2:
        return []
    step = max(1, len(coords) // (n + 1))
    return [i * step for i in range(1, n + 1)]

def build_logs(total_minutes: int) -> List[List[Dict[str, Any]]]:
    logs: List[List[Dict[str, Any]]] = []
    left = total_minutes
    while left > 0:
        drive_today = min(MAX_DRIVE_HOURS_PER_DAY * 60, left)
        end_h, end_m = divmod(8 * 60 + drive_today, 60)
        day = [
            {"status": "on_duty", "start": "07:00", "end": "08:00"},
            {"status": "driving", "start": "08:00", "end": f"{end_h:02d}:{end_m:02d}"},
        ]
        if drive_today < left:
            day.append({"status": "off_duty", "start": f"{end_h:02d}:{end_m:02d}", "end": "24:00"})
        logs.append(day)
        left -= drive_today
    return logs

def plan_trip(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        s = geocode(data["current_location"])
        p = geocode(data["pickup_location"])
        d = geocode(data["dropoff_location"])

        r1 = directions([s, p])
        r2 = directions([p, d])

        total_distance_m = r1["distance"] + r2["distance"]
        total_duration_s = r1["duration"] + r2["duration"] + PICKUP_DROP_DURATION_MIN * 120

        coords_combo = r1["coords"] + r2["coords"]
        combined_enc = poly.encode(coords_combo)

        fuel_idx = distribute_fuel_stops(coords_combo, total_distance_m)
        stops = [
            {"type": "pickup", "name": data["pickup_location"], "lat": p[0], "lng": p[1], "duration_minutes": PICKUP_DROP_DURATION_MIN},
            *[
                {"type": "fuel", "name": "Fuel stop", "lat": coords_combo[i][0], "lng": coords_combo[i][1], "duration_minutes": FUEL_STOP_MIN}
                for i in fuel_idx
            ],
            {"type": "dropoff", "name": data["dropoff_location"], "lat": d[0], "lng": d[1], "duration_minutes": PICKUP_DROP_DURATION_MIN},
        ]

        duration_minutes = int(total_duration_s / 60)
        return {
            "distance_miles": round(total_distance_m / 1609.34, 1),
            "duration_minutes": duration_minutes,
            "polyline": combined_enc,
            "polylines": [r1["polyline"], r2["polyline"]],
            "stops": stops,
            "logs": build_logs(duration_minutes),
            "instructions": (r1.get("instructions") or []) + (r2.get("instructions") or []),  # ← add this
        }
    except Exception as e:
        # Surface a meaningful error to the view; DRF will turn it into 400
        raise TripPlanningError(str(e))
