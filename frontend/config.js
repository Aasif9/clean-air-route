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

// Make available globally
window.APP_CONFIG = currentConfig;
