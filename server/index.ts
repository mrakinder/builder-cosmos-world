import "dotenv/config";
import express from "express";
import cors from "cors";
import path from "path";
import { handleDemo } from "./routes/demo";
import {
  handleStartScraping,
  handleScrapingStatus,
  handlePropertyStats,
  handleStopScraping,
  handleActivityLog,
  handlePriceTrends,
  handleGetProperties,
  handleGetStreetMap,
  handleAddStreet,
  handleCheckPropertyUpdates
} from "./routes/scraping";
import {
  handleRetrainModel,
  handleRetrainAdvancedModel,
  handleModelInfo,
  handleModelComparison
} from "./routes/models";
import {
  handleAddManualProperty,
  handleManualPropertyStats,
  handleDeleteManualProperties,
  handleExportProperties
} from "./routes/manual-properties";
import {
  handleMLPredict,
  handleProphetForecast,
  handleTrainML,
  handleStreamlitStatus,
  handleStartStreamlit,
  handleStopStreamlit,
  handleSupersetStatus,
  handlePipelineStatus,
  handleMLProgress
} from "./routes/ml-integration";
import deployRouter from "./routes/deploy";

export function createServer() {
  const app = express();

  // Middleware
  app.use(cors());
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Example API routes
  app.get("/api/ping", (_req, res) => {
    const ping = process.env.PING_MESSAGE ?? "ping";
    res.json({ message: ping });
  });

  app.get("/api/demo", handleDemo);

  // Scraping routes
  app.post("/api/start-scraping", handleStartScraping);
  app.get("/api/scraping-status", handleScrapingStatus);
  app.get("/api/property-stats", handlePropertyStats);
  app.post("/api/stop-scraping", handleStopScraping);
  app.get("/api/activity-log", handleActivityLog);
  app.get("/api/price-trends", handlePriceTrends);

  // Property and street management routes
  app.get("/api/properties", handleGetProperties);
  app.get("/api/street-map", handleGetStreetMap);
  app.post("/api/add-street", handleAddStreet);
  app.post("/api/check-property-updates", handleCheckPropertyUpdates);

  // Model routes
  app.post("/api/retrain-model", handleRetrainModel);
  app.post("/api/retrain-advanced-model", handleRetrainAdvancedModel);
  app.get("/api/model-info", handleModelInfo);
  app.get("/api/model-comparison", handleModelComparison);

  // Manual property routes
  app.post("/api/manual-property/add", handleAddManualProperty);
  app.get("/api/manual-property-stats", handleManualPropertyStats);
  app.delete("/api/manual-property/delete-manual-properties", handleDeleteManualProperties);
  app.get("/api/export-properties", handleExportProperties);

  // ML Integration routes
  app.post("/api/ml/predict", handleMLPredict);
  app.get("/api/ml/forecast", handleProphetForecast);
  app.post("/api/ml/train", handleTrainML);
  app.get("/api/ml/progress", handleMLProgress);
  app.get("/api/streamlit/status", handleStreamlitStatus);
  app.post("/api/streamlit/start", handleStartStreamlit);
  app.post("/api/streamlit/stop", handleStopStreamlit);
  app.get("/api/superset/status", handleSupersetStatus);
  app.get("/api/pipeline/status", handlePipelineStatus);

  // Deploy routes
  app.use("/api", deployRouter);

  // New 5-Module System Routes
  app.post("/api/scraper/start", handleStartScraping);
  app.get("/api/scraper/status", handleScrapingStatus);
  app.post("/api/scraper/stop", handleStopScraping);

  // Global SSE connections array
  const sseConnections: any[] = [];

  // Global broadcast function
  (global as any).broadcastSSE = (data: any) => {
    const message = `data: ${JSON.stringify(data)}\n\n`;
    sseConnections.forEach((res, index) => {
      try {
        res.write(message);
      } catch (error) {
        // Remove dead connections
        sseConnections.splice(index, 1);
      }
    });
  };

  // Server-Sent Events for real-time updates
  app.get("/api/events/stream", (req, res) => {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    // Add connection to list
    sseConnections.push(res);

    // Send initial connection message
    res.write(`data: ${JSON.stringify({ type: 'connected', message: 'SSE connected' })}\n\n`);

    // Keep connection alive
    const heartbeat = setInterval(() => {
      try {
        res.write(`data: ${JSON.stringify({ type: 'heartbeat', timestamp: Date.now() })}\n\n`);
      } catch (error) {
        clearInterval(heartbeat);
      }
    }, 30000);

    req.on('close', () => {
      clearInterval(heartbeat);
      const index = sseConnections.indexOf(res);
      if (index !== -1) {
        sseConnections.splice(index, 1);
      }
    });
  });

  // SPA fallback - serve index.html for any non-API routes
  // This ensures React Router works correctly for direct URL access
  app.get('*', (req, res, next) => {
    // Skip API routes
    if (req.path.startsWith('/api/')) {
      return next();
    }

    // For development, let Vite handle static files
    if (process.env.NODE_ENV !== 'production') {
      return next();
    }

    // In production, serve the built React app
    res.sendFile(path.join(__dirname, '../spa/index.html'));
  });

  return app;
}
