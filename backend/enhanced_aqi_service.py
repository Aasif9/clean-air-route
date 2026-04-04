import os
import math
import requests
import polyline
import time
from functools import lru_cache
from aqi_cache import AQICache

ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
AQI_API_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"
API_KEY = os.getenv("Maps_API_KEY", "YOUR_KEY_HERE")

_cache = AQICache(ttl_seconds=600)  # 10 minutes cache


def _decode_polyline(encoded):
    """Decode Google encoded polyline to list of (lat, lon) tuples."""
    return polyline.decode(encoded)


def _calculate_polyline_distance(coords):
    """Calculate total distance of polyline in kilometers using Haversine formula."""
    total_distance = 0.0
    for i in range(len(coords) - 1):
        lat1, lon1 = coords[i]
        lat2, lon2 = coords[i + 1]
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        total_distance += R * c
    
    return total_distance


def _dynamic_sampling(coords, distance_km):
    """
    Dynamic spatial sampling based on route distance.
    - < 3km: Sample every 500m (4-6 points)
    - 3km - 15km: Sample every 1km (3-12 points)  
    - > 15km: Sample every 1.5km (max 15 points)
    """
    if distance_km < 3:
        step_size_km = 0.5  # 500m
    elif distance_km <= 15:
        step_size_km = 1.0  # 1km
    else:
        step_size_km = 1.5  # 1.5km
    
    # Calculate number of samples
    num_samples = min(int(distance_km / step_size_km) + 1, 15)
    
    # Ensure minimum samples for very short routes
    if distance_km < 1:
        num_samples = max(3, num_samples)
    
    if len(coords) <= num_samples:
        return coords
    
    # Calculate step indices
    step = (len(coords) - 1) / (num_samples - 1)
    sampled_coords = []
    
    for i in range(num_samples):
        idx = min(round(i * step), len(coords) - 1)
        sampled_coords.append(coords[idx])
    
    print(f"[Sampling] Route distance: {distance_km:.1f}km, step: {step_size_km}km, samples: {len(sampled_coords)}")
    return sampled_coords


def _round_coordinates(lat, lon, decimals=4):
    """Round coordinates to 4 decimal places (~11m precision) for cache optimization."""
    return round(lat, decimals), round(lon, decimals)


