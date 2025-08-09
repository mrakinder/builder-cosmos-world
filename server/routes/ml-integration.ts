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
    // Run model training via CLI
    const { stdout, stderr } = await execAsync("python property_monitor_cli.py ml train");
    
    if (stderr) {
      console.error("ML Training error:", stderr);
      return res.status(500).json({ error: "Model training failed" });
    }

    const result = JSON.parse(stdout);
    res.json(result);
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
    const { stdout, stderr } = await execAsync("python property_monitor_cli.py web start");
    
    if (stderr) {
      console.error("Streamlit Start error:", stderr);
      return res.status(500).json({ error: "Failed to start Streamlit" });
    }

    const result = JSON.parse(stdout);
    res.json(result);
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
      ml_trained: false,
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
