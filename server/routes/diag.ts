import { RequestHandler } from "express";
import dns from 'dns';
import { promisify } from 'util';

const dnsLookup = promisify(dns.lookup);

// PRODUCTION-ONLY API URL - NO LOCALHOST IN PRODUCTION
const getApiUrl = (): string => {
  const apiUrl = process.env.PYTHON_API_URL || 'https://glow-nest-api.fly.dev';

  // PRODUCTION SAFETY: Ban localhost in production builds
  if (process.env.NODE_ENV === 'production' && apiUrl.includes('localhost')) {
    console.error('🚨 LOCALHOST BANNED IN PRODUCTION BUILD');
    return 'https://glow-nest-api.fly.dev';
  }

  return apiUrl;
};

// Safe fetch with comprehensive error handling
const safeFetch = async (url: string, options: RequestInit = {}) => {
  const startTime = Date.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout
    
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'Glow-Nest-Diagnostics/1.0',
        ...options.headers
      }
    });
    
    clearTimeout(timeoutId);
    const endTime = Date.now();
    const text = await response.text();
    
    return {
      success: true,
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries()),
      body: text.substring(0, 500), // First 500 chars
      bodyLength: text.length,
      responseTime: endTime - startTime,
      url
    };
    
  } catch (error: any) {
    const endTime = Date.now();
    return {
      success: false,
      error: {
        name: error.name,
        message: error.message,
        code: error.code,
        errno: error.errno,
        cause: error.cause?.toString(),
        stack: error.stack?.split('\n').slice(0, 3).join('\n')
      },
      responseTime: endTime - startTime,
      url
    };
  }
};

// DNS lookup helper
const checkDNS = async (hostname: string) => {
  try {
    const result = await dnsLookup(hostname);
    return {
      success: true,
      address: result.address,
      family: result.family
    };
  } catch (error: any) {
    return {
      success: false,
      error: {
        name: error.name,
        message: error.message,
        code: error.code
      }
    };
  }
};

