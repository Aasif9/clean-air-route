class AQIAPI {
    constructor(baseURL = 'http://localhost:5002') {
        this.baseURL = baseURL;
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

    async getMultiRoutes(startLat, startLon, endLat, endLon) {
        const params = new URLSearchParams({
            start_lat: startLat,
            start_lon: startLon,
            end_lat: endLat,
            end_lon: endLon
        });
        return this.request(`/routes/multi?${params}`);
    }
}

window.AQIAPI = AQIAPI;
