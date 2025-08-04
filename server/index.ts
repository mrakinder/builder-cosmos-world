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
  handlePriceTrends
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

  return app;
}
