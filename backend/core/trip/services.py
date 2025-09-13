import os
import math
from typing import Dict, Any, List, Tuple
import requests
import polyline as poly

ORS_API_KEY = os.getenv('ORS_API_KEY') 
GEOCODE_URL = os.getenv('GEOCODE_URL')
DIRECTIONS_URL = os.getenv('DIRECTIONS_URL')

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
	if r.status_code != 200:
		raise TripPlanningError(f'Geocoding failed: {r.text}')
	feats = r.json().get('features', [])
	if not feats:
		raise TripPlanningError(f'No results for location: {place}')
	coords = feats[0]['geometry']['coordinates'] # [lng, lat]
	return coords[1], coords[0]


def directions(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
	if not ORS_API_KEY:
		# fabricate a simple line if no key (dev mode)
		latlngs = [(lat, lng) for lat, lng in coords]
		enc = poly.encode(latlngs)
		return {
			'distance': 850000, # meters
			'duration': int(850/55*3600),
			'polyline': enc,
			'waypoints': [{'lat': lat, 'lng': lng} for lat, lng in coords],
		}
	body = {
		'coordinates': [[lng, lat] for lat, lng in coords],
		'instructions': True,
		'preference': 'recommended'
	}
	headers = {'Authorization': ORS_API_KEY, 'Content-Type': 'application/json'}
	r = requests.post(DIRECTIONS_URL, json=body, headers=headers, timeout=30)
	if r.status_code != 200:
		raise TripPlanningError(f'Directions failed: {r.text}')
	data = r.json()['features'][0]
	dist = data['properties']['summary']['distance'] # meters
	dur = data['properties']['summary']['duration'] # seconds
	# Build encoded polyline from geometry
	coords_ll = [(lat, lng) for lng, lat in data['geometry']['coordinates']]
	enc = poly.encode(coords_ll)
	return {
		'distance': dist,
		'duration': dur,
		'polyline': enc,
		'waypoints': [{'lat': lat, 'lng': lng} for lat, lng in coords_ll[:: int(max(1, len(coords_ll)//20)) ]],
	}


# Basic HOS/fuel logic placeholder
MAX_DRIVE_HOURS_PER_DAY = 11
ON_DUTY_LIMIT = 14
CYCLE_LIMIT_HOURS = 70
FUEL_INTERVAL_MILES = 1000
PICKUP_DROP_DURATION_MIN = 60

def build_logs(total_minutes: int) -> List[List[Dict[str, Any]]]:
	# naive split across days; refine later
	logs: List[List[Dict[str, Any]]] = []
	minutes_left = total_minutes
	day = 0
	while minutes_left > 0:
		day += 1
		drive_today = min(MAX_DRIVE_HOURS_PER_DAY*60, minutes_left)
		day_blocks = [
			{"status": "on_duty", "start": "07:00", "end": "08:00"},
			{"status": "driving", "start": "08:00", "end": f"{8 + drive_today//60:02d}:{drive_today%60:02d}"},
		]
		if drive_today < minutes_left:
			day_blocks.append({"status": "off_duty", "start": f"{8 + drive_today//60:02d}:{drive_today%60:02d}", "end": "24:00"})
		logs.append(day_blocks)
		minutes_left -= drive_today
	return logs


def plan_trip(data: Dict[str, Any]) -> Dict[str, Any]:
	start = data['current_location']
	pickup = data['pickup_location']
	drop = data['dropoff_location']
 
	# Geocode locations
	s = geocode(start)
	p = geocode(pickup)
	d = geocode(drop)

	# Route: start -> pickup -> drop
	route1 = directions([s, p])
	route2 = directions([p, d])

	total_distance_m = route1['distance'] + route2['distance']
	total_duration_s = route1['duration'] + route2['duration'] + PICKUP_DROP_DURATION_MIN*120 # pickup+drop

	# Fuel stops (every <= 1000 miles)
	distance_miles = round(total_distance_m / 1609.34, 1)
	fuel_stops_needed = max(0, int(distance_miles // FUEL_INTERVAL_MILES))

	stops: List[Dict[str, Any]] = [
		{"type": "pickup", "name": pickup, "lat": p[0], "lng": p[1], "duration_minutes": PICKUP_DROP_DURATION_MIN},
		{"type": "dropoff", "name": drop, "lat": d[0], "lng": d[1], "duration_minutes": PICKUP_DROP_DURATION_MIN},
	]

	# Logs
	duration_minutes = int(total_duration_s/60)
	logs = build_logs(duration_minutes)

	# Build a single valid polyline from the concatenated coordinates
	coords_combo = [s, p] + [p, d]  # Concatenate all coordinates in order
	combined_enc = poly.encode([s, p, d])
	polyline_enc = route1['polyline'] + route2['polyline']
	instructions = (route1.get('instructions', []) or []) + (route2.get('instructions', []) or [])


	return {
		'distance_miles': distance_miles,
		'duration_minutes': duration_minutes,
		'polyline': combined_enc,
		'polylines': [polyline_enc],
		'stops': stops,
		'logs': logs,
		'instructions': instructions,
  
	}