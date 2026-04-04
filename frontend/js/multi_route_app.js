// Multi-Route Application Controller
class MultiRouteApp {
    constructor() {
        this.api = new AQIAPI();
        this.map = new AQIMap();
        this.currentRoutes = null;
        this.startPoint = null;
        this.endPoint = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updatePollutionDescription();
        this.checkBackendStatus();
    }

    setupEventListeners() {
        // Map click events
        document.addEventListener('mapClick', (e) => this.handleMapClick(e));
        
        // Button events
        document.getElementById('calculateBtn').addEventListener('click', () => this.calculateRoutes());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearAll());
        document.getElementById('centerBtn').addEventListener('click', () => this.map.centerMap());
        document.getElementById('fullscreenBtn').addEventListener('click', () => this.map.toggleFullscreen());
        
        // Route card events
        document.querySelectorAll('.route-select-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectRoute(e.target.dataset.route));
        });
        
        // Pollution slider
        document.getElementById('pollutionSlider').addEventListener('input', () => {
            this.updatePollutionDescription();
        });
    }

    async handleMapClick(event) {
        const { lat, lng } = event.detail;
        
        if (!this.startPoint) {
            this.setStartPoint(lat, lng);
        } else if (!this.endPoint) {
            this.setEndPoint(lat, lng);
        } else {
            this.clearAll();
            this.setStartPoint(lat, lng);
        }
    }

    setStartPoint(lat, lng) {
        this.startPoint = { lat, lng };
        this.map.setStartMarker(lat, lng);
        document.getElementById('startInput').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }

    setEndPoint(lat, lng) {
        this.endPoint = { lat, lng };
        this.map.setEndMarker(lat, lng);
        document.getElementById('endInput').value = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    }

    async calculateRoutes() {
        if (!this.startPoint || !this.endPoint) {
            Utils.showError('Please select start and end points on the map');
            return;
        }

        Utils.setLoading(true);
        
        try {
            const data = await this.api.getMultiRoutes(
                this.startPoint.lat,
                this.startPoint.lon,
                this.endPoint.lat,
                this.endPoint.lon
            );
            
            this.displayMultiRoutes(data);
            
        } catch (error) {
            Utils.showError(error.message);
        } finally {
            Utils.setLoading(false);
        }
    }

    displayMultiRoutes(data) {
        console.log(`Received ${data.total_routes} routes`);
        this.currentRoutes = data.routes;
        
        // Clear existing routes
        this.map.clearRoutes();
        
        // Draw all routes with different colors
        const colors = ['#2ecc71', '#e74c3c', '#9b59b6', '#f39c12', '#1abc9c'];
        const routeTypes = ['cleanest', 'fastest', 'alternative_1', 'alternative_2', 'alternative_3'];
        
        data.routes.forEach((route, index) => {
            const color = colors[index % colors.length];
            const routeType = routeTypes[index % routeTypes.length];
            
            // Create route object for map
            const routeData = {
                ...route,
                coordinates: route.coordinates
            };
            
            this.map.drawRoute(routeData, routeType, color);
        });
        
        // Update route cards
        this.updateRouteCards(data.routes);
        
        // Fit map to show all routes
        this.map.fitRoutes();
        
        // Select first route by default
        this.selectRoute('route_1');
    }

    updateRouteCards(routes) {
        const container = document.getElementById('routeCardsContainer');
        if (!container) {
            // Create container if it doesn't exist
            this.createRouteCardsContainer();
        }
        
        const routeTypes = ['🌱 Cleanest', '🚀 Fastest', '🛣️ Alternative'];
        
        let html = '';
        routes.forEach((route, index) => {
            const routeType = routeTypes[index % routeTypes.length];
            const routeId = `route_${index + 1}`;
            
            html += `
                <div class="route-card" id="${routeId}-card" data-route="${routeId}">
                    <div class="route-header">
                        <h4>${routeType} Route</h4>
                        <span class="route-number">#${index + 1}</span>
                    </div>
                    <div class="route-metrics">
                        <div class="metric">
                            <span class="metric-label">Distance</span>
                            <span class="metric-value">${Utils.formatDistance(route.analysis.total_distance_km)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Time</span>
                            <span class="metric-value">${route.analysis.total_travel_time_min} min</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Avg AQI</span>
                            <span class="metric-value aqi-value ${Utils.getAQIClass(route.analysis.average_aqi)}">
                                ${route.analysis.average_aqi.toFixed(1)}
                            </span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">AQI Range</span>
                            <span class="metric-value">${route.analysis.min_aqi.toFixed(1)} - ${route.analysis.max_aqi.toFixed(1)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Exposure</span>
                            <span class="metric-value">${route.analysis.exposure_score.toFixed(0)}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Sample Points</span>
                            <span class="metric-value">${route.analysis.sample_points_count}</span>
                        </div>
                    </div>
                    <button class="btn btn-primary route-select-btn" data-route="${routeId}">
                        Select This Route
                    </button>
                </div>
            `;
        });
        
        document.getElementById('routeCardsContainer').innerHTML = html;
        
        // Add event listeners to new buttons
        document.querySelectorAll('.route-select-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectRoute(e.target.dataset.route));
        });
    }

    createRouteCardsContainer() {
        const controlPanel = document.querySelector('.control-panel');
        const comparisonSection = document.querySelector('.comparison-summary');
        
        if (comparisonSection) {
            comparisonSection.innerHTML = `
                <h4>Available Routes</h4>
                <div id="routeCardsContainer" class="route-cards-container">
                    <!-- Route cards will be inserted here -->
                </div>
            `;
        }
    }

    selectRoute(routeId) {
        if (!this.currentRoutes) return;
        
        // Extract route number from routeId (e.g., "route_1" -> 0)
        const routeIndex = parseInt(routeId.split('_')[1]) - 1;
        
        // Update visual selection
        document.querySelectorAll('.route-card').forEach(card => {
            card.classList.remove('active');
        });
        
        const selectedCard = document.getElementById(`${routeId}-card`);
        if (selectedCard) {
            selectedCard.classList.add('active');
        }
        
        // Highlight route on map
        this.map.highlightRoute(routeIndex);
        
        console.log(`Selected route ${routeIndex + 1}`);
    }

    updatePollutionDescription() {
        const factor = parseFloat(document.getElementById('pollutionSlider').value);
        document.getElementById('pollutionValue').textContent = factor.toFixed(1);
        document.getElementById('pollutionDescription').textContent = Utils.getPollutionDescription(factor);
    }

    async checkBackendStatus() {
        try {
            const response = await this.api.getStatus();
            document.getElementById('backendStatus').textContent = 'Online';
            document.getElementById('backendStatus').className = 'status-value online';
        } catch (error) {
            document.getElementById('backendStatus').textContent = 'Offline';
            document.getElementById('backendStatus').className = 'status-value offline';
        }
    }

    clearAll() {
        this.startPoint = null;
        this.endPoint = null;
        this.currentRoutes = null;
        
        this.map.clearAll();
        
        document.getElementById('startInput').value = '';
        document.getElementById('endInput').value = '';
        
        // Clear route cards
        const container = document.getElementById('routeCardsContainer');
        if (container) {
            container.innerHTML = '<p>Select start and end points to see available routes</p>';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.multiRouteApp = new MultiRouteApp();
});
