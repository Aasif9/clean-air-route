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

    async getMultiRoutes(startLat, startLon, endLat, endLon, userId = null) {
        const params = new URLSearchParams({
            start_lat: startLat,
            start_lon: startLon,
            end_lat: endLat,
            end_lon: endLon
        });
        if (userId) {
            params.append('user_id', userId);
        }
        const url = `/routes/multi?${params}`;
        console.log('[API] Calling backend URL:', this.baseURL + url);
        console.log('[API] With params:', params.toString());
        return this.request(url);
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
 
// Update your existing calculateRoute function
async function calculateRoute(startLat, startLon, endLat, endLon) {
    const userId = historyManager.getUserId();
    
    const url = `${window.APP_CONFIG.apiBaseUrl}/routes/multi?` +
                `start_lat=${startLat}&start_lon=${startLon}&` +
                `end_lat=${endLat}&end_lon=${endLon}&` +
                `user_id=${userId}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Refresh route history after calculation
        setTimeout(() => {
            historyManager.loadRouteHistory();
        }, 1000);
        
        return data;
    } catch (error) {
        console.error('Route calculation failed:', error);
        throw error;
    }
}

// Export for use in other modules
window.AQIAPI = AQIAPI;
window.calculateRoute = calculateRoute;
