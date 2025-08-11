/**
 * Safe JSON parser to prevent "Unexpected end of JSON input" errors
 * Replaces all unsafe await res.json() calls
 */

export interface SafeJsonResult {
  ok: boolean;
  data?: any;
  error?: string;
  raw?: string;
  status: number;
}

export async function safeJson(res: Response): Promise<SafeJsonResult> {
  try {
    const text = await res.text();
    
    // Empty response check
    if (!text || text.trim() === '') {
      return {
        ok: false,
        error: `Empty response body (HTTP ${res.status})`,
        raw: text,
        status: res.status
      };
    }
    
    // Try to parse JSON
    try {
      const data = JSON.parse(text);
      return {
        ok: true,
        data,
        status: res.status
      };
    } catch (parseError) {
      return {
        ok: false,
        error: `Invalid JSON: ${parseError.message}`,
        raw: text.substring(0, 120) + (text.length > 120 ? '...' : ''),
        status: res.status
      };
    }
  } catch (fetchError) {
    return {
      ok: false,
      error: `Response read error: ${fetchError.message}`,
      status: res.status
    };
  }
}

/**
 * Safe fetch wrapper for production API calls
 */
export async function safeFetchJson(url: string, options: RequestInit = {}): Promise<SafeJsonResult> {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    return await safeJson(response);
  } catch (fetchError) {
    return {
      ok: false,
      error: `Fetch failed: ${fetchError.message}`,
      status: 0
    };
  }
}
