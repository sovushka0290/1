/**
 * ProtoQol Client-Side Configuration
 * SINGLE SOURCE OF TRUTH for API endpoints and system flags.
 */

const PQ_CONFIG = Object.freeze({
    // System Identification
    VERSION: '3.8.5-B2B',
    ENV: window.location.hostname === 'localhost' ? 'DEV' : 'PROD',

    // API Routing
    API_BASE: (window.location.hostname === 'localhost' || window.location.hostname === '')
        ? 'http://localhost:8000'
        : '/api',
    
    ENDPOINTS: {
        ETCH_DEED: '/api/v1/etch_deed',
        STATS: '/api/v1/dashboard/stats',
        MISSIONS: '/api/v1/gateway/missions',
        CAMPAIGNS: '/api/v1/campaigns',
        HEALTH: '/api/v1/engine/health'
    },

    // B2B System Flags
    B2B_KEY: 'PQ_LIVE_DEMO_SECRET',
    DEBUG_MODE: true, // Set to false in production

    // UI Orchestration
    POLL_INTERVAL_MS: 5000,
    TYPING_SPEED_MS: 15,
});

/**
 * PATH INTEGRITY: Helper to get full API URL
 */
function getApiUrl(endpointKey) {
    if (!PQ_CONFIG.ENDPOINTS[endpointKey]) {
        console.error(`[CONFIG_ERROR] Unknown endpoint key: ${endpointKey}`);
        return null;
    }
    return `${PQ_CONFIG.API_BASE}${PQ_CONFIG.ENDPOINTS[endpointKey]}`;
}

/**
 * HEALTH CHECK: Verify backend availability before critical actions
 */
async function checkBackendHealth() {
    try {
        const start = performance.now();
        const resp = await fetch(getApiUrl('HEALTH'));
        const end = performance.now();
        if (resp.ok) {
            console.log(`%c✓ Engine Healthy (${Math.round(end - start)}ms)`, "color: #00FF00");
            return true;
        }
        return false;
    } catch (err) {
        console.warn("%c❌ Engine Offline or Unreachable", "color: #FF0000");
        return false;
    }
}

// Global Export for legacy script compatibility
window.PQ_CONFIG = PQ_CONFIG;
window.getApiUrl = getApiUrl;
window.checkBackendHealth = checkBackendHealth;
