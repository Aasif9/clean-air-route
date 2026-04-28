"""
Route Fallback System
Provides reliable route generation with multiple fallback strategies.
Always returns a route, never fails.
"""

import math
import polyline
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("Maps_API_KEY", "AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw")

# Simple in-memory cache (can be replaced with Redis/DB)
_route_cache = []

CONFIDENCE_SCORES = {
    "routes_api": 1.0,
    "directions_api": 0.9,
    "cache_hit": 0.7,
    "snapped_route": 0.6,
    "expanded_search": 0.5,
    "closest_reachable": 0.45,
    "fallback": 0.4
}


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000  # Earth radius in meters
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def validate_coordinates(lat: float, lon: float) -> Tuple[bool, Optional[str]]:
    """
    Validate coordinate point with comprehensive checks.
    Returns (is_valid, error_message)
    """
    # Check for None or invalid types
    if lat is None or lon is None:
        return False, "Coordinates cannot be None"
    
    # Check range
    if not (-90 <= lat <= 90):
        return False, f"Latitude {lat} out of valid range [-90, 90]"
    
    if not (-180 <= lon <= 180):
        return False, f"Longitude {lon} out of valid range [-180, 180]"
    
    # Check for null island (coordinates near 0,0)
    if abs(lat) < 0.01 and abs(lon) < 0.01:
        return False, "Coordinates appear to be null island (0,0)"
    
    # Check for unrealistic coordinates (very high precision suggests error)
    if abs(lat) > 89.9 or abs(lon) > 179.9:
        return False, "Coordinates too close to poles or date line"
    
    return True, None


def is_likely_in_ocean(lat: float, lon: float) -> bool:
    """
    Simple heuristic to detect if coordinates are likely in ocean.
    This is a basic check - for production, use a proper land mask.
    """
    # Known ocean regions (very rough approximation)
    # For Kolkata area, this is less relevant, but included for robustness
    
    # Check if far from any known land (simplified)
    # In production, use a proper land mask database or API
    return False  # Disabled for now - requires land mask data


def _encode_polyline(coords: list) -> str:
    """Encode coordinates to polyline string."""
    return polyline.encode(coords)


def _is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_m: float = 500) -> bool:
    """Check if two points are within specified radius."""
    return _haversine_distance(lat1, lon1, lat2, lon2) <= radius_m


def snap_to_nearest_road(lat: float, lon: float) -> Optional[Tuple[float, float]]:
    """
    Snap coordinate to nearest road using Google Roads API.
    Returns (snapped_lat, snapped_lon) or None if failed.
    """
    try:
        url = "https://roads.googleapis.com/v1/nearestRoads"
        params = {
            "points": f"{lat},{lon}",
            "key": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=1)
        response.raise_for_status()
        
        data = response.json()
        if data.get("snappedPoints"):
            snapped = data["snappedPoints"][0]
            location = snapped.get("location")
            if location:
                return (location["latitude"], location["longitude"])
        
        return None
    except Exception as e:
        print(f"[Fallback] Roads API snapping failed: {e}")
        return None


def try_routes_api(start_lat: float, start_lon: float, end_lat: float, end_lon: float, timeout_ms: int = 800) -> Optional[Dict]:
    """
    Primary: Try Google Routes API with timeout.
    Returns route data or None if failed.
    """
    try:
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
        }
        payload = {
            "origin": {"location": {"latLng": {"latitude": start_lat, "longitude": start_lon}}},
            "destination": {"location": {"latLng": {"latitude": end_lat, "longitude": end_lon}}},
            "travelMode": "DRIVE",
            "computeAlternativeRoutes": True,
            "routingPreference": "TRAFFIC_AWARE",
        }
        
        response = requests.post(
            url,
            params={"key": API_KEY},
            headers=headers,
            json=payload,
            timeout=timeout_ms / 1000
        )
        response.raise_for_status()
        
        routes = response.json().get("routes", [])
        if not routes:
            return None
        
        route = routes[0]
        return {
            "polyline": route["polyline"]["encodedPolyline"],
            "distance": route.get("distanceMeters", 0),
            "duration": int(route.get("duration", "0s").replace("s", "")),
            "source": "routes_api"
        }
    except Exception as e:
        print(f"[Fallback] Routes API failed: {e}")
        return None


