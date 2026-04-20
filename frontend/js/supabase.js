// Supabase client for frontend
class SupabaseClient {
    constructor() {
        this.url = window.SUPABASE_CONFIG.url;
        this.key = window.SUPABASE_CONFIG.anonKey;
    }
 
    async getRouteHistory(userId = 'anonymous_user') {
        try {
            const response = await fetch(`${window.APP_CONFIG.apiBaseUrl}/routes/history/${userId}`);
            const data = await response.json();
            return data.routes || [];
        } catch (error) {
            console.error('Error fetching route history:', error);
            return [];
        }
    }
 
    async saveRoute(userId, routeData) {
        try {
            const response = await fetch(`${window.APP_CONFIG.apiBaseUrl}/routes/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    route_data: routeData
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error saving route:', error);
            return null;
        }
    }
}
 
// Global instance
window.supabaseClient = new SupabaseClient();
