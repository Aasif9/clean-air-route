// Map Module
class AQIMap {
    constructor(containerId = 'map') {
        this.container = containerId;
        this.map = null;
        this.markers = {
            start: null,
            end: null,
            stations: [],
            routes: {
                clean: null,
                fast: null,
                alternatives: []
            }
        };
        
        // Kolkata bounds
        this.kolkataBounds = [
            [22.505, 88.296],  // Southwest
            [22.640, 88.431]   // Northeast
        ];
        
        this.init();
    }
 
    init() {
        // Initialize Leaflet map
        this.map = L.map(this.container).fitBounds(this.kolkataBounds);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add click handler
        this.map.on('click', (e) => this.handleMapClick(e));
        
        console.log('Map initialized');
    }
 
    handleMapClick(event) {
        const { lat, lng } = event.latlng;
        
        // Emit custom event for app to handle - use 'lon' to match working pattern
        const mapClickEvent = new CustomEvent('mapClick', {
            detail: { lat, lon: lng }
        });
        document.dispatchEvent(mapClickEvent);
    }
 
    addStartMarker(lat, lon) {
        if (this.markers.start) {
            this.map.removeLayer(this.markers.start);
        }
        
        this.markers.start = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'custom-marker start-marker',
                html: '<i class="fas fa-play"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(this.map);
        
        this.markers.start.bindPopup('Start Point').openPopup();
    }
 