def try_directions_api(start_lat: float, start_lon: float, end_lat: float, end_lon: float, timeout_ms: int = 1000) -> Optional[Dict]:
    """
    Secondary: Try Google Directions API with alternatives.
    Returns route data or None if failed.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{start_lat},{start_lon}",
            "destination": f"{end_lat},{end_lon}",
            "mode": "driving",
            "alternatives": "true",
            "key": API_KEY
        }
        
        response = requests.get(url, params=params, timeout=timeout_ms / 1000)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") != "OK" or not data.get("routes"):
            return None
        
        route = data["routes"][0]
        leg = route["legs"][0]
        
        # Convert overview_polyline to encoded format
        encoded_polyline = route.get("overview_polyline", {}).get("points", "")
        
        return {
            "polyline": encoded_polyline,
            "distance": leg.get("distance", {}).get("value", 0),
            "duration": leg.get("duration", {}).get("value", 0),
            "source": "directions_api"
        }
    except Exception as e:
        print(f"[Fallback] Directions API failed: {e}")
        return None


def cache_route(route_data: Dict, start_lat: float, start_lon: float, end_lat: float, end_lon: float):
    """Store route in cache."""
    cache_entry = {
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon,
        "polyline": route_data["polyline"],
        "distance": route_data["distance"],
        "duration": route_data["duration"],
        "timestamp": datetime.now()
    }
    _route_cache.append(cache_entry)
    
    # Clean old entries (keep last 1000)
    if len(_route_cache) > 1000:
        _route_cache.pop(0)


def lookup_cached_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, radius_m: float = 500) -> Optional[Dict]:
    """
    Cache Layer: Search for similar routes within radius.
    Returns cached route or None.
    """
    # Clean expired entries (older than 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    global _route_cache
    _route_cache = [r for r in _route_cache if r["timestamp"] > cutoff]
    
    for entry in _route_cache:
        if (_is_within_radius(start_lat, start_lon, entry["start_lat"], entry["start_lon"], radius_m) and
            _is_within_radius(end_lat, end_lon, entry["end_lat"], entry["end_lon"], radius_m)):
            return {
                "polyline": entry["polyline"],
                "distance": entry["distance"],
                "duration": entry["duration"],
                "source": "cache_hit"
            }
    
    return None


def fallback_straight_line(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Dict:
    """
    Final Fallback: Generate straight-line route.
    NEVER fails - always returns a route.
    """
    # Calculate distance
    distance = _haversine_distance(start_lat, start_lon, end_lat, end_lon)
    
    # Estimate duration (assuming 30 km/h average speed in urban areas)
    duration = int((distance / 1000) / 30 * 3600)  # seconds
    
    # Create simple polyline with start and end points
    coords = [[start_lat, start_lon], [end_lat, end_lon]]
    encoded_polyline = _encode_polyline(coords)
    
    return {
        "polyline": encoded_polyline,
        "distance": distance,
        "duration": duration,
        "source": "fallback"
    }


def try_with_snapped_coordinates(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[Dict]:
    """
    Try routing with snapped coordinates using Google Roads API.
    Returns route data or None if failed.
    """
    # Snap start point
    snapped_start = snap_to_nearest_road(start_lat, start_lon)
    snapped_end = snap_to_nearest_road(end_lat, end_lon)
    
    if not snapped_start or not snapped_end:
        return None
    
    # Try routing with snapped coordinates
    result = try_routes_api(snapped_start[0], snapped_start[1], snapped_end[0], snapped_end[1])
    if result:
        result["source"] = "snapped_route"
        result["snapped_start"] = snapped_start
        result["snapped_end"] = snapped_end
        return result
    
    return None


def try_with_expanded_search(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Optional[Dict]:
    """
    Try routing with expanded search area by creating intermediate waypoints.
    Returns route data or None if failed.
    """
    distance = _haversine_distance(start_lat, start_lon, end_lat, end_lon)
    
    # For long distances, try breaking into segments
    if distance > 50000:  # > 50km
        # Create midpoint
        mid_lat = (start_lat + end_lat) / 2
        mid_lon = (start_lon + end_lon) / 2
        
        # Try routing to midpoint first
        result1 = try_routes_api(start_lat, start_lon, mid_lat, mid_lon)
        if not result1:
            return None
        
        # Then from midpoint to end
        result2 = try_routes_api(mid_lat, mid_lon, end_lat, end_lon)
        if not result2:
            return None
        
        # Combine routes (simplified - just return first segment for now)
        result1["source"] = "expanded_search"
        result1["distance"] = result1["distance"] + result2["distance"]
        result1["duration"] = result1["duration"] + result2["duration"]
        return result1
    
    return None


def get_route_with_fallback(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> Tuple[Dict, str]:
    """
    Main wrapper function with enhanced fallback orchestration.
    
    Args:
        start_lat, start_lon: Starting coordinates
        end_lat, end_lon: Ending coordinates
    
    Returns:
        Tuple of (route_data, source_label)
        route_data: Dict with polyline, distance, duration, source, confidence
        source_label: String indicating which method was used
    """
    # Validate coordinates
    for lat, lon, name in [(start_lat, start_lon, "start"), (end_lat, end_lon, "end")]:
        is_valid, error = validate_coordinates(lat, lon)
        if not is_valid:
            print(f"[Fallback] Invalid {name} coordinates: {error}")
            result = fallback_straight_line(start_lat, start_lon, end_lat, end_lon)
            result["confidence"] = CONFIDENCE_SCORES["fallback"]
            result["validation_error"] = error
            return result, "fallback"
    
    # Check for very short routes
    distance = _haversine_distance(start_lat, start_lon, end_lat, end_lon)
    if distance < 100:
        print("[Fallback] Very short route, using straight-line fallback")
        result = fallback_straight_line(start_lat, start_lon, end_lat, end_lon)
        result["confidence"] = CONFIDENCE_SCORES["fallback"]
        return result, "fallback"
    
    # Try 1: Routes API (primary)
    print("[Fallback] Attempt 1: Routes API")
    result = try_routes_api(start_lat, start_lon, end_lat, end_lon)
    if result:
        cache_route(result, start_lat, start_lon, end_lat, end_lon)
        result["confidence"] = CONFIDENCE_SCORES["routes_api"]
        return result, "routes_api"
    
    # Try 2: Directions API (secondary)
    print("[Fallback] Attempt 2: Directions API")
    result = try_directions_api(start_lat, start_lon, end_lat, end_lon)
    if result:
        cache_route(result, start_lat, start_lon, end_lat, end_lon)
        result["confidence"] = CONFIDENCE_SCORES["directions_api"]
        return result, "directions_api"
    
    # Try 3: Snapped coordinates (using Roads API)
    print("[Fallback] Attempt 3: Snapped coordinates")
    result = try_with_snapped_coordinates(start_lat, start_lon, end_lat, end_lon)
    if result:
        cache_route(result, start_lat, start_lon, end_lat, end_lon)
        result["confidence"] = CONFIDENCE_SCORES["snapped_route"]
        return result, "snapped_route"
    
    # Try 4: Expanded search (for long distances)
    print("[Fallback] Attempt 4: Expanded search")
    result = try_with_expanded_search(start_lat, start_lon, end_lat, end_lon)
    if result:
        cache_route(result, start_lat, start_lon, end_lat, end_lon)
        result["confidence"] = CONFIDENCE_SCORES["expanded_search"]
        return result, "expanded_search"
    
    # Try 5: Cache lookup
    print("[Fallback] Attempt 5: Cache lookup")
    result = lookup_cached_route(start_lat, start_lon, end_lat, end_lon)
    if result:
        result["confidence"] = CONFIDENCE_SCORES["cache_hit"]
        return result, "cache_hit"
    
    # Try 6: Straight-line fallback (NEVER fails)
    print("[Fallback] Attempt 6: Straight-line fallback (final)")
    result = fallback_straight_line(start_lat, start_lon, end_lat, end_lon)
    result["confidence"] = CONFIDENCE_SCORES["fallback"]
    return result, "fallback"


def get_fallback_message(source: str, confidence: float) -> str:
    """
    Generate user-friendly message based on fallback source.
    """
    messages = {
        "routes_api": "Route calculated using primary routing service.",
        "directions_api": "Route calculated using alternative routing service.",
        "snapped_route": "Route calculated using snapped coordinates to nearest roads.",
        "expanded_search": "Route calculated using expanded search with intermediate waypoints.",
        "cache_hit": "Route retrieved from cache (similar recent route).",
        "fallback": "Approximate straight-line route. Narrow your search area or try different locations for better accuracy."
    }
    return messages.get(source, "Route calculated.")
