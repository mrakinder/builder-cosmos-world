/**
 * PRODUCTION ACCEPTANCE TEST
 * Verify localhost is banned and production API is working
 *
 * Run: npm run test:acceptance-prod
 */

import {
  API_CONFIG,
  getHealthUrl,
  getDebugRoutesUrl,
  getScraperStartUrl,
} from "./shared/config";
import { safeFetchJson } from "./shared/safe-parser";

interface TestResult {
  name: string;
  passed: boolean;
  message: string;
  details?: any;
}

async function runAcceptanceTest(): Promise<void> {
  const results: TestResult[] = [];
  const startTime = Date.now();

  console.log("🚀 PRODUCTION ACCEPTANCE TEST STARTED");
  console.log("=====================================");
  console.log(`Target API: ${API_CONFIG.BASE_URL}`);
  console.log(`Environment: ${process.env.NODE_ENV || "development"}`);
  console.log("");

  // Test 1: Localhost Ban Verification
  results.push({
    name: "Localhost Ban Verification",
    passed: !API_CONFIG.BASE_URL.includes("localhost"),
    message: API_CONFIG.BASE_URL.includes("localhost")
      ? "❌ CRITICAL: localhost detected in production config"
      : "✅ localhost successfully banned from production",
    details: { configured_url: API_CONFIG.BASE_URL },
  });

  // Test 2: Health Check
  console.log("🏥 Testing Health Endpoint...");
  try {
    const healthResult = await safeFetchJson(getHealthUrl());
    const healthPassed =
      healthResult.ok &&
      healthResult.status === 200 &&
      healthResult.data?.ok === true;

    results.push({
      name: "Health Check",
      passed: healthPassed,
      message: healthPassed
        ? "✅ Health endpoint responding correctly"
        : `❌ Health endpoint failed: ${healthResult.error || "Invalid response"}`,
      details: {
        status: healthResult.status,
        response: healthResult.data,
        error: healthResult.error,
      },
    });

    if (healthPassed) {
      console.log(`   ✅ Status: ${healthResult.status}`);
      console.log(
        `   ✅ Response: ${JSON.stringify(healthResult.data).substring(0, 100)}...`,
      );
    } else {
      console.log(`   ❌ Status: ${healthResult.status}`);
      console.log(`   ❌ Error: ${healthResult.error}`);
    }
  } catch (error: any) {
    results.push({
      name: "Health Check",
      passed: false,
      message: `❌ Health check exception: ${error.message}`,
      details: { error: error.message },
    });
  }

  // Test 3: Routes Debug Check
  console.log("🛣️  Testing Routes Debug Endpoint...");
  try {
    const routesResult = await safeFetchJson(getDebugRoutesUrl());
    const routesPassed = routesResult.ok && routesResult.status === 200;
    const hasCriticalRoutes =
      routesResult.data?.critical_check?.scraper_start === true;

    results.push({
      name: "Routes Debug Check",
      passed: routesPassed && hasCriticalRoutes,
      message:
        routesPassed && hasCriticalRoutes
          ? "✅ Routes debug endpoint working, critical routes found"
          : `❌ Routes debug failed: ${routesResult.error || "Missing critical routes"}`,
      details: {
        status: routesResult.status,
        critical_check: routesResult.data?.critical_check,
        total_routes: routesResult.data?.total_routes,
      },
    });

    if (routesPassed) {
      console.log(`   ✅ Status: ${routesResult.status}`);
      console.log(`   ✅ Total routes: ${routesResult.data?.total_routes}`);
      console.log(`   ✅ Critical check:`, routesResult.data?.critical_check);
    }
  } catch (error: any) {
    results.push({
      name: "Routes Debug Check",
      passed: false,
      message: `❌ Routes debug exception: ${error.message}`,
      details: { error: error.message },
    });
  }

  // Test 4: Scraper Start (POST JSON)
  console.log("🤖 Testing Scraper Start Endpoint...");
  try {
    const scraperResult = await safeFetchJson(getScraperStartUrl(), {
      method: "POST",
      body: JSON.stringify({
        listing_type: "sale",
        max_pages: 1,
        delay_ms: 1000,
        headful: false,
      }),
    });

    const scraperPassed =
      scraperResult.ok &&
      (scraperResult.status === 202 || scraperResult.status === 409) &&
      scraperResult.data?.ok === true;

    results.push({
      name: "Scraper Start Endpoint",
      passed: scraperPassed,
      message: scraperPassed
        ? `✅ Scraper endpoint working (${scraperResult.status})`
        : `❌ Scraper endpoint failed: ${scraperResult.error || "Invalid response"}`,
      details: {
        status: scraperResult.status,
        response: scraperResult.data,
        error: scraperResult.error,
      },
    });

    if (scraperPassed) {
      console.log(`   ✅ Status: ${scraperResult.status}`);
      console.log(`   ✅ Task ID: ${scraperResult.data?.task || "N/A"}`);
      console.log(`   �� Status: ${scraperResult.data?.status || "N/A"}`);
    }
  } catch (error: any) {
    results.push({
      name: "Scraper Start Endpoint",
      passed: false,
      message: `❌ Scraper start exception: ${error.message}`,
      details: { error: error.message },
    });
  }

  // Generate Report
  const endTime = Date.now();
  const duration = endTime - startTime;
  const passed = results.filter((r) => r.passed).length;
  const total = results.length;
  const allPassed = passed === total;

  console.log("");
  console.log("📋 ACCEPTANCE TEST RESULTS");
  console.log("==========================");

  results.forEach((result) => {
    console.log(
      `${result.passed ? "✅" : "❌"} ${result.name}: ${result.message}`,
    );
  });

  console.log("");
  console.log(`🎯 Summary: ${passed}/${total} tests passed`);
  console.log(`⏱️  Duration: ${duration}ms`);
  console.log(`🌐 API URL: ${API_CONFIG.BASE_URL}`);
  console.log("");

  if (allPassed) {
    console.log("🎉 ACCEPTANCE PASSED: Production API ready");
    console.log("✅ All localhost references removed");
    console.log("✅ Production API endpoints functional");
    console.log("✅ Ready for deployment");

    // Log success to application logs
    if (typeof window === "undefined") {
      // Server-side logging
      console.log("[ACCEPTANCE_LOG] ACCEPTANCE PASSED - Production ready");
    }
  } else {
    console.log("🚨 ACCEPTANCE FAILED: Issues detected");
    console.log("❌ Check failed tests above");
    console.log("❌ Do not deploy until all tests pass");

    process.exit(1);
  }
}

// Auto-run if called directly
if (require.main === module) {
  runAcceptanceTest().catch((error) => {
    console.error("💥 Acceptance test crashed:", error);
    process.exit(1);
  });
}

export { runAcceptanceTest };