@lru_cache(maxsize=1000)
def _fetch_aqi_cached(lat_rounded, lon_rounded):
    """
    Fetch UAQI from Google Air Quality API with coordinate rounding.
    Uses LRU cache for additional in-memory caching.
    """
    try:
        resp = requests.post(
            AQI_API_URL,
            params={"key": API_KEY},
            json={
                "location": {"latitude": lat_rounded, "longitude": lon_rounded},
                "universalAqi": True,
                "extraComputations": ["LOCAL_AQI"],
            },
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        aqi = data["indexes"][0]["aqi"]
        return float(aqi)
    except Exception as e:
        print(f"[AQI API fallback] lat={lat_rounded:.4f} lon={lon_rounded:.4f} error={e}")
        return 50.0


def _fetch_aqi(lat, lon):
    """
    Fetch AQI with coordinate rounding and multi-level caching.
    """
    # Check TTL cache first
    cached = _cache.get(lat, lon)
    if cached is not None:
        return cached
    
    # Round coordinates for cache optimization
    lat_rounded, lon_rounded = _round_coordinates(lat, lon)
    
    # Use LRU cache
    aqi = _fetch_aqi_cached(lat_rounded, lon_rounded)
    
    # Store in TTL cache with original coordinates
    _cache.set(lat, lon, aqi)
    
    return aqi


def _sample_route_aqi(encoded_polyline):
    """
    Sample AQI along route using dynamic spatial sampling.
    Returns average AQI and sample points used.
    """
    coords = _decode_polyline(encoded_polyline)
    distance_km = _calculate_polyline_distance(coords)
    
    # Apply dynamic sampling
    sample_coords = _dynamic_sampling(coords, distance_km)
    
    print(f"[Sampling] Route distance: {distance_km:.1f}km, samples: {len(sample_coords)}")
    
    # Fetch AQI for each sample point
    aqi_values = []
    for lat, lon in sample_coords:
        aqi = _fetch_aqi(lat, lon)
        aqi_values.append(aqi)
        time.sleep(0.1)  # Small delay to avoid rate limiting
    
    avg_aqi = sum(aqi_values) / len(aqi_values)
    return avg_aqi, sample_coords, aqi_values


def _exposure_score(duration_seconds, avg_aqi):
    """
    Enhanced exponential exposure score.
    Score = duration × 1.05^AQI
    This amplifies AQI differences more aggressively.
    """
    return duration_seconds * (1.05 ** avg_aqi)


def _fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Call Google Routes API v2 with multiple alternatives.
    Returns up to 3 route options.
    """
    try:
        resp = requests.post(
            ROUTES_API_URL,
            params={"key": API_KEY},
            headers={
                "X-Goog-FieldMask": (
                    "routes.duration,routes.distanceMeters,"
                    "routes.polyline.encodedPolyline"
                )
            },
            json={
                "origin": {
                    "location": {"latLng": {"latitude": origin_lat, "longitude": origin_lon}}
                },
                "destination": {
                    "location": {"latLng": {"latitude": dest_lat, "longitude": dest_lon}}
                },
                "travelMode": "DRIVE",
                "computeAlternativeRoutes": True,
                "routingPreference": "TRAFFIC_AWARE",
                "routeModifiers": {
                    "avoidTolls": False,
                    "avoidHighways": False,
                    "avoidFerries": True
                }
            },
            timeout=15,
        )
        resp.raise_for_status()
        raw_routes = resp.json().get("routes", [])

        # Process up to 3 routes
        result = []
        for i, r in enumerate(raw_routes[:3]):
            dur_str = r.get("duration", "0s")
            dur_sec = int(dur_str.replace("s", ""))
            
            result.append({
                "route_id": i,
                "encoded_polyline": r["polyline"]["encodedPolyline"],
                "duration_seconds": dur_sec,
                "distance_meters": r.get("distanceMeters", 0),
            })
        
        print(f"[Routes API] Found {len(result)} alternative routes")
        return result

    except Exception as e:
        print(f"[Routes API error] {e}")
        return []


def _route_to_coords(encoded_polyline):
    """Decode polyline to [[lat, lon], ...] for frontend."""
    return [[lat, lon] for lat, lon in _decode_polyline(encoded_polyline)]


def find_best_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Enhanced route finding with 3 alternatives and improved scoring.
    Returns fastest and cleanest routes with detailed analysis.
    """
    routes = _fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon)

    if not routes:
        return {"error": "No routes returned from Google Routes API"}

    if len(routes) < 2:
        return {"error": "Need at least 2 alternative routes for comparison"}

    # Score each route with enhanced AQI sampling
    scored_routes = []
    for route in routes:
        avg_aqi, sample_coords, aqi_values = _sample_route_aqi(route["encoded_polyline"])
        score = _exposure_score(route["duration_seconds"], avg_aqi)
        
        scored_routes.append({
            **route,
            "avg_aqi": avg_aqi,
            "exposure_score": score,
            "sample_coords": sample_coords,
            "aqi_values": aqi_values
        })
    
    # Sort by different metrics
    fastest_route = min(scored_routes, key=lambda x: x["duration_seconds"])
    cleanest_route = min(scored_routes, key=lambda x: x["exposure_score"])
    
    # Build detailed analysis
    def build_analysis(route, route_type):
        return {
            "total_distance_km": round(route["distance_meters"] / 1000, 2),
            "total_travel_time_min": round(route["duration_seconds"] / 60, 1),
            "average_aqi": round(route["avg_aqi"], 1),
            "exposure_score": round(route["exposure_score"], 1),
            "route_type": route_type,
            "sample_points_count": len(route["sample_coords"]),
            "min_aqi": round(min(route["aqi_values"]), 1),
            "max_aqi": round(max(route["aqi_values"]), 1)
        }
    
    fast_analysis = build_analysis(fastest_route, "fastest")
    clean_analysis = build_analysis(cleanest_route, "cleanest")
    
    # Calculate comparison metrics
    dist_increase_pct = (
        round((clean_analysis["total_distance_km"] - fast_analysis["total_distance_km"])
              / fast_analysis["total_distance_km"] * 100, 1)
        if fast_analysis["total_distance_km"] > 0 else 0
    )
    
    aqi_improvement = round(fast_analysis["average_aqi"] - clean_analysis["average_aqi"], 1)
    aqi_improvement_pct = (
        round(aqi_improvement / fast_analysis["average_aqi"] * 100, 1)
        if fast_analysis["average_aqi"] > 0 else 0
    )
    
    exposure_reduction = round(
        (fast_analysis["exposure_score"] - clean_analysis["exposure_score"])
        / fast_analysis["exposure_score"] * 100, 1
    ) if fast_analysis["exposure_score"] > 0 else 0

    return {
        "fast_route": {
            "coordinates": _route_to_coords(fastest_route["encoded_polyline"]),
            "node_count": len(_decode_polyline(fastest_route["encoded_polyline"])),
            "analysis": fast_analysis,
            "sample_coords": fastest_route["sample_coords"],
            "aqi_values": fastest_route["aqi_values"]
        },
        "clean_route": {
            "coordinates": _route_to_coords(cleanest_route["encoded_polyline"]),
            "node_count": len(_decode_polyline(cleanest_route["encoded_polyline"])),
            "analysis": clean_analysis,
            "sample_coords": cleanest_route["sample_coords"],
            "aqi_values": cleanest_route["aqi_values"]
        },
        "additional_routes": [
            {
                "coordinates": _route_to_coords(route["encoded_polyline"]),
                "node_count": len(_decode_polyline(route["encoded_polyline"])),
                "analysis": build_analysis(route, f"alternative_{i}"),
                "sample_coords": route["sample_coords"],
                "aqi_values": route["aqi_values"]
            }
            for i, route in enumerate(scored_routes)
            if route["route_id"] != fastest_route["route_id"] and route["route_id"] != cleanest_route["route_id"]
        ],
        "comparison": {
            "distance_increase_percent": dist_increase_pct,
            "aqi_improvement": aqi_improvement,
            "aqi_improvement_pct": aqi_improvement_pct,
            "exposure_reduction_percent": exposure_reduction
        },
        "status": "success",
        "data_source": "google_live_enhanced",
        "cache_stats": {
            "cache_size": _cache.size(),
            "lru_cache_info": _fetch_aqi_cached.cache_info()
        }
    }
