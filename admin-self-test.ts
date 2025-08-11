/**
 * ADMIN PANEL SELF-TEST INTEGRATION
 * Ready-to-use functions for admin panel testing
 */

import {
  API_CONFIG,
  getHealthUrl,
  getDebugRoutesUrl,
  getScraperStartUrl,
} from "./shared/config";
import { safeFetchJson } from "./shared/safe-parser";

interface AdminTestResult {
  ok: boolean;
  message: string;
  status?: number;
  data?: any;
  error?: string;
}

/**
 * Server-side API test (calls /diag/api-check)
 */
export async function runServerSideTest(): Promise<AdminTestResult> {
  try {
    console.log("🖥️  Running server-side API test...");

    const result = await safeFetchJson("/diag/api-check");

    if (result.ok && result.data?.ok) {
      console.log("✅ Server-side test passed");
      return {
        ok: true,
        message: "✅ Server-side test: All API endpoints working",
        data: result.data,
      };
    } else {
      console.log("❌ Server-side test failed");
      return {
        ok: false,
        message: `❌ Server-side test failed: ${result.error || "Unknown error"}`,
        error: result.error,
        data: result.data,
      };
    }
  } catch (error: any) {
    return {
      ok: false,
      message: `❌ Server-side test exception: ${error.message}`,
      error: error.message,
    };
  }
}

/**
 * Client-side API test (direct browser to production API)
 */
export async function runClientSideTest(): Promise<AdminTestResult> {
  try {
    console.log("🌐 Running client-side API test...");

    // Test 1: Health check
    const healthResult = await safeFetchJson(getHealthUrl());
    if (!healthResult.ok || healthResult.status !== 200) {
      return {
        ok: false,
        message: `❌ Health check failed: ${healthResult.error}`,
        status: healthResult.status,
        error: healthResult.error,
      };
    }

    // Test 2: Routes check
    const routesResult = await safeFetchJson(getDebugRoutesUrl());
    if (!routesResult.ok || routesResult.status !== 200) {
      return {
        ok: false,
        message: `❌ Routes check failed: ${routesResult.error}`,
        status: routesResult.status,
        error: routesResult.error,
      };
    }

    // Test 3: Scraper endpoint check
    const scraperResult = await safeFetchJson(getScraperStartUrl(), {
      method: "POST",
      body: JSON.stringify({
        listing_type: "sale",
        max_pages: 1,
        delay_ms: 500,
        headful: false,
      }),
    });

    const scraperOk =
      scraperResult.ok &&
      (scraperResult.status === 202 || scraperResult.status === 409);

    if (!scraperOk) {
      return {
        ok: false,
        message: `❌ Scraper endpoint failed: ${scraperResult.error}`,
        status: scraperResult.status,
        error: scraperResult.error,
      };
    }

    console.log("✅ Client-side test passed");
    return {
      ok: true,
      message: "✅ Client-side test: Direct API access working",
      data: {
        health: healthResult.data,
        routes: routesResult.data?.total_routes,
        scraper: scraperResult.data?.task,
      },
    };
  } catch (error: any) {
    return {
      ok: false,
      message: `❌ Client-side test exception: ${error.message}`,
      error: error.message,
    };
  }
}

/**
 * Combined test with logging for admin panel
 */
export async function runAdminPanelTests(
  addLogEntry: (message: string) => void,
): Promise<boolean> {
  addLogEntry("🔧 ADMIN SELF-TEST STARTED");
  addLogEntry(`🎯 Target API: ${API_CONFIG.BASE_URL}`);
  addLogEntry(
    `🚫 Localhost banned: ${API_CONFIG.BASE_URL.includes("localhost") ? "❌ DETECTED" : "✅ Confirmed"}`,
  );

  // Server-side test
  addLogEntry("🖥️  Running server-side test...");
  const serverResult = await runServerSideTest();
  addLogEntry(serverResult.message);

  if (serverResult.ok && serverResult.data) {
    const summary = serverResult.data.summary;
    addLogEntry(
      `   DNS: ${summary?.dnsOk ? "✅" : "❌"} | Health: ${summary?.healthOk ? "✅" : "❌"} | Routes: ${summary?.routesOk ? "✅" : "❌"} | Scraper: ${summary?.scraperOk ? "✅" : "❌"}`,
    );
  }

  // Client-side test
  addLogEntry("🌐 Running client-side test...");
  const clientResult = await runClientSideTest();
  addLogEntry(clientResult.message);

  if (clientResult.ok && clientResult.data) {
    addLogEntry(
      `   Health: ${clientResult.data.health?.ok ? "✅" : "❌"} | Routes: ${clientResult.data.routes || 0} total | Scraper: ${clientResult.data.scraper ? "✅" : "❌"}`,
    );
  }

  // Overall result
  const allPassed = serverResult.ok && clientResult.ok;

  if (allPassed) {
    addLogEntry("🎉 ADMIN SELF-TEST PASSED");
    addLogEntry("✅ All API endpoints working correctly");
    addLogEntry("✅ Production API connectivity confirmed");
    addLogEntry("✅ Ready for scraper operation");
  } else {
    addLogEntry("🚨 ADMIN SELF-TEST FAILED");
    addLogEntry("❌ Check API connectivity and deployment");
    addLogEntry("❌ Do not start scraper until tests pass");
  }

  return allPassed;
}

// Export for use in admin panel
export { API_CONFIG };