    addEndMarker(lat, lon) {
        if (this.markers.end) {
            this.map.removeLayer(this.markers.end);
        }
        
        this.markers.end = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'custom-marker end-marker',
                html: '<i class="fas fa-flag-checkered"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            })
        }).addTo(this.map);
        
        this.markers.end.bindPopup('End Point').openPopup();
    }
 
    addAQIStations(stations) {
        // Clear existing station markers
        this.clearStationMarkers();
        
        stations.forEach(station => {
            const color = Utils.getAQIColor(station.aqi);
            const category = Utils.getAQICategory(station.aqi);
            
            const marker = L.circleMarker([station.lat, station.lon], {
                radius: 8,
                fillColor: color,
                color: '#fff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8,
                className: `aqi-station ${category}` 
            }).addTo(this.map);
            
            marker.bindPopup(`
                <div class="station-popup">
                    <h4>${station.name}</h4>
                    <p><strong>AQI:</strong> ${station.aqi}</p>
                    <p><strong>Category:</strong> ${Utils.getAQIDescription(station.aqi)}</p>
                    <p><strong>Location:</strong> ${Utils.formatCoordinates(station.lat, station.lon)}</p>
                </div>
            `);
            
            this.markers.stations.push(marker);
        });
    }
 
    drawRoute(routeData, type, customColor = null) {
        const coordinates = routeData.coordinates.map(coord => [coord[0], coord[1]]);
        
        // Use custom color if provided, otherwise use default colors
        let color;
        if (customColor) {
            color = customColor;
        } else {
            color = type === 'clean' ? '#2ecc71' : '#e74c3c';
        }
        
        const weight = 4;
        const opacity = 0.8;
        
        const polyline = L.polyline(coordinates, {
            color: color,
            weight: weight,
            opacity: opacity,
            smoothFactor: 1
        }).addTo(this.map);
        
        // Enhanced popup with detailed information
        const analysis = routeData.analysis;
        const popupContent = `
            <div class="route-popup">
                <h4>${type === 'clean' ? '🌱 Clean Route' : type === 'fast' ? '🚀 Fast Route' : '🛣️ Route'}</h4>
                <div class="route-stats">
                    <p><strong>📏 Distance:</strong> ${Utils.formatDistance(analysis.total_distance_km)}</p>
                    <p><strong>⏱️ Time:</strong> ${analysis.total_travel_time_min} min</p>
                    <p><strong>💨 Avg AQI:</strong> ${analysis.average_aqi.toFixed(1)}</p>
                    <p><strong>📊 AQI Range:</strong> ${analysis.min_aqi.toFixed(1)} - ${analysis.max_aqi.toFixed(1)}</p>
                    <p><strong>⚡ Exposure Score:</strong> ${analysis.exposure_score.toFixed(0)}</p>
                    <p><strong>📍 Sample Points:</strong> ${analysis.sample_points_count}</p>
                </div>
            </div>
        `;
        
        polyline.bindPopup(popupContent);
        
        // Add hover tooltip with quick info
        polyline.bindTooltip(`
            <div class="route-tooltip">
                <strong>${type === 'clean' ? 'Clean' : type === 'fast' ? 'Fast' : 'Route'}</strong><br>
                ${Utils.formatDistance(analysis.total_distance_km)} • AQI ${analysis.average_aqi.toFixed(1)}
            </div>
        `, {
            permanent: false,
            direction: 'center',
            className: 'route-tooltip',
            offset: [0, -10]
        });
        
        // Add hover effects
        polyline.on('mouseover', function(e) {
            this.setStyle({
                weight: weight + 2,
                opacity: 1
            });
        });
        
        polyline.on('mouseout', function(e) {
            this.setStyle({
                weight: weight,
                opacity: opacity
            });
        });
        
        // Store route with type
        if (!this.markers.routes[type]) {
            this.markers.routes[type] = [];
        }
        this.markers.routes[type].push(polyline);
        
        return polyline;
    }

    drawAlternativeRoutes(alternativeRoutes) {
        // Clear existing alternative routes
        this.clearAlternativeRoutes();
        
        const colors = ['#9b59b6', '#f39c12', '#1abc9c', '#e67e22', '#34495e'];
        
        alternativeRoutes.forEach((routeData, index) => {
            const coordinates = routeData.coordinates.map(coord => [coord[0], coord[1]]);
            const color = colors[index % colors.length];
            
            const polyline = L.polyline(coordinates, {
                color: color,
                weight: 3,
                opacity: 0.6,
                smoothFactor: 1,
                dashArray: '10, 5'
            }).addTo(this.map);
            
            // Enhanced popup for alternative routes
            const analysis = routeData.analysis;
            const popupContent = `
                <div class="route-popup">
                    <h4>🛣️ Alternative Route ${index + 1}</h4>
                    <div class="route-stats">
                        <p><strong>📏 Distance:</strong> ${Utils.formatDistance(analysis.total_distance_km)}</p>
                        <p><strong>⏱️ Time:</strong> ${analysis.total_travel_time_min} min</p>
                        <p><strong>💨 Avg AQI:</strong> ${analysis.average_aqi.toFixed(1)}</p>
                        <p><strong>📊 AQI Range:</strong> ${analysis.min_aqi.toFixed(1)} - ${analysis.max_aqi.toFixed(1)}</p>
                        <p><strong>⚡ Exposure Score:</strong> ${analysis.exposure_score.toFixed(0)}</p>
                        <p><strong>📍 Sample Points:</strong> ${analysis.sample_points_count}</p>
                    </div>
                </div>
            `;
            
            polyline.bindPopup(popupContent);
            
            // Add hover tooltip
            polyline.bindTooltip(`
                <div class="route-tooltip">
                    <strong>Alt ${index + 1}</strong><br>
                    ${Utils.formatDistance(analysis.total_distance_km)} • AQI ${analysis.average_aqi.toFixed(1)}
                </div>
            `, {
                permanent: false,
                direction: 'center',
                className: 'route-tooltip',
                offset: [0, -10]
            });
            
            // Add hover effects
            polyline.on('mouseover', function(e) {
                this.setStyle({
                    weight: 5,
                    opacity: 0.9
                });
            });
            
            polyline.on('mouseout', function(e) {
                this.setStyle({
                    weight: 3,
                    opacity: 0.6
                });
            });
            
            this.markers.routes.alternatives.push(polyline);
        });
    }

    clearAlternativeRoutes() {
        this.markers.routes.alternatives.forEach(route => {
            this.map.removeLayer(route);
        });
        this.markers.routes.alternatives = [];
    }
 
    fitRoutes() {
        const bounds = L.latLngBounds();
        
        // Add start and end markers
        if (this.markers.start) bounds.extend(this.markers.start.getLatLng());
        if (this.markers.end) bounds.extend(this.markers.end.getLatLng());
        
        // Add route bounds
        Object.values(this.markers.routes).forEach(route => {
            if (route) bounds.extend(route.getBounds());
        });
        
        if (bounds.isValid()) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }
 
    highlightRoute(routeIndex) {
        // Reset all routes
        Object.values(this.markers.routes).forEach(routeGroup => {
            if (Array.isArray(routeGroup)) {
                routeGroup.forEach(route => {
                    if (route) {
                        route.setStyle({
                            weight: 4,
                            opacity: 0.8
                        });
                    }
                });
            } else if (routeGroup) {
                routeGroup.setStyle({
                    weight: 4,
                    opacity: 0.8
                });
            }
        });
        
        // Find and highlight the selected route
        let routeCount = 0;
        Object.values(this.markers.routes).forEach(routeGroup => {
            if (Array.isArray(routeGroup)) {
                routeGroup.forEach(route => {
                    if (route && routeCount === routeIndex) {
                        route.setStyle({
                            weight: 7,
                            opacity: 1.0
                        });
                    }
                    routeCount++;
                });
            } else if (routeGroup) {
                if (routeCount === routeIndex) {
                    routeGroup.setStyle({
                        weight: 7,
                        opacity: 1.0
                    });
                }
                routeCount++;
            }
        });
    }
 
    clearRoutes() {
        Object.values(this.markers.routes).forEach(routeGroup => {
            if (Array.isArray(routeGroup)) {
                routeGroup.forEach(route => {
                    if (route) this.map.removeLayer(route);
                });
            } else if (routeGroup) {
                this.map.removeLayer(routeGroup);
            }
        });
        this.markers.routes = { clean: null, fast: null, alternatives: [] };
    }
 
    clearStationMarkers() {
        this.markers.stations.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers.stations = [];
    }
 
    clearMarkers() {
        if (this.markers.start) {
            this.map.removeLayer(this.markers.start);
            this.markers.start = null;
        }
        
        if (this.markers.end) {
            this.map.removeLayer(this.markers.end);
            this.markers.end = null;
        }
        
        this.clearRoutes();
    }
 
    centerMap() {
        this.map.fitBounds(this.kolkataBounds);
    }
 
    toggleFullscreen() {
        const mapContainer = document.getElementById('map');
        
        if (!document.fullscreenElement) {
            mapContainer.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }
}
 
// Export for use in other modules
window.AQIMap = AQIMap;
