"""
Utilities for LightAutoML module
Progress tracking, evaluation, and logging
"""

import json
import time
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score


class ProgressTracker:
    """
    Real-time progress tracker for ML training
    Writes progress to JSON file for live updates
    """
    
    def __init__(self, progress_file: str):
        self.progress_file = progress_file
        self.start_time = None
        self.current_progress = 0.0
        self.current_stage = "idle"
        self.is_training = False
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(progress_file), exist_ok=True)
        
        # Initialize progress file
        self._write_progress({
            'status': 'idle',
            'progress': 0.0,
            'stage': 'idle',
            'message': 'Ready to start training',
            'start_time': None,
            'elapsed_time': 0,
            'estimated_total_time': None,
            'success': None,
            'error': None
        })
    
    def start_training(self):
        """Start training progress tracking"""
        self.start_time = time.time()
        self.is_training = True
        self.current_progress = 0.0
        self.current_stage = "starting"
        
        self._write_progress({
            'status': 'training',
            'progress': 0.0,
            'stage': 'starting',
            'message': 'Starting LightAutoML training...',
            'start_time': self.start_time,
            'elapsed_time': 0,
            'estimated_total_time': 3600,  # 1 hour estimate
            'success': None,
            'error': None
        })
    
    def update_progress(self, stage: str, progress: float, message: str = ""):
        """
        Update training progress
        
        Args:
            stage: Current training stage
            progress: Progress percentage (0-100)
            message: Status message
        """
        if not self.is_training:
            return
        
        self.current_progress = min(100.0, max(0.0, progress))
        self.current_stage = stage
        
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Estimate remaining time
        if progress > 0:
            estimated_total = (elapsed / progress) * 100
        else:
            estimated_total = 3600  # Default 1 hour
        
        self._write_progress({
            'status': 'training',
            'progress': self.current_progress,
            'stage': stage,
            'message': message or f"Training stage: {stage}",
            'start_time': self.start_time,
            'elapsed_time': elapsed,
            'estimated_total_time': estimated_total,
            'estimated_remaining': max(0, estimated_total - elapsed),
            'success': None,
            'error': None
        })
    
    def complete_training(self, success: bool, final_mape: float = None, error: str = None, message: str = ""):
        """
        Complete training progress tracking
        
        Args:
            success: Whether training succeeded
            final_mape: Final MAPE score if successful
            error: Error message if failed
            message: Completion message
        """
        self.is_training = False
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        self._write_progress({
            'status': 'completed' if success else 'failed',
            'progress': 100.0 if success else self.current_progress,
            'stage': 'completed' if success else 'failed',
            'message': message or ('Training completed successfully' if success else f'Training failed: {error}'),
            'start_time': self.start_time,
            'elapsed_time': elapsed,
            'estimated_total_time': elapsed,
            'estimated_remaining': 0,
            'success': success,
            'error': error,
            'final_mape': final_mape,
            'completion_time': time.time()
        })
    
    def _write_progress(self, progress_data: Dict[str, Any]):
        """Write progress data to JSON file"""
        try:
            progress_data['timestamp'] = time.time()
            progress_data['readable_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error writing progress: {e}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress data"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'status': 'idle',
                'progress': 0.0,
                'stage': 'idle',
                'message': 'No training in progress'
            }


