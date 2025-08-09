import "dotenv/config";
import express from "express";
import cors from "cors";
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
  handlePipelineStatus
} from "./routes/ml-integration";

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
  app.get("/api/streamlit/status", handleStreamlitStatus);
  app.post("/api/streamlit/start", handleStartStreamlit);
  app.post("/api/streamlit/stop", handleStopStreamlit);
  app.get("/api/superset/status", handleSupersetStatus);
  app.get("/api/pipeline/status", handlePipelineStatus);

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
