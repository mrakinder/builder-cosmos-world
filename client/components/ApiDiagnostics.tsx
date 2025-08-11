import React, { useState } from 'react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Loader2, CheckCircle, XCircle, AlertTriangle, Activity } from 'lucide-react';
import { API_CONFIG, safeFetch, getHealthUrl, getDebugRoutesUrl, getScraperStartUrl } from '../../shared/config';
import { safeJson, safeFetchJson } from '../../shared/safe-parser';

interface DiagnosticResult {
  success: boolean;
  status?: number;
  data?: any;
  error?: string;
  details?: any;
}

interface ServerDiagnostics {
  ok: boolean;
  summary: {
    dnsOk: boolean;
    healthOk: boolean;
    routesOk: boolean;
    scraperOk: boolean;
    overallOk: boolean;
  };
  diagnostics: any;
  recommendations: string[];
}

export const ApiDiagnostics: React.FC = () => {
  const [isServerTesting, setIsServerTesting] = useState(false);
  const [isClientTesting, setIsClientTesting] = useState(false);
  const [serverResults, setServerResults] = useState<ServerDiagnostics | null>(null);
  const [clientResults, setClientResults] = useState<{
    health: DiagnosticResult;
    routes: DiagnosticResult;
    scraper: DiagnosticResult;
  } | null>(null);

  const runServerSideTest = async () => {
    setIsServerTesting(true);
    setServerResults(null);
    
    try {
      const response = await fetch('/diag/api-check');
      const data = await response.json();
      setServerResults(data);
    } catch (error: any) {
      setServerResults({
        ok: false,
        summary: {
          dnsOk: false,
          healthOk: false,
          routesOk: false,
          scraperOk: false,
          overallOk: false
        },
        diagnostics: {},
        recommendations: [`Server-side test failed: ${error.message}`]
      });
    } finally {
      setIsServerTesting(false);
    }
  };

  const runClientSideTest = async () => {
    setIsClientTesting(true);
    setClientResults(null);
    
    const results = {
      health: { success: false } as DiagnosticResult,
      routes: { success: false } as DiagnosticResult,
      scraper: { success: false } as DiagnosticResult
    };

    try {
      // Test 1: Health Check
      const healthResult = await safeFetch(getHealthUrl());
      results.health = {
        success: healthResult.ok && healthResult.status === 200,
        status: healthResult.status,
        data: healthResult.data,
        error: healthResult.error,
        details: healthResult.details
      };

      // Test 2: Routes Check
      const routesResult = await safeFetch(getDebugRoutesUrl());
      results.routes = {
        success: routesResult.ok && routesResult.status === 200,
        status: routesResult.status,
        data: routesResult.data,
        error: routesResult.error,
        details: routesResult.details
      };

      // Test 3: Scraper Test (light test)
      const scraperResult = await safeFetch(getScraperStartUrl(), {
        method: 'POST',
        body: JSON.stringify({
          listing_type: 'sale',
          max_pages: 1,
          delay_ms: 500,
          headful: false
        })
      });
      
      results.scraper = {
        success: scraperResult.ok && (scraperResult.status === 202 || scraperResult.status === 409),
        status: scraperResult.status,
        data: scraperResult.data,
        error: scraperResult.error,
        details: scraperResult.details
      };

    } catch (error: any) {
      results.health.error = `Client test failed: ${error.message}`;
    }

    setClientResults(results);
    setIsClientTesting(false);
  };

  const getStatusIcon = (success: boolean) => {
    return success ? (
      <CheckCircle className="w-4 h-4 text-green-600" />
    ) : (
      <XCircle className="w-4 h-4 text-red-600" />
    );
  };

  const getStatusBadge = (success: boolean, label: string) => {
    return (
      <Badge variant={success ? "default" : "destructive"} className="ml-2">
        {success ? "✅" : "❌"} {label}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            API Diagnostics
          </CardTitle>
          <CardDescription>
            Test API connectivity and functionality from both server and client perspectives
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          
          {/* API Configuration Info */}
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>🎯 Production API:</strong> {API_CONFIG.BASE_URL}<br/>
              <strong>🚫 Localhost banned:</strong> {API_CONFIG.BASE_URL.includes('localhost') ? '❌ DETECTED' : '✅ Confirmed'}
            </AlertDescription>
          </Alert>

          {/* Server-Side Test */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold">Server-Side Test</h4>
              <Button
                onClick={runServerSideTest}
                disabled={isServerTesting}
                variant="outline"
                size="sm"
              >
                {isServerTesting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  '🔍 Test from Server'
                )}
              </Button>
            </div>
            
            {serverResults && (
              <div className="space-y-2 p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  {getStatusIcon(serverResults.summary.overallOk)}
                  <span className="ml-2 font-medium">
                    Overall Status: {serverResults.summary.overallOk ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="flex items-center">
                    {getStatusIcon(serverResults.summary.dnsOk)}
                    <span className="ml-2">DNS Resolution</span>
                  </div>
                  <div className="flex items-center">
                    {getStatusIcon(serverResults.summary.healthOk)}
                    <span className="ml-2">Health Endpoint</span>
                  </div>
                  <div className="flex items-center">
                    {getStatusIcon(serverResults.summary.routesOk)}
                    <span className="ml-2">Routes Endpoint</span>
                  </div>
                  <div className="flex items-center">
                    {getStatusIcon(serverResults.summary.scraperOk)}
                    <span className="ml-2">Scraper Endpoint</span>
                  </div>
                </div>
                
                {serverResults.recommendations.length > 0 && (
                  <div className="mt-2">
                    <p className="font-medium text-sm">Recommendations:</p>
                    <ul className="text-xs space-y-1 mt-1">
                      {serverResults.recommendations.map((rec, index) => (
                        <li key={index} className="text-gray-600">{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Client-Side Test */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold">Client-Side Test</h4>
              <Button
                onClick={runClientSideTest}
                disabled={isClientTesting}
                variant="outline"
                size="sm"
              >
                {isClientTesting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  '🌐 Test from Browser'
                )}
              </Button>
            </div>
            
            {clientResults && (
              <div className="space-y-2 p-3 bg-gray-50 rounded-lg">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Health Check:</span>
                    <div className="flex items-center">
                      {getStatusBadge(clientResults.health.success, `${clientResults.health.status || 'ERR'}`)}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Routes Check:</span>
                    <div className="flex items-center">
                      {getStatusBadge(clientResults.routes.success, `${clientResults.routes.status || 'ERR'}`)}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm">Scraper Test:</span>
                    <div className="flex items-center">
                      {getStatusBadge(clientResults.scraper.success, `${clientResults.scraper.status || 'ERR'}`)}
                    </div>
                  </div>
                </div>
                
                {/* Show errors if any */}
                {(clientResults.health.error || clientResults.routes.error || clientResults.scraper.error) && (
                  <div className="mt-2 p-2 bg-red-50 rounded border">
                    <p className="font-medium text-sm text-red-800">Errors:</p>
                    <ul className="text-xs space-y-1 mt-1 text-red-700">
                      {clientResults.health.error && <li>Health: {clientResults.health.error}</li>}
                      {clientResults.routes.error && <li>Routes: {clientResults.routes.error}</li>}
                      {clientResults.scraper.error && <li>Scraper: {clientResults.scraper.error}</li>}
                    </ul>
                  </div>
                )}
                
                {/* Show success data if available */}
                {clientResults.health.success && clientResults.health.data && (
                  <div className="mt-2 p-2 bg-green-50 rounded border">
                    <p className="font-medium text-sm text-green-800">API Response Sample:</p>
                    <pre className="text-xs text-green-700 mt-1 overflow-x-auto">
                      {JSON.stringify(clientResults.health.data, null, 2).substring(0, 300)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quick Status Summary */}
          {(serverResults || clientResults) && (
            <Alert>
              <AlertDescription>
                <strong>Quick Summary:</strong> {' '}
                {serverResults?.summary.overallOk && clientResults?.health.success ? (
                  <span className="text-green-600 font-medium">✅ API is working correctly from both server and client!</span>
                ) : (
                  <span className="text-red-600 font-medium">❌ API has connectivity issues. Check diagnostics above.</span>
                )}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ApiDiagnostics;
