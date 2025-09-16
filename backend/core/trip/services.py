import os,requests
from typing import Dict, Any, List, Tuple
import requests
import polyline as poly

ORS_API_KEY = os.getenv('ORS_API_KEY') 
GEOCODE_URL = os.getenv('GEOCODE_URL')
DIRECTIONS_URL = os.getenv('DIRECTIONS_URL')

# Basic HOS/fuel logic placeholder
MAX_DRIVE_HOURS_PER_DAY = 11
ON_DUTY_LIMIT = 14
CYCLE_LIMIT_HOURS = 70
FUEL_INTERVAL_MILES = 1000
PICKUP_DROP_DURATION_MIN = 60
FUEL_STOP_MIN = 15 # time spent at fuel stop


class TripPlanningError(Exception):
	pass

def geocode(place: str) -> Tuple[float, float]:
	if not ORS_API_KEY:
		# fallback to synthetic coords for dev without key
		h = abs(hash(place))
		return 30 + (h % 1000) / 100.0, -100 + (h % 1000) / 100.0
	params = {
		'api_key': ORS_API_KEY,
		'text': place,
		'size': 1
	}
	r = requests.get(GEOCODE_URL, params=params, timeout=20)
	r.raise_for_status()
	feats = r.json().get('features', [])
	if not feats:
		raise TripPlanningError(f'No results for location: {place}')
	lng, lat = feats[0]["geometry"]["coordinates"]
	return lat, lng


def directions(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
	"""Return distance (m), duration (s), encoded polyline, coords (lat,lng) list"""
	if not ORS_API_KEY:
		# fabricate a simple line if no key (dev mode)
		coords_ll = list(coords)
		enc = poly.encode(coords_ll)
		return {
			'distance': 850000,  # meters
			'duration': int(850 / 55 * 3600),
			'polyline': enc,
			'coords': coords_ll,
			'instructions': [],
		}
	body = {
		'coordinates': [[lng, lat] for lat, lng in coords],
		'instructions': True,
		'preference': 'recommended'
	}
	headers = {'Authorization': ORS_API_KEY, 'Content-Type': 'application/json'}
	r = requests.post(DIRECTIONS_URL, json=body, headers=headers, timeout=30)
	r.raise_for_status()
	feat = r.json()['features'][0]
	dist = feat["properties"]["summary"]["distance"]
	dur = feat["properties"]["summary"]["duration"]
	# Build encoded polyline from geometry
	coords_ll = [(lat, lng) for lng, lat in feat["geometry"]["coordinates"]]
	enc = poly.encode(coords_ll)
	return {
		'distance': dist,
		'duration': dur,
		'polyline': enc,
		'coords': coords_ll,
		'instructions': feat["properties"].get("segments", []),
	}


def distribute_fuel_stops(coords: List[Tuple[float,float]], total_distance_m: float) -> List[int]:
    """Pick roughly-even indices along the route every <= 1000 miles."""
    miles = total_distance_m / 1609.34
    n = int(miles // FUEL_INTERVAL_MILES)
    if n <= 0 or len(coords) < 2:
        return []
    step = max(1, len(coords) // (n + 1))
    return [i * step for i in range(1, n + 1)]


def build_logs(total_minutes: int) -> List[List[Dict[str, Any]]]:
	logs: List[List[Dict[str, Any]]] = []
	minutes_left = total_minutes
	while minutes_left > 0:
		drive_today = min(MAX_DRIVE_HOURS_PER_DAY * 60, minutes_left)
		# driving starts at 08:00 each day
		start_minutes = 8 * 60
		end_total_minutes = start_minutes + drive_today
		end_h, end_m = divmod(end_total_minutes, 60)
		day = [
			{"status": "on_duty", "start": "07:00", "end": "08:00"},
			{"status": "driving", "start": "08:00", "end": f"{end_h:02d}:{end_m:02d}"},
		]
		if drive_today < minutes_left:
			day.append({"status": "off_duty", "start": f"{end_h:02d}:{end_m:02d}", "end": "24:00"})
		logs.append(day)
		minutes_left -= drive_today
	return logs


def plan_trip(data: Dict[str, Any]) -> Dict[str, Any]:
	s = geocode(data["current_location"])
	p = geocode(data["pickup_location"])
	d = geocode(data["dropoff_location"])

	r1 = directions([s, p])
	r2 = directions([p, d])

	total_distance_m = r1["distance"] + r2["distance"]
	# add pickup and dropoff durations (two stops) and convert minutes to seconds
	total_duration_s = r1["duration"] + r2["duration"] + (PICKUP_DROP_DURATION_MIN * 60 * 2)

	# concat coords → 1 route
	coords_combo = r1["coords"] + r2["coords"]
	combined_enc = poly.encode(coords_combo)

	# fuel stops by index along coords
	fuel_idx = distribute_fuel_stops(coords_combo, total_distance_m)

	stops = [
		{"type": "pickup", "name": data["pickup_location"], "lat": p[0], "lng": p[1], "duration_minutes": PICKUP_DROP_DURATION_MIN},
		*[
			{"type": "fuel", "name": "Fuel stop", "lat": coords_combo[i][0], "lng": coords_combo[i][1], "duration_minutes": FUEL_STOP_MIN}
			for i in fuel_idx
		],
		{"type": "dropoff", "name": data["dropoff_location"], "lat": d[0], "lng": d[1], "duration_minutes": PICKUP_DROP_DURATION_MIN},
	]

	# Logs
	duration_minutes = int(total_duration_s / 60)
	return {
		"distance_miles": round(total_distance_m / 1609.34, 1),
		"duration_minutes": duration_minutes,
		"polyline": combined_enc,
		"polylines": [r1["polyline"], r2["polyline"]],
		"stops": stops,
		"logs": build_logs(duration_minutes),
		"instructions": r1["instructions"] + r2["instructions"],
	}