class ModelEvaluator:
    """
    Model evaluation utilities
    """
    
    def __init__(self):
        pass
    
    def evaluate_regression(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Evaluate regression model performance
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dict[str, float]: Evaluation metrics
        """
        metrics = {}
        
        # MAPE - Main metric for this project
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100
        metrics['mape'] = round(mape, 2)
        
        # RMSE
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        metrics['rmse'] = round(rmse, 2)
        
        # R²
        r2 = r2_score(y_true, y_pred)
        metrics['r2'] = round(r2, 4)
        
        # MAE
        mae = np.mean(np.abs(y_true - y_pred))
        metrics['mae'] = round(mae, 2)
        
        # Median APE
        ape = np.abs((y_true - y_pred) / y_true) * 100
        median_ape = np.median(ape)
        metrics['median_ape'] = round(median_ape, 2)
        
        # Max error
        max_error = np.max(np.abs(y_true - y_pred))
        metrics['max_error'] = round(max_error, 2)
        
        # Residual analysis
        residuals = y_true - y_pred
        metrics['residual_mean'] = round(np.mean(residuals), 2)
        metrics['residual_std'] = round(np.std(residuals), 2)
        
        return metrics
    
    def evaluate_by_segments(self, y_true: np.ndarray, y_pred: np.ndarray, 
                           segments: pd.Series) -> Dict[str, Dict[str, float]]:
        """
        Evaluate model performance by segments (e.g., districts, price ranges)
        
        Args:
            y_true: True values
            y_pred: Predicted values
            segments: Segment labels
            
        Returns:
            Dict[str, Dict[str, float]]: Metrics by segment
        """
        segment_metrics = {}
        
        for segment in segments.unique():
            if pd.isna(segment):
                continue
                
            mask = segments == segment
            if mask.sum() < 5:  # Skip segments with too few samples
                continue
            
            y_true_seg = y_true[mask]
            y_pred_seg = y_pred[mask]
            
            segment_metrics[str(segment)] = self.evaluate_regression(y_true_seg, y_pred_seg)
            segment_metrics[str(segment)]['sample_count'] = int(mask.sum())
        
        return segment_metrics
    
    def calculate_prediction_intervals(self, y_pred: np.ndarray, 
                                     confidence: float = 0.8) -> Dict[str, np.ndarray]:
        """
        Calculate prediction intervals (simplified approach)
        
        Args:
            y_pred: Predictions
            confidence: Confidence level
            
        Returns:
            Dict[str, np.ndarray]: Lower and upper bounds
        """
        # Simplified approach - use std of predictions
        pred_std = np.std(y_pred)
        
        # Z-score for confidence interval
        from scipy import stats
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        margin = z_score * pred_std
        
        return {
            'lower': y_pred - margin,
            'upper': y_pred + margin,
            'margin': margin
        }


class Logger:
    """
    Custom logger for ML training
    """
    
    def __init__(self, log_file: str, level: str = "INFO"):
        self.logger = logging.getLogger("laml_trainer")
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Create log directory if not exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, level.upper()))
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def debug(self, message: str):
        self.logger.debug(message)


class ModelValidator:
    """
    Cross-validation and model validation utilities
    """
    
    def __init__(self):
        pass
    
    def time_series_split_validate(self, X: pd.DataFrame, y: pd.Series, 
                                  model_class, n_splits: int = 5) -> Dict[str, Any]:
        """
        Perform time series cross-validation
        
        Args:
            X: Feature matrix
            y: Target variable
            model_class: Model class to validate
            n_splits: Number of splits
            
        Returns:
            Dict[str, Any]: Validation results
        """
        from sklearn.model_selection import TimeSeriesSplit
        
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        fold_metrics = []
        
        for i, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train_fold = X.iloc[train_idx]
            X_val_fold = X.iloc[val_idx]
            y_train_fold = y.iloc[train_idx]
            y_val_fold = y.iloc[val_idx]
            
            # Train model
            model = model_class()
            model.fit(X_train_fold, y_train_fold)
            
            # Predict
            y_pred_fold = model.predict(X_val_fold)
            
            # Evaluate
            evaluator = ModelEvaluator()
            metrics = evaluator.evaluate_regression(y_val_fold.values, y_pred_fold)
            metrics['fold'] = i + 1
            metrics['train_size'] = len(train_idx)
            metrics['val_size'] = len(val_idx)
            
            fold_metrics.append(metrics)
        
        # Aggregate metrics
        cv_results = {
            'fold_metrics': fold_metrics,
            'mean_mape': np.mean([m['mape'] for m in fold_metrics]),
            'std_mape': np.std([m['mape'] for m in fold_metrics]),
            'mean_r2': np.mean([m['r2'] for m in fold_metrics]),
            'std_r2': np.std([m['r2'] for m in fold_metrics])
        }
        
        return cv_results


def load_training_progress() -> Dict[str, Any]:
    """
    Load current training progress from file
    
    Returns:
        Dict[str, Any]: Current progress data
    """
    progress_file = "ml/reports/training_progress.json"
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            'status': 'idle',
            'progress': 0.0,
            'stage': 'idle',
            'message': 'No training in progress'
        }


def format_time(seconds: float) -> str:
    """
    Format seconds to human-readable time string
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def save_model_metadata(model_path: str, metadata: Dict[str, Any]):
    """
    Save model metadata to accompany saved model
    
    Args:
        model_path: Path to saved model
        metadata: Metadata to save
    """
    metadata_path = model_path.replace('.pkl', '_metadata.json')
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
