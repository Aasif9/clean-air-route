class AQIMap {
    constructor(containerId = 'map') {
        this.containerId = containerId;
        this.map = null;
        this.startMarker = null;
        this.endMarker = null;
        this.drawnRoutes = []; // FIX: flat array instead of nested object
        this.kolkataBounds = [[22.505, 88.296], [22.640, 88.431]];
        this.ROUTE_COLORS = ['#2ecc71', '#e74c3c', '#9b59b6', '#f39c12', '#1abc9c'];
        this.init();
    }

    init() {
        this.map = L.map(this.containerId).fitBounds(this.kolkataBounds);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        this.map.on('click', (e) => {
            document.dispatchEvent(new CustomEvent('mapClick', {
                detail: { lat: e.latlng.lat, lon: e.latlng.lng } // FIX: use lon not lng
            }));
        });
    }

    setStartMarker(lat, lon) {
        if (this.startMarker) this.map.removeLayer(this.startMarker);
        this.startMarker = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'custom-marker',
                html: '<div style="background:#2ecc71;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4)"></div>',
                iconSize: [22, 22], iconAnchor: [11, 11]
            })
        }).addTo(this.map).bindPopup('Start point');
    }

    setEndMarker(lat, lon) {
        if (this.endMarker) this.map.removeLayer(this.endMarker);
        this.endMarker = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'custom-marker',
                html: '<div style="background:#e74c3c;width:16px;height:16px;border-radius:50%;border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.4)"></div>',
                iconSize: [22, 22], iconAnchor: [11, 11]
            })
        }).addTo(this.map).bindPopup('End point');
    }

    drawAllRoutes(routes) {
        this.clearRoutes();
        routes.forEach((route, index) => {
            const color = this.ROUTE_COLORS[index % this.ROUTE_COLORS.length];
            const isFirst = index === 0;
            const coords = route.coordinates.map(c => [c[0], c[1]]);
            const label = index === 0 ? 'Cleanest' : index === 1 ? 'Fastest' : `Alternative ${index}`;

            const pl = L.polyline(coords, {
                color: color,
                weight: isFirst ? 6 : 4,
                opacity: isFirst ? 1.0 : 0.65,
                smoothFactor: 1
            }).addTo(this.map);

            const a = route.analysis;
            pl.bindPopup(`
                <div style="font-family:sans-serif;min-width:160px">
                    <strong style="color:${color}">${label} Route</strong><br>
                    <table style="margin-top:6px;font-size:13px;width:100%">
                        <tr><td>Distance</td><td><b>${a.total_distance_km} km</b></td></tr>
                        <tr><td>Time</td><td><b>${a.total_travel_time_min} min</b></td></tr>
                        <tr><td>Avg AQI</td><td><b>${a.average_aqi}</b></td></tr>
                        <tr><td>AQI range</td><td><b>${a.min_aqi} – ${a.max_aqi}</b></td></tr>
                        <tr><td>Exposure</td><td><b>${a.exposure_score}</b></td></tr>
                    </table>
                </div>
            `);
            pl.bindTooltip(`<b>${label}</b> · ${a.total_distance_km}km · AQI ${a.average_aqi}`, {
                sticky: true, className: 'route-tooltip'
            });

            pl.on('mouseover', function() { this.setStyle({ weight: isFirst ? 8 : 6, opacity: 1 }); });
            pl.on('mouseout', function() { this.setStyle({ weight: isFirst ? 6 : 4, opacity: isFirst ? 1 : 0.65 }); });

            this.drawnRoutes.push(pl);
        });

        this.fitAllRoutes();
    }

    highlightRoute(index) {
        this.drawnRoutes.forEach((pl, i) => {
            const isSelected = i === index;
            pl.setStyle({
                weight: isSelected ? 8 : 3,
                opacity: isSelected ? 1.0 : 0.35
            });
            if (isSelected) pl.bringToFront();
        });
    }

    fitAllRoutes() {
        const bounds = L.latLngBounds();
        if (this.startMarker) bounds.extend(this.startMarker.getLatLng());
        if (this.endMarker) bounds.extend(this.endMarker.getLatLng());
        this.drawnRoutes.forEach(pl => bounds.extend(pl.getBounds()));
        if (bounds.isValid()) this.map.fitBounds(bounds, { padding: [50, 50] });
    }

    clearRoutes() {
        this.drawnRoutes.forEach(pl => this.map.removeLayer(pl));
        this.drawnRoutes = [];
    }

    clearAll() {
        this.clearRoutes();
        if (this.startMarker) { this.map.removeLayer(this.startMarker); this.startMarker = null; }
        if (this.endMarker) { this.map.removeLayer(this.endMarker); this.endMarker = null; }
    }

    centerMap() { this.map.fitBounds(this.kolkataBounds); }

    toggleFullscreen() {
        const el = document.getElementById(this.containerId);
        if (!document.fullscreenElement) el.requestFullscreen();
        else document.exitFullscreen();
    }
}

window.AQIMap = AQIMap;
