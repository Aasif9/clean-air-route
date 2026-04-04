import time
from threading import Lock

class AQICache:
    """
    TTL cache for Google Air Quality API responses.
    Key = (lat rounded to 3dp, lon rounded to 3dp) => ~111m grid cell.
    TTL = 300 seconds (5 minutes).
    """
    def __init__(self, ttl_seconds=300):
        self._store = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def _make_key(self, lat, lon):
        return (round(lat, 3), round(lon, 3))

    def get(self, lat, lon):
        key = self._make_key(lat, lon)
        with self._lock:
            entry = self._store.get(key)
            if entry and (time.time() - entry["ts"]) < self._ttl:
                return entry["aqi"]
        return None

    def set(self, lat, lon, aqi):
        key = self._make_key(lat, lon)
        with self._lock:
            self._store[key] = {"aqi": aqi, "ts": time.time()}

    def size(self):
        return len(self._store)
