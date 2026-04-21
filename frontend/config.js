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

// Supabase configuration
const SUPABASE_CONFIG = {
    development: {
        url: 'https://bnlcnefcjngoapdcijer.supabase.co',
        anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJubGNuZWZjam5nb2FwZGNpamVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzYzMDQsImV4cCI6MjA5MTkxMjMwNH0.wvUyDePWbUvGvksin82JhVIxbDXUuV1Y4O0N2FvwpCQ'
    },
    production: {
        url: 'https://bnlcnefcjngoapdcijer.supabase.co',
        anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJubGNuZWZjam5nb2FwZGNpamVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMzYzMDQsImV4cCI6MjA5MTkxMjMwNH0.wvUyDePWbUvGvksin82JhVIxbDXUuV1Y4O0N2FvwpCQ'
    }
};

// Auto-detect environment - also check for 127.0.0.1 and other local addresses
const isLocalhost = window.location.hostname === 'localhost' || 
                   window.location.hostname === '127.0.0.1' || 
                   window.location.hostname.startsWith('192.168.') ||
                   window.location.hostname.startsWith('10.') ||
                   window.location.port === '3000'; // Force local if on port 3000

const currentConfig = CONFIG[isLocalhost ? 'development' : 'production'];
const currentSupabaseConfig = SUPABASE_CONFIG[isLocalhost ? 'development' : 'production'];

// Make available globally
window.APP_CONFIG = currentConfig;
window.SUPABASE_CONFIG = currentSupabaseConfig;
