class AQIAPI {
    constructor(baseURL = null) {
        this.baseURL = baseURL || (window.APP_CONFIG ? window.APP_CONFIG.apiBaseUrl : 'http://localhost:5002');
        this.timeout = 60000; // FIX: was 10s, AQI sampling takes 30-40s
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                headers: { 'Content-Type': 'application/json', ...options.headers }
            });
            clearTimeout(timer);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return await response.json();
        } catch (error) {
            clearTimeout(timer);
            if (error.name === 'AbortError') throw new Error('Request timed out after 60 seconds');
            console.error('[API Error]', error);
            throw error;
        }
    }

    async getSystemStatus() {
        try {
            const response = await this.request('/');
            return { status: 'online', message: response };
        } catch (error) {
            return { status: 'offline', error: error.message };
        }
    }

    async getStations() {
        try {
            return await this.request('/stations');
        } catch (error) {
            throw new Error(`Failed to fetch AQI stations: ${error.message}`);
        }
    }

    async getMultiRoutes(startLat, startLon, endLat, endLon) {
        const params = new URLSearchParams({
            start_lat: startLat,
            start_lon: startLon,
            end_lat: endLat,
            end_lon: endLon
        });
        return this.request(`/routes/multi?${params}`);
    }

    async getCleanRoute(startLat, startLon, endLat, endLon, pollutionFactor = 2.0) {
        const params = new URLSearchParams({
            start_lat: startLat,
            start_lon: startLon,
            end_lat: endLat,
            end_lon: endLon,
            pollution_factor: pollutionFactor
        });

        try {
            return await this.request(`/routes/clean?${params}`);
        } catch (error) {
            throw new Error(`Failed to calculate routes: ${error.message}`);
        }
    }

    async saveRoutes(routeData) {
        try {
            console.log('[API] saveRoutes called with:', routeData);
            console.log('[API] Full URL:', `${this.baseURL}/save-routes`);
            const response = await this.request('/save-routes', {
                method: 'POST',
                body: JSON.stringify(routeData)
            });
            console.log('✅ Routes saved to database:', response);
            return response;
        } catch (error) {
            console.error('❌ Failed to save routes to database:', error);
            console.error('[API] Error details:', error.message);
            // Don't throw error - saving is optional, route calculation is primary
            return { success: false, error: error.message };
        }
    }

    async testConnection() {
        const startTime = Date.now();
        try {
            await this.getSystemStatus();
            return {
                success: true,
                responseTime: Date.now() - startTime
            };
        } catch (error) {
            return {
                success: false,
                error: error.message,
                responseTime: Date.now() - startTime
            };
        }
    }
}
 
// Export for use in other modules
window.AQIAPI = AQIAPI;
