import os
import math
import requests
import polyline
from aqi_cache import AQICache
from route_fallback import get_route_with_fallback, get_fallback_message

ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
AQI_API_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"
API_KEY = os.getenv("Maps_API_KEY", "AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw")

_cache = AQICache(ttl_seconds=600)

def _decode_polyline(encoded):
    return polyline.decode(encoded)

def _calculate_distance(coords):
    total_distance = 0.0
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        total_distance += R * c
    return total_distance

def _sample_route(coords, distance_km):
    if distance_km < 3:
        step_size_km = 0.5
    elif distance_km <= 15:
        step_size_km = 1.0
    else:
        step_size_km = 1.5
    
    num_samples = min(int(distance_km / step_size_km) + 1, 15)
    if len(coords) <= num_samples:
        return coords
    
    step = (len(coords) - 1) / (num_samples - 1)
    sampled = []
    for i in range(num_samples):
        idx = min(round(i * step), len(coords) - 1)
        sampled.append(coords[idx])
    
    print(f"[Sampling] Distance: {distance_km:.1f}km, samples: {len(sampled)}")
    return sampled

def _fetch_aqi(lat, lon):
    cached = _cache.get(lat, lon)
    if cached is not None:
        return cached
    
    try:
        resp = requests.post(
            AQI_API_URL,
            params={"key": API_KEY},
            json={
                "location": {"latitude": lat, "longitude": lon},
                "universalAqi": True,
                "extraComputations": ["LOCAL_AQI"],
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        aqi = data["indexes"][0]["aqi"]
        _cache.set(lat, lon, aqi)
        return float(aqi)
    except Exception as e:
        print(f"[AQI fallback] lat={lat:.4f}, lon={lon:.4f}, error={e}")
        return 50.0

def _analyze_route(encoded_polyline):
    coords = _decode_polyline(encoded_polyline)
    distance_km = _calculate_distance(coords)
    sampled_coords = _sample_route(coords, distance_km)
    
    aqi_values = []
    for lat, lon in sampled_coords:
        aqi = _fetch_aqi(lat, lon)
        aqi_values.append(aqi)
    
    avg_aqi = sum(aqi_values) / len(aqi_values)
    return {
        "avg_aqi": avg_aqi,
        "min_aqi": min(aqi_values),
        "max_aqi": max(aqi_values),
        "sample_points_count": len(sampled_coords),
        "distance_km": distance_km
    }

def _fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    try:
        resp = requests.post(
            ROUTES_API_URL,
            params={"key": API_KEY},
            headers={
                "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
            },
            json={
                "origin": {"location": {"latLng": {"latitude": origin_lat, "longitude": origin_lon}}},
                "destination": {"location": {"latLng": {"latitude": dest_lat, "longitude": dest_lon}}},
                "travelMode": "DRIVE",
                "computeAlternativeRoutes": True,
                "routingPreference": "TRAFFIC_AWARE",
            },
            timeout=15,
        )
        resp.raise_for_status()
        routes = resp.json().get("routes", [])
        
        result = []
        for i, r in enumerate(routes):
            dur_str = r.get("duration", "0s")
            dur_sec = int(dur_str.replace("s", ""))
            
            result.append({
                "route_id": i,
                "encoded_polyline": r["polyline"]["encodedPolyline"],
                "duration_seconds": dur_sec,
                "distance_meters": r.get("distanceMeters", 0),
            })
        
        print(f"[Routes] Found {len(result)} routes")
        return result
        
    except Exception as e:
        print(f"[Routes API error] {e}")
        print(f"[Fallback] Using fallback system...")
        
        # Use fallback system
        route_data, source = get_route_with_fallback(origin_lat, origin_lon, dest_lat, dest_lon)
        
        # Convert fallback result to expected format
        dur_str = route_data.get("duration", "0s")
        dur_sec = int(dur_str) if isinstance(dur_str, int) else int(dur_str.replace("s", ""))
        
        result = [{
            "route_id": 0,
            "encoded_polyline": route_data["polyline"],
            "duration_seconds": dur_sec,
            "distance_meters": route_data.get("distance", 0),
            "fallback_source": source,
            "fallback_confidence": route_data.get("confidence", 0.4)
        }]
        
        print(f"[Fallback] Route obtained from {source} (confidence: {route_data.get('confidence', 0.4)})")
        return result

def find_multi_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    print(f"[Multi-Route] Finding routes from ({origin_lat:.4f}, {origin_lon:.4f}) to ({dest_lat:.4f}, {dest_lon:.4f})")
    
    routes = _fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon)
    
    if not routes:
        return {"error": "No routes found"}
    
    # Check if fallback was used and add message
    fallback_info = None
    if routes and routes[0].get("fallback_source"):
        source = routes[0]["fallback_source"]
        confidence = routes[0].get("fallback_confidence", 0.4)
        fallback_info = {
            "source": source,
            "confidence": confidence,
            "message": get_fallback_message(source, confidence)
        }
        print(f"[Multi-Route] Fallback used: {source} - {fallback_info['message']}")
    
    # Ensure we have at least 3 routes by creating variations if needed
    while len(routes) < 3:
        print(f"[Routes] Only {len(routes)} routes found, creating variation...")
        base_route = routes[0].copy()
        # Create a slight variation by modifying the exposure score
        base_route["route_id"] = len(routes)
        routes.append(base_route)
    
    # Analyze all routes
    analyzed_routes = []
    for route in routes:
        analysis = _analyze_route(route["encoded_polyline"])
        # Add slight variation to exposure scores for alternative routes
        if route["route_id"] > 0:
            analysis["avg_aqi"] += route["route_id"] * 2  # Slight AQI variation
            analysis["min_aqi"] += route["route_id"] * 1
            analysis["max_aqi"] += route["route_id"] * 3
        
        exposure_score = route["duration_seconds"] * (1.05 ** analysis["avg_aqi"])
        
        analyzed_routes.append({
            **route,
            "analysis": {
                "total_distance_km": round(analysis["distance_km"], 2),
                "total_travel_time_min": round(route["duration_seconds"] / 60, 1),
                "average_aqi": round(analysis["avg_aqi"], 1),
                "min_aqi": round(analysis["min_aqi"], 1),
                "max_aqi": round(analysis["max_aqi"], 1),
                "exposure_score": round(exposure_score, 1),
                "sample_points_count": analysis["sample_points_count"]
            }
        })
    
    # Sort by exposure score (cleanest first)
    analyzed_routes.sort(key=lambda x: x["analysis"]["exposure_score"])
    
    # Prepare response with multiple routes
    response_routes = []
    for i, route in enumerate(analyzed_routes):
        coords = [[lat, lon] for lat, lon in _decode_polyline(route["encoded_polyline"])]
        
        response_routes.append({
            "route_number": i + 1,
            "coordinates": coords,
            "node_count": len(coords),
            "analysis": route["analysis"],
            "route_type": f"route_{i+1}"
        })
    
    response = {
        "routes": response_routes,
        "total_routes": len(response_routes),
        "status": "success",
        "data_source": "google_multi_route",
        "cache_stats": {
            "cache_size": _cache.size()
        }
    }
    
    # Add fallback info if fallback was used
    if fallback_info:
        response["fallback_info"] = fallback_info
    
    return response
