// Configuration for different environments
const CONFIG = {
    development: {
        apiBaseUrl: 'http://localhost:5002',
        environment: 'Development'
    },
    production: {
        apiBaseUrl: 'https://kolkata-clean-air-route.onrender.com',
        environment: 'Production'
    }
};

// Auto-detect environment
const currentConfig = CONFIG[window.location.hostname === 'localhost' ? 'development' : 'production'];
const SUPABASE_CONFIG = {
    url: 'https://bnlcnefcjngoapdcijer.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJubGNuZWZjam5nb2FwZGNpamVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzYzMDQsImV4cCI6MjA5MTkxMjMwNH0.wvUyDePWbUvGvksin82JhVIxbDXUuV1Y4O0N2FvwpCQ' // Replace with your actual key
};
 
// Make available globally
window.APP_CONFIG = currentConfig;
window.SUPABASE_CONFIG = SUPABASE_CONFIG;
