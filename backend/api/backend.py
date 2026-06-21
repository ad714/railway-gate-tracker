import os
import json
import logging
import asyncio
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from pprint import pformat
import concurrent.futures

# Load environment (RAILRADAR_API_KEY, etc.) from backend/.env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

# Live train data now comes from the RailRadar API (was the Selenium NTES scraper)
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from railradar_client import fetch_live_train_data
from predictor import predict_gate

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('railway_gate.log'),
        logging.StreamHandler()
    ]
)

# Station data lives in the repo (backend/data/), resolved relative to this file
STATIONS_JSON_PATH = str(Path(__file__).resolve().parent.parent / "data" / "kerala_railway_stations.json")

# Load station data
try:
    with open(STATIONS_JSON_PATH, 'r', encoding='utf-8') as f:
        all_stations = json.load(f)
    logging.info(f"Loaded {len(all_stations)} stations")
except Exception as e:
    logging.error(f"Failed to load station data: {str(e)}")
    exit(1)

# Pre-process route sequences (preserve JSON order)
route_sequences = {}
for station in all_stations:
    routes = station['route'] if isinstance(station['route'], list) else [station['route']]
    for route in routes:
        if route not in route_sequences:
            route_sequences[route] = []
        route_sequences[route].append(station)

# Define known junctions and their codes
junctions = {
    "TVC": {"name": "Thiruvananthapuram Central", "code": "TVC", "lat": 8.5241391, "lon": 76.9366376},
    "QLN": {"name": "Kollam Jn", "code": "QLN", "lat": 8.8932118, "lon": 76.6141396},
    "KYJ": {"name": "Kayamkulam Jn", "code": "KYJ", "lat": 9.1748422, "lon": 76.5013352},
    "ERS": {"name": "Ernakulam Jn", "code": "ERS", "lat": 9.9816358, "lon": 76.2998842},
    "NCJ": {"name": "Nagercoil Jn", "code": "NCJ", "lat": 8.1744, "lon": 77.4332},
    "SCT": {"name": "Sengottai", "code": "SCT", "lat": 8.9755, "lon": 77.2498}
}

