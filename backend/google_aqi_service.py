import os
import math
import requests
import polyline
from aqi_cache import AQICache

ROUTES_API_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
AQI_API_URL = "https://airquality.googleapis.com/v1/currentConditions:lookup"
API_KEY = os.getenv("Maps_API_KEY", "YOUR_KEY_HERE")

_cache = AQICache(ttl_seconds=300)


def _decode_polyline(encoded):
    """Decode Google encoded polyline to list of (lat, lon) tuples."""
    return polyline.decode(encoded)


def _sample_equidistant(coords, n=6):
    """
    Pick n equidistant points from a list of (lat, lon) coords.
    Returns list of (lat, lon).
    """
    if len(coords) <= n:
        return coords
    step = (len(coords) - 1) / (n - 1)
    return [coords[round(i * step)] for i in range(n)]


def _fetch_aqi(lat, lon):
    """
    Fetch UAQI from Google Air Quality API for a single point.
    Returns float AQI or 50 (neutral fallback) on failure.
    """
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
        print(f"[AQI API fallback] lat={lat:.4f} lon={lon:.4f} error={e}")
        return 50.0


def _sample_route_aqi(encoded_polyline, n=6):
    """
    Sample AQI at n equidistant points along route.
    Returns average AQI as float.
    """
    coords = _decode_polyline(encoded_polyline)
    sample_points = _sample_equidistant(coords, n)
    aqi_values = [_fetch_aqi(lat, lon) for lat, lon in sample_points]
    return sum(aqi_values) / len(aqi_values)


def _exposure_score(duration_seconds, avg_aqi):
    """
    Exponential exposure score.
    exp(aqi/75) amplifies small AQI differences significantly:
      AQI 50 → multiplier 1.95
      AQI 55 → multiplier 2.07   (+6% vs AQI 50)
      AQI 100 → multiplier 3.79  (+94% vs AQI 50)
    Compared to linear (1 + aqi/100):
      AQI 50 → 1.50, AQI 55 → 1.55 (only 3% diff)
    """
    return duration_seconds * math.exp(avg_aqi / 75)


def _fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Call Google Routes API v2. Returns list of route dicts with
    encoded_polyline, duration_seconds, distance_meters.
    Falls back to empty list on failure.
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
            },
            timeout=10,
        )
        resp.raise_for_status()
        raw_routes = resp.json().get("routes", [])

        result = []
        for r in raw_routes:
            dur_str = r.get("duration", "0s")
            dur_sec = int(dur_str.replace("s", ""))
            result.append({
                "encoded_polyline": r["polyline"]["encodedPolyline"],
                "duration_seconds": dur_sec,
                "distance_meters": r.get("distanceMeters", 0),
            })
        return result

    except Exception as e:
        print(f"[Routes API error] {e}")
        return []


def _route_to_coords(encoded_polyline):
    """Decode polyline to [[lat, lon], ...] for frontend."""
    return [[lat, lon] for lat, lon in _decode_polyline(encoded_polyline)]


def find_best_routes(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Main entry point. Returns dict with fastest + cleanest route
    and comparison metrics. Compatible with existing frontend response format.
    """
    routes = _fetch_routes(origin_lat, origin_lon, dest_lat, dest_lon)

    if not routes:
        return {"error": "No routes returned from Google Routes API"}

    # Score every alternative
    scored = []
    for r in routes:
        avg_aqi = _sample_route_aqi(r["encoded_polyline"], n=6)
        score = _exposure_score(r["duration_seconds"], avg_aqi)
        scored.append({**r, "avg_aqi": avg_aqi, "score": score})

    fastest = min(scored, key=lambda x: x["duration_seconds"])
    cleanest = min(scored, key=lambda x: x["score"])

    def build_analysis(r):
        return {
            "total_distance_km": round(r["distance_meters"] / 1000, 2),
            "total_travel_time_min": round(r["duration_seconds"] / 60, 1),
            "average_aqi": round(r["avg_aqi"], 1),
            "exposure_score": round(r["score"], 1),
        }

    fast_a = build_analysis(fastest)
    clean_a = build_analysis(cleanest)

    dist_diff = fast_a["total_distance_km"]
    dist_increase_pct = (
        round((clean_a["total_distance_km"] - fast_a["total_distance_km"])
              / fast_a["total_distance_km"] * 100, 1)
        if dist_diff > 0 else 0
    )
    aqi_improvement = round(fast_a["average_aqi"] - clean_a["average_aqi"], 1)
    aqi_improvement_pct = (
        round(aqi_improvement / fast_a["average_aqi"] * 100, 1)
        if fast_a["average_aqi"] > 0 else 0
    )

    return {
        "fast_route": {
            "coordinates": _route_to_coords(fastest["encoded_polyline"]),
            "node_count": len(_decode_polyline(fastest["encoded_polyline"])),
            "analysis": fast_a,
        },
        "clean_route": {
            "coordinates": _route_to_coords(cleanest["encoded_polyline"]),
            "node_count": len(_decode_polyline(cleanest["encoded_polyline"])),
            "analysis": clean_a,
        },
        "comparison": {
            "distance_increase_percent": dist_increase_pct,
            "aqi_improvement": aqi_improvement,
            "aqi_improvement_pct": aqi_improvement_pct,
        },
        "status": "success",
        "data_source": "google_live",
    }
