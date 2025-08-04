import { RequestHandler } from "express";

// Mock model status storage
let modelStatus = {
  lastTraining: new Date(),
  isTraining: false,
  accuracy: 0.85,
  r2: 0.78,
  mae: 5420,
  rmse: 8950
};

export const handleRetrainModel: RequestHandler = (req, res) => {
  if (modelStatus.isTraining) {
    return res.status(400).json({ 
      error: 'Модель вже тренується', 
      status: 'training' 
    });
  }

  modelStatus.isTraining = true;

  // Simulate training process
  setTimeout(() => {
    modelStatus = {
      lastTraining: new Date(),
      isTraining: false,
      accuracy: 0.85 + (Math.random() * 0.1), // 85-95%
      r2: 0.78 + (Math.random() * 0.15), // 78-93%
      mae: 5000 + (Math.random() * 2000), // 5000-7000
      rmse: 8000 + (Math.random() * 3000) // 8000-11000
    };
    console.log('Model retraining completed');
  }, 5000); // Complete after 5 seconds

  res.json({ 
    message: 'Перетренування моделі розпочато', 
    estimatedTime: '3-7 хвилин',
    status: 'training'
  });
};

export const handleRetrainAdvancedModel: RequestHandler = (req, res) => {
  if (modelStatus.isTraining) {
    return res.status(400).json({ 
      error: 'Модель вже тренується', 
      status: 'training' 
    });
  }

  modelStatus.isTraining = true;

  // Simulate advanced training process
  setTimeout(() => {
    modelStatus = {
      lastTraining: new Date(),
      isTraining: false,
      accuracy: 0.88 + (Math.random() * 0.08), // 88-96%
      r2: 0.82 + (Math.random() * 0.12), // 82-94%
      mae: 4500 + (Math.random() * 1500), // 4500-6000
      rmse: 7500 + (Math.random() * 2500) // 7500-10000
    };
    console.log('Advanced model retraining completed');
  }, 7000); // Complete after 7 seconds

  res.json({ 
    message: 'Перетренування розширеної моделі розпочато', 
    estimatedTime: '5-10 хвилин',
    status: 'training'
  });
};

export const handleModelInfo: RequestHandler = (req, res) => {
  res.json({
    lastTraining: modelStatus.lastTraining,
    isTraining: modelStatus.isTraining,
    accuracy: Math.round(modelStatus.accuracy * 100) / 100,
    r2: Math.round(modelStatus.r2 * 100) / 100,
    mae: Math.round(modelStatus.mae),
    rmse: Math.round(modelStatus.rmse),
    status: modelStatus.isTraining ? 'training' : 'ready'
  });
};

export const handleModelComparison: RequestHandler = (req, res) => {
  const baseModel = {
    name: 'Real Data Model',
    accuracy: modelStatus.accuracy,
    r2: modelStatus.r2,
    mae: modelStatus.mae,
    rmse: modelStatus.rmse
  };

  const advancedModel = {
    name: 'Advanced Model',
    accuracy: modelStatus.accuracy + 0.03,
    r2: modelStatus.r2 + 0.04,
    mae: modelStatus.mae - 500,
    rmse: modelStatus.rmse - 700
  };

  const xgbModel = {
    name: 'XGBoost Model',
    accuracy: modelStatus.accuracy + 0.05,
    r2: modelStatus.r2 + 0.06,
    mae: modelStatus.mae - 800,
    rmse: modelStatus.rmse - 1000
  };

  res.json({
    models: [baseModel, advancedModel, xgbModel],
    bestModel: xgbModel.name,
    comparisonDate: new Date()
  });
};