# Predefine route-to-junction mapping (J1 = before, J2 = after)
route_junctions = {
    "Trivandrum to Kollam": {"J1": junctions["NCJ"], "J2": junctions["QLN"]},
    "Kollam to Kayamkulam": {"J1": junctions["QLN"], "J2": junctions["KYJ"]},
    "Kayamkulam - Ernakulam via Alappuzha": {"J1": junctions["KYJ"], "J2": junctions["ERS"]},
    "Kayamkulam via Kottayam to Ernakulam": {"J1": junctions["KYJ"], "J2": junctions["ERS"]},
    "Kollam - Aryankavu": {"J1": junctions["QLN"], "J2": junctions["SCT"]}
}

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers"""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def is_junction(station):
    """Identify if a station is a junction"""
    return ('jn' in station['station_name'].lower() or 
            'junction' in station['station_name'].lower() or
            'central' in station['station_name'].lower())

def detect_route_near_junction(gate_lat, gate_lon, route_coordinates):
    """Detect the specific railway route for a gate using the road route polyline"""
    min_dist = float('inf')
    closest_coord = None
    for coord in route_coordinates:
        dist = haversine(gate_lat, gate_lon, coord['latitude'], coord['longitude'])
        if dist < min_dist:
            min_dist = dist
            closest_coord = coord

    closest_station = min(all_stations, 
                         key=lambda s: haversine(closest_coord['latitude'], closest_coord['longitude'], s['lat'], s['lon']))
    
    routes = closest_station['route'] if isinstance(closest_station['route'], list) else [closest_station['route']]
    if len(routes) == 1:
        return routes[0]
    
    nearby_coords = [coord for coord in route_coordinates 
                    if haversine(gate_lat, gate_lon, coord['latitude'], coord['longitude']) < 5]
    route_scores = {}
    for route in routes:
        route_stations = route_sequences.get(route, [])
        if not route_stations:
            route_scores[route] = float('inf')
            continue
        total_dist = sum(haversine(coord['latitude'], coord['longitude'], s['lat'], s['lon']) 
                        for coord in nearby_coords for s in route_stations)
        avg_dist = total_dist / (len(nearby_coords) * len(route_stations)) if nearby_coords else float('inf')
        route_scores[route] = avg_dist
    
    return min(route_scores, key=route_scores.get)

def find_nearest_station_and_adjacents(gate_lat, gate_lon, route):
    """Find the nearest station (N) and adjacent stations (O1, O2) based on route sequence"""
    if route not in route_sequences:
        return None, None, None
    
    stations = route_sequences[route]
    closest_idx = min(range(len(stations)),
                     key=lambda i: haversine(gate_lat, gate_lon, stations[i]['lat'], stations[i]['lon']))
    
    N = stations[closest_idx]
    O1 = stations[closest_idx - 1] if closest_idx > 0 else None
    O2 = stations[closest_idx + 1] if closest_idx < len(stations) - 1 else None
    
    return N, O1, O2

def find_controlling_junctions(route):
    """Find junctions (J1, J2) based on predefined route mapping"""
    if route not in route_junctions:
        app.logger.warning(f"Route '{route}' not found in route_junctions mapping")
        return None, None
    
    junction_data = route_junctions[route]
    J1 = junction_data["J1"]
    J2 = junction_data["J2"]
    
    return J1, J2

def format_station(station):
    """Format station or junction data for response"""
    if not station:
        return None
    # Handle both station (from JSON) and junction (from dict) formats
    name = station.get('station_name') or station.get('name')
    code = station.get('station_code') or station.get('code')
    lat = station.get('lat')
    lon = station.get('lon')
    return {
        'name': name,
        'code': code,
        'position': {'latitude': lat, 'longitude': lon}
    }

@app.route('/railway_data', methods=['POST'])
def process_gates():
    try:
        data = request.get_json()
        
        app.logger.info(f"New request from {request.remote_addr}")
        app.logger.debug(f"Raw request data:\n{pformat(data, indent=2)}")
        
        gates = data.get('gates', [])
        route_coordinates = data.get('routeCoordinates', [])
        
        if not isinstance(gates, list) or not isinstance(route_coordinates, list):
            app.logger.error("Invalid data format - expected 'gates' and 'routeCoordinates' as lists")
            return jsonify({"error": "Expected 'gates' and 'routeCoordinates' as arrays"}), 400
        
        app.logger.info(f"Processing {len(gates)} gates with {len(route_coordinates)} route coordinates")
        
        results = []
        
        for i, gate in enumerate(gates):
            gate_lat = gate.get('crossingCenter', {}).get('latitude', gate['latitude'])
            gate_lon = gate.get('crossingCenter', {}).get('longitude', gate['longitude'])
            
            app.logger.debug(f"Processing Gate {i+1}: {gate.get('name')} at ({gate_lat}, {gate_lon})")
            
            # Detect the railway route
            route = detect_route_near_junction(gate_lat, gate_lon, route_coordinates)
            
            # Find nearest station (N) and adjacent stations (O1, O2)
            N, O1, O2 = find_nearest_station_and_adjacents(gate_lat, gate_lon, route)
            
            # Find controlling junctions (J1, J2) based on route
            J1, J2 = find_controlling_junctions(route)
            
            result = {
                'gate_id': gate['gateNumber'],
                'position': {'latitude': gate_lat, 'longitude': gate_lon},
                'route': route,
                'nearest_station': format_station(N),
                'adjacent_stations': {
                    'before': format_station(O1),
                    'after': format_station(O2)
                },
                'junctions': {
                    'before': format_station(J1),
                    'after': format_station(J2)
                }
            }
            
            app.logger.debug(f"Gate {i+1} result:\n{pformat(result, indent=2)}")
            results.append(result)
        
        # Fetch live train data between junctions
        app.logger.info("Fetching live train data for gates...")
        
        # Create a new event loop for the async task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Run the async task in a thread-safe manner
            with concurrent.futures.ThreadPoolExecutor() as pool:
                live_trains_data = loop.run_in_executor(
                    pool,
                    lambda: asyncio.run(fetch_live_train_data({"gates": results}, mode="between_junctions"))
                )
                live_trains_data = loop.run_until_complete(live_trains_data)
        finally:
            loop.close()
        
        app.logger.info(f"Live train data fetched: {pformat(live_trains_data, indent=2)}")
        
        # Add live train data to results, then run the closure predictor
        for result, live_trains in zip(results, live_trains_data):
            result["live_trains"] = live_trains["live_trains"]
            prediction = predict_gate(result)
            result["prediction"] = prediction

        app.logger.info(f"Returning results for {len(results)} gates with live train data")
        app.logger.debug(f"Final response:\n{pformat({'gates': results}, indent=2)}")
        return jsonify({"gates": results}), 200
        
    except Exception as e:
        app.logger.error(f"Error processing gates: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)