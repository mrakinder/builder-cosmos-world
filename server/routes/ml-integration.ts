import { Request, Response } from "express";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs/promises";
import path from "path";

const execAsync = promisify(exec);

// ML Model Prediction endpoint
export async function handleMLPredict(req: Request, res: Response) {
  try {
    const { area, district, rooms, floor, building_type, renovation } = req.body;
    
    if (!area || !district) {
      return res.status(400).json({ error: "Area and district are required" });
    }

    // Run ML inference via CLI
    const { stdout, stderr } = await execAsync(`python property_monitor_cli.py ml infer --area ${area} --district "${district}" --rooms ${rooms || 2} --floor ${floor || 1} --building_type "${building_type || 'apartment'}" --renovation "${renovation || 'good'}"`);
    
    if (stderr) {
      console.error("ML Prediction error:", stderr);
      return res.status(500).json({ error: "Model prediction failed" });
    }

    const prediction = JSON.parse(stdout);
    res.json(prediction);
  } catch (error) {
    console.error("ML Predict error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}

// Prophet Forecasting endpoint
export async function handleProphetForecast(req: Request, res: Response) {
  try {
    const { district } = req.query;
    
    // Run Prophet forecasting via CLI
    const command = district 
      ? `python property_monitor_cli.py forecasting predict --district "${district}"`
      : `python property_monitor_cli.py forecasting predict --all`;
    
    const { stdout, stderr } = await execAsync(command);
    
    if (stderr) {
      console.error("Prophet Forecast error:", stderr);
      return res.status(500).json({ error: "Forecasting failed" });
    }

    const forecast = JSON.parse(stdout);
    res.json(forecast);
  } catch (error) {
    console.error("Prophet Forecast error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}

// Train ML Model endpoint
export async function handleTrainML(req: Request, res: Response) {
  try {
    // In development, return mock success response and start progress tracking
    if (process.env.NODE_ENV !== 'production') {
      startTrainingProgress(); // Start the progress simulation

      res.json({
        success: true,
        message: "LightAutoML навчання запущено!",
        mape: "14.2",
        target_mape: 15.0,
        status: "training_started"
      });
      return;
    }

    // Run model training via CLI
    const { stdout, stderr } = await execAsync("python property_monitor_cli.py ml train");

    if (stderr) {
      console.error("ML Training error:", stderr);
      return res.status(500).json({ error: "Model training failed" });
    }

    const result = JSON.parse(stdout);
    res.json({ success: true, ...result });
  } catch (error) {
    console.error("ML Training error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}

// Get Streamlit URL endpoint
export async function handleStreamlitStatus(req: Request, res: Response) {
  try {
    // Check if Streamlit is running
    const { stdout } = await execAsync("python property_monitor_cli.py web status");
    const status = JSON.parse(stdout);
    res.json(status);
  } catch (error) {
    res.json({ running: false, url: null });
  }
}

// Start Streamlit endpoint
export async function handleStartStreamlit(req: Request, res: Response) {
  try {
    // In development, return mock success response
    if (process.env.NODE_ENV !== 'production') {
      res.json({
        success: true,
        message: "Streamlit запущено!",
        url: "http://localhost:8501",
        status: "running"
      });
      return;
    }

    const { stdout, stderr } = await execAsync("python property_monitor_cli.py web start");

    if (stderr) {
      console.error("Streamlit Start error:", stderr);
      return res.status(500).json({ error: "Failed to start Streamlit" });
    }

    const result = JSON.parse(stdout);
    res.json({ success: true, ...result });
  } catch (error) {
    console.error("Streamlit Start error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}

// Stop Streamlit endpoint
export async function handleStopStreamlit(req: Request, res: Response) {
  try {
    await execAsync("python property_monitor_cli.py web stop");
    res.json({ success: true, message: "Streamlit stopped" });
  } catch (error) {
    console.error("Streamlit Stop error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}

// Store training start time globally
let trainingStartTime: number | null = null;

// ML Training Progress endpoint
export async function handleMLProgress(req: Request, res: Response) {
  try {
    // In development, simulate progressive training
    if (process.env.NODE_ENV !== 'production') {
      if (!trainingStartTime) {
        // No training in progress
        res.json({ status: "idle", progress: 0, message: "No training in progress" });
        return;
      }

      const elapsed = (Date.now() - trainingStartTime) / 1000; // seconds
      const progress = Math.min(Math.floor((elapsed / 30) * 100), 100); // 30 seconds = 100%

      if (progress >= 100) {
        // Training completed, reset start time
        trainingStartTime = null;
        res.json({
          status: "completed",
          progress: 100,
          stage: "completed",
          message: "Training completed successfully"
        });
        return;
      }

      res.json({
        status: "training",
        progress: progress,
        stage: progress < 25 ? "loading_data" :
               progress < 50 ? "feature_engineering" :
               progress < 75 ? "model_training" : "evaluation",
        message: `Training in progress: ${progress}%`
      });
      return;
    }

    // In production, get real progress from CLI
    const { stdout } = await execAsync("python property_monitor_cli.py ml progress");
    const progress = JSON.parse(stdout);
    res.json(progress);
  } catch (error) {
    res.json({ status: "idle", progress: 0, message: "No training in progress" });
  }
}

// Function to start training progress tracking
export function startTrainingProgress() {
  trainingStartTime = Date.now();
}

// Get Superset status
export async function handleSupersetStatus(req: Request, res: Response) {
  try {
    const { stdout } = await execAsync("python property_monitor_cli.py superset status");
    const status = JSON.parse(stdout);
    res.json(status);
  } catch (error) {
    res.json({ running: false, url: null });
  }
}

// System pipeline status
export async function handlePipelineStatus(req: Request, res: Response) {
  try {
    // In development, return mock data instead of trying to execute Python CLI
    if (process.env.NODE_ENV !== 'production') {
      res.json({
        botasaurus_ready: false,
        lightautoml_trained: false,
        prophet_ready: false,
        streamlit_running: false,
        superset_running: false,
        scraper_status: 'idle',
        database_ready: true,
        last_updated: new Date().toISOString()
      });
      return;
    }

    const { stdout } = await execAsync("python property_monitor_cli.py status");
    const status = JSON.parse(stdout);
    res.json(status);
  } catch (error) {
    console.error("Pipeline Status error:", error);
    // Fallback to mock data on error
    res.json({
      botasaurus_ready: false,
      lightautoml_trained: false,
      prophet_ready: false,
      streamlit_running: false,
      superset_running: false,
      scraper_status: 'idle',
      database_ready: true,
      last_updated: new Date().toISOString(),
      error: error.message
    });
  }
}
