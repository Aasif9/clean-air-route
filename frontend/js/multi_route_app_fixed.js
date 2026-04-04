class MultiRouteApp {
    constructor() {
        this.api = new AQIAPI();
        this.map = new AQIMap('map');
        this.currentRoutes = null;
        this.startPoint = null;
        this.endPoint = null;
        this.clickState = 'start'; // 'start' | 'end'
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkBackendStatus();
    }

    setupEventListeners() {
        // FIX: use lon (matches mapClick event detail)
        document.addEventListener('mapClick', (e) => this.handleMapClick(e.detail.lat, e.detail.lon));

        document.getElementById('calculateBtn').addEventListener('click', () => this.calculateRoutes());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearAll());

        const centerBtn = document.getElementById('centerBtn');
        if (centerBtn) centerBtn.addEventListener('click', () => this.map.centerMap());

        const fsBtn = document.getElementById('fullscreenBtn');
        if (fsBtn) fsBtn.addEventListener('click', () => this.map.toggleFullscreen());
    }

    handleMapClick(lat, lon) {
        if (this.clickState === 'start') {
            this.startPoint = { lat, lon };
            this.map.setStartMarker(lat, lon);
            document.getElementById('startInput').value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.clickState = 'end';
        } else if (this.clickState === 'end') {
            this.endPoint = { lat, lon };
            this.map.setEndMarker(lat, lon);
            document.getElementById('endInput').value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
            this.clickState = 'start'; // reset for next selection cycle
        }
    }

    async calculateRoutes() {
        if (!this.startPoint || !this.endPoint) {
            this.showError('Click the map to set a start point, then an end point.');
            return;
        }

        this.setLoading(true, 'Fetching routes and AQI data from Google...');

        try {
            const data = await this.api.getMultiRoutes(
                this.startPoint.lat,
                this.startPoint.lon, // FIX: was this.startPoint.lng
                this.endPoint.lat,
                this.endPoint.lon    // FIX: was this.endPoint.lng
            );

            if (data.error) throw new Error(data.error);

            this.currentRoutes = data.routes;
            this.map.drawAllRoutes(data.routes);
            this.renderRouteCards(data.routes);

        } catch (error) {
            this.showError(`Route calculation failed: ${error.message}`);
            console.error('[App Error]', error);
        } finally {
            this.setLoading(false);
        }
    }

    renderRouteCards(routes) {
        const container = document.getElementById('routeCardsContainer');
        if (!container) return;

        const labels = ['Cleanest', 'Fastest', 'Alternative 1', 'Alternative 2', 'Alternative 3'];
        const colors = ['#2ecc71', '#e74c3c', '#9b59b6', '#f39c12', '#1abc9c'];

        container.innerHTML = routes.map((route, i) => {
            const a = route.analysis;
            const aqiClass = a.average_aqi <= 50 ? 'aqi-good'
                : a.average_aqi <= 100 ? 'aqi-moderate'
                : a.average_aqi <= 150 ? 'aqi-unhealthy' : 'aqi-very-unhealthy';

            return `
            <div class="route-card" id="card-${i}" data-index="${i}" onclick="app.selectRoute(${i})">
                <div class="route-header">
                    <div style="display:flex;align-items:center;gap:8px">
                        <div style="width:12px;height:12px;border-radius:50%;background:${colors[i % colors.length]};flex-shrink:0"></div>
                        <h4 style="margin:0;color:#2c3e50;font-size:15px">${labels[i] || 'Route ' + (i+1)}</h4>
                    </div>
                    <span class="route-number" style="background:${colors[i % colors.length]}">#${i+1}</span>
                </div>
                <div class="route-metrics">
                    <div class="metric">
                        <span class="metric-label">Distance</span>
                        <span class="metric-value">${a.total_distance_km} km</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Time</span>
                        <span class="metric-value">${a.total_travel_time_min} min</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg AQI</span>
                        <span class="metric-value aqi-value ${aqiClass}">${a.average_aqi}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">AQI range</span>
                        <span class="metric-value">${a.min_aqi} – ${a.max_aqi}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Exposure score</span>
                        <span class="metric-value">${a.exposure_score}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sample points</span>
                        <span class="metric-value">${a.sample_points_count}</span>
                    </div>
                </div>
            </div>`;
        }).join('');
    }

    selectRoute(index) {
        document.querySelectorAll('.route-card').forEach(c => c.classList.remove('active'));
        const card = document.getElementById(`card-${index}`);
        if (card) { card.classList.add('active'); card.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
        this.map.highlightRoute(index);
    }

    clearAll() {
        this.startPoint = null;
        this.endPoint = null;
        this.currentRoutes = null;
        this.clickState = 'start';
        this.map.clearAll();
        document.getElementById('startInput').value = '';
        document.getElementById('endInput').value = '';
        const container = document.getElementById('routeCardsContainer');
        if (container) container.innerHTML = '<p style="color:#7f8c8d;font-size:13px">Click the map to set start and end points, then press Calculate Routes.</p>';
    }

    async checkBackendStatus() {
        const el = document.getElementById('backendStatus');
        if (!el) return;
        const result = await this.api.getSystemStatus();
        el.textContent = result.status === 'online' ? 'Online' : 'Offline';
        el.style.color = result.status === 'online' ? '#27ae60' : '#e74c3c';
    }

    setLoading(show, message = 'Calculating...') {
        const overlay = document.getElementById('loadingOverlay');
        if (!overlay) return;
        if (show) {
            overlay.querySelector('p').textContent = message;
            overlay.style.display = 'flex';
        } else {
            overlay.style.display = 'none';
        }
    }

    showError(msg) {
        const toast = document.getElementById('errorToast');
        const msgEl = document.getElementById('errorMessage');
        if (!toast || !msgEl) { alert(msg); return; }
        msgEl.textContent = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.app = new MultiRouteApp();
});
