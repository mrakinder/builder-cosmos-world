/**
 * Centralized API Configuration
 * Single source of truth for all API URLs and settings
 */

// Environment-based API URL configuration
const getApiUrl = (): string => {
  // Check environment variables first
  if (typeof process !== 'undefined' && process.env?.PYTHON_API_URL) {
    return process.env.PYTHON_API_URL;
  }
  
  // Check browser environment variables (injected during build)
  if (typeof window !== 'undefined' && (window as any).__PYTHON_API_URL__) {
    return (window as any).__PYTHON_API_URL__;
  }
  
  // Development vs Production defaults
  if (typeof window !== 'undefined') {
    // Browser environment - check hostname
    if (window.location.hostname.includes('fly.dev') || window.location.hostname.includes('localhost')) {
      return 'https://glow-nest-api.fly.dev';
    }
  }
  
  // Server environment - check NODE_ENV or hostname
  if (typeof process !== 'undefined') {
    if (process.env.NODE_ENV === 'production') {
      return 'https://glow-nest-api.fly.dev';
    }
    // Local development fallback
    return 'http://localhost:8080';
  }
  
  // Final fallback
  return 'https://glow-nest-api.fly.dev';
};

export const API_CONFIG = {
  // Base API URL
  BASE_URL: getApiUrl(),
  
  // Timeout settings
  TIMEOUT: 15000, // 15 seconds
  
  // Endpoints
  ENDPOINTS: {
    HEALTH: '/health',
    DEBUG_ROUTES: '/__debug/routes',
    SCRAPER_START: '/scraper/start',
    SCRAPER_START_ALIAS: '/api/scraper/start',
    SCRAPER_STOP: '/scraper/stop',
    SCRAPER_STATUS: '/scraper/status',
    PROGRESS_STREAM: '/progress/scrape',
    EVENTS_STREAM: '/events/stream'
  },
  
  // Request headers
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cache-Control': 'no-cache'
  }
} as const;

// Helper functions for building URLs
export const buildApiUrl = (endpoint: string): string => {
  const baseUrl = API_CONFIG.BASE_URL.replace(/\/$/, ''); // Remove trailing slash
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

export const getHealthUrl = (): string => buildApiUrl(API_CONFIG.ENDPOINTS.HEALTH);
export const getDebugRoutesUrl = (): string => buildApiUrl(API_CONFIG.ENDPOINTS.DEBUG_ROUTES);
export const getScraperStartUrl = (): string => buildApiUrl(API_CONFIG.ENDPOINTS.SCRAPER_START);
export const getProgressStreamUrl = (): string => buildApiUrl(API_CONFIG.ENDPOINTS.PROGRESS_STREAM);
export const getEventsStreamUrl = (): string => buildApiUrl(API_CONFIG.ENDPOINTS.EVENTS_STREAM);

// Logging helper
export const logApiRequest = (method: string, url: string, body?: any): void => {
  const timestamp = new Date().toISOString();
  console.log(`[API-REQUEST] ${timestamp} ${method} ${url}`);
  if (body) {
    console.log(`[API-REQUEST] Body: ${JSON.stringify(body).substring(0, 200)}${JSON.stringify(body).length > 200 ? '...' : ''}`);
  }
};

export const logApiResponse = (url: string, status: number, body?: string): void => {
  const timestamp = new Date().toISOString();
  console.log(`[API-RESPONSE] ${timestamp} ${status} ${url}`);
  if (body) {
    console.log(`[API-RESPONSE] Body: ${body.substring(0, 200)}${body.length > 200 ? '...' : ''}`);
  }
};

// Error handling helper
export const handleApiError = (error: any, context: string): { error: string, details: any } => {
  const timestamp = new Date().toISOString();
  console.error(`[API-ERROR] ${timestamp} ${context}:`, error);
  
  return {
    error: error.message || 'Unknown error',
    details: {
      name: error.name,
      message: error.message,
      code: error.code,
      errno: error.errno,
      cause: error.cause,
      stack: error.stack?.split('\n').slice(0, 3).join('\n'), // First 3 lines of stack
      context,
      timestamp
    }
  };
};

// Safe fetch wrapper with comprehensive error handling
export const safeFetch = async (url: string, options: RequestInit = {}): Promise<{
  ok: boolean;
  status: number;
  data?: any;
  text?: string;
  error?: string;
  details?: any;
}> => {
  const method = options.method || 'GET';
  logApiRequest(method, url, options.body);
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...API_CONFIG.HEADERS,
        ...options.headers
      },
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    const text = await response.text();
    logApiResponse(url, response.status, text);
    
    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        text,
        error: `HTTP ${response.status}: ${response.statusText}`,
        details: { status: response.status, statusText: response.statusText, headers: Object.fromEntries(response.headers.entries()) }
      };
    }
    
    // Try to parse JSON
    try {
      const data = JSON.parse(text);
      return { ok: true, status: response.status, data, text };
    } catch (parseError) {
      return {
        ok: false,
        status: response.status,
        text,
        error: 'Invalid JSON response',
        details: { parseError: (parseError as Error).message }
      };
    }
    
  } catch (error: any) {
    const errorInfo = handleApiError(error, `safeFetch ${method} ${url}`);
    return {
      ok: false,
      status: 0,
      error: errorInfo.error,
      details: errorInfo.details
    };
  }
};

// Export current configuration for debugging
export const debugConfig = () => {
  console.log('API Configuration:', {
    BASE_URL: API_CONFIG.BASE_URL,
    ENDPOINTS: API_CONFIG.ENDPOINTS,
    TIMEOUT: API_CONFIG.TIMEOUT,
    environment: {
      NODE_ENV: typeof process !== 'undefined' ? process.env?.NODE_ENV : 'browser',
      hostname: typeof window !== 'undefined' ? window.location.hostname : 'server',
      PYTHON_API_URL: typeof process !== 'undefined' ? process.env?.PYTHON_API_URL : 'not set'
    }
  });
};