export const handleApiDiagnostics: RequestHandler = async (req, res) => {
  const apiUrl = getApiUrl();
  const hostname = new URL(apiUrl).hostname;
  
  console.log(`[DIAG] Starting API diagnostics for ${apiUrl}`);
  
  try {
    // 1. DNS Resolution Check
    console.log(`[DIAG] Checking DNS resolution for ${hostname}`);
    const dnsResult = await checkDNS(hostname);
    
    // 2. Health Check
    console.log(`[DIAG] Checking health endpoint`);
    const healthResult = await safeFetch(`${apiUrl}/health`);
    
    // 3. Routes Debug Check
    console.log(`[DIAG] Checking debug routes endpoint`);
    const routesResult = await safeFetch(`${apiUrl}/__debug/routes`);
    
    // 4. Scraper Start Test
    console.log(`[DIAG] Testing scraper start endpoint`);
    const scraperTestBody = {
      listing_type: "sale",
      max_pages: 1,
      delay_ms: 500,
      headful: false
    };
    
    const scraperResult = await safeFetch(`${apiUrl}/scraper/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(scraperTestBody)
    });
    
    // Compile results
    const diagnostics = {
      timestamp: new Date().toISOString(),
      apiUrl,
      hostname,
      dns: dnsResult,
      tests: {
        health: {
          ...healthResult,
          expected: "JSON with {ok: true}",
          isValidJson: healthResult.success && healthResult.body ? (() => {
            try {
              const parsed = JSON.parse(healthResult.body);
              return { valid: true, hasOk: !!parsed.ok, data: parsed };
            } catch {
              return { valid: false };
            }
          })() : { valid: false }
        },
        routes: {
          ...routesResult,
          expected: "JSON with critical_check object",
          isValidJson: routesResult.success && routesResult.body ? (() => {
            try {
              const parsed = JSON.parse(routesResult.body);
              return { 
                valid: true, 
                hasCriticalCheck: !!parsed.critical_check,
                scraperStartExists: parsed.critical_check?.scraper_start || false,
                data: parsed 
              };
            } catch {
              return { valid: false };
            }
          })() : { valid: false }
        },
        scraperStart: {
          ...scraperResult,
          expected: "JSON with {ok: true} or 409 conflict",
          requestBody: scraperTestBody,
          isValidJson: scraperResult.success && scraperResult.body ? (() => {
            try {
              const parsed = JSON.parse(scraperResult.body);
              return { 
                valid: true, 
                hasOk: 'ok' in parsed,
                isSuccess: parsed.ok === true,
                isConflict: scraperResult.status === 409,
                data: parsed 
              };
            } catch {
              return { valid: false };
            }
          })() : { valid: false }
        }
      }
    };
    
    // Summary
    const summary = {
      dnsOk: dnsResult.success,
      healthOk: healthResult.success && healthResult.status === 200,
      routesOk: routesResult.success && routesResult.status === 200,
      scraperOk: scraperResult.success && (scraperResult.status === 202 || scraperResult.status === 409),
      overallOk: false
    };
    
    summary.overallOk = summary.dnsOk && summary.healthOk && summary.routesOk && summary.scraperOk;
    
    console.log(`[DIAG] Diagnostics completed. Overall OK: ${summary.overallOk}`);
    
    res.json({
      ok: summary.overallOk,
      summary,
      diagnostics,
      recommendations: generateRecommendations(summary, diagnostics)
    });
    
  } catch (error: any) {
    console.error('[DIAG] Diagnostics failed:', error);
    res.status(500).json({
      ok: false,
      error: 'Diagnostics failed',
      details: {
        name: error.name,
        message: error.message,
        stack: error.stack?.split('\n').slice(0, 3).join('\n')
      },
      timestamp: new Date().toISOString()
    });
  }
};

function generateRecommendations(summary: any, diagnostics: any): string[] {
  const recommendations: string[] = [];
  
  if (!summary.dnsOk) {
    recommendations.push("❌ DNS resolution failed. Check if glow-nest-api.fly.dev domain exists and is accessible.");
  }
  
  if (!summary.healthOk) {
    if (diagnostics.tests.health.success) {
      if (diagnostics.tests.health.status !== 200) {
        recommendations.push(`❌ Health endpoint returned ${diagnostics.tests.health.status}. API might be down or misconfigured.`);
      } else if (!diagnostics.tests.health.isValidJson.valid) {
        recommendations.push("❌ Health endpoint returned non-JSON response. This might not be FastAPI.");
      } else if (!diagnostics.tests.health.isValidJson.hasOk) {
        recommendations.push("❌ Health endpoint JSON missing 'ok' field. Wrong API implementation.");
      }
    } else {
      recommendations.push("❌ Health endpoint unreachable. API server is down or URL is wrong.");
    }
  }
  
  if (!summary.routesOk) {
    recommendations.push("❌ Debug routes endpoint failed. FastAPI debug endpoint missing or broken.");
  }
  
  if (!summary.scraperOk) {
    if (diagnostics.tests.scraperStart.success) {
      if (diagnostics.tests.scraperStart.status === 404) {
        recommendations.push("❌ Scraper start endpoint not found (404). Route not implemented.");
      } else if (diagnostics.tests.scraperStart.status >= 500) {
        recommendations.push("❌ Scraper start endpoint server error. Check FastAPI logs.");
      }
    } else {
      recommendations.push("❌ Scraper start endpoint unreachable. Same as health endpoint issue.");
    }
  }
  
  if (summary.overallOk) {
    recommendations.push("✅ All diagnostics passed! API is working correctly.");
  } else {
    recommendations.push("🔧 Run: fly deploy -c fly.api.toml -a glow-nest-api to deploy the API if it's missing.");
  }
  
  return recommendations;
}
