"""
LightAutoML Training Module - Module 2
Automated ML for price prediction with real-time progress tracking
Target: MAPE ≤ 15%
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, TimeSeriesSplit
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
import joblib

# LightAutoML imports
from lightautoml.automl.presets.tabular_presets import TabularAutoML
from lightautoml.tasks import Task
from lightautoml.ml_algo.dl_utils import save_sklearn_pipeline

from .features import FeatureEngineer
from .utils import ProgressTracker, ModelEvaluator, Logger


class LightAutoMLTrainer:
    """
    LightAutoML trainer with real-time progress tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.logger = Logger("ml/reports/training.log")
        self.progress_tracker = ProgressTracker("ml/reports/training_progress.json")
        self.feature_engineer = FeatureEngineer()
        self.evaluator = ModelEvaluator()
        
        # Model and data
        self.model = None
        self.feature_names = []
        self.training_data = None
        self.test_data = None
        
        # Results
        self.training_results = {}
        
    def _default_config(self) -> Dict[str, Any]:
        """Default training configuration"""
        return {
            'target_column': 'price_usd',
            'test_size': 0.2,
            'validation_size': 0.2,
            'random_state': 42,
            'target_mape': 15.0,
            'timeout': 3600,  # 1 hour
            'cv_folds': 5,
            'model_path': 'models/laml_price_model.pkl',
            'metrics_path': 'ml/reports/laml_metrics.json',
            'feature_importance_path': 'ml/reports/laml_feature_importance.csv',
            'min_samples': 100,
            'max_samples': 50000
        }
    
    def train_model(self, data_source: str = "database") -> Dict[str, Any]:
        """
        Train LightAutoML model with real-time progress tracking
        
        Args:
            data_source: Source of data ("database" or path to CSV)
            
        Returns:
            Dict[str, Any]: Training results with metrics
        """
        try:
            self.progress_tracker.start_training()
            self.logger.info("🚀 Starting LightAutoML training with real-time progress")
            
            # Stage 1: Load and prepare data (0-20%)
            self.progress_tracker.update_progress(
                stage="load_data",
                progress=5.0,
                message="Loading training data from source..."
            )
            
            df = self._load_data(data_source)
            if df is None or len(df) < self.config['min_samples']:
                raise ValueError(f"Insufficient data: {len(df) if df is not None else 0} samples")
            
            self.progress_tracker.update_progress(
                stage="load_data",
                progress=15.0,
                message=f"Loaded {len(df)} samples for training"
            )
            
            # Stage 2: Feature engineering (20-40%)
            self.progress_tracker.update_progress(
                stage="feature_engineering",
                progress=25.0,
                message="Performing feature engineering..."
            )
            
            X, y = self._prepare_features(df)
            
            self.progress_tracker.update_progress(
                stage="feature_engineering",
                progress=35.0,
                message=f"Created {X.shape[1]} features from {len(X)} samples"
            )
            
            # Stage 3: Data splitting (40-45%)
            self.progress_tracker.update_progress(
                stage="data_splitting",
                progress=42.0,
                message="Splitting data into train/validation/test sets..."
            )
            
            X_train, X_test, y_train, y_test = self._split_data(X, y)
            
            # Stage 4: Model initialization and training (45-85%)
            self.progress_tracker.update_progress(
                stage="model_initialization",
                progress=48.0,
                message="Initializing LightAutoML model..."
            )
            
            # Initialize LightAutoML
            automl = self._initialize_automl()
            
            self.progress_tracker.update_progress(
                stage="model_training",
                progress=55.0,
                message="Training LightAutoML model (this may take time)..."
            )
            
            # Train model with progress updates
            self.model = self._train_with_progress(automl, X_train, y_train)
            
            self.progress_tracker.update_progress(
                stage="model_training",
                progress=80.0,
                message="Model training completed, evaluating performance..."
            )
            
            # Stage 5: Model evaluation (85-95%)
            self.progress_tracker.update_progress(
                stage="model_evaluation",
                progress=87.0,
                message="Evaluating model performance on test set..."
            )
            
            metrics = self._evaluate_model(X_test, y_test)
            
            # Stage 6: Save model and results (95-100%)
            self.progress_tracker.update_progress(
                stage="saving_model",
                progress=95.0,
                message="Saving model and generating reports..."
            )
            
            self._save_model_and_results(metrics)
            
            # Complete training
            self.progress_tracker.complete_training(
                success=True,
                final_mape=metrics['mape'],
                message=f"Training completed! MAPE: {metrics['mape']:.2f}%"
            )
            
            self.logger.info(f"✅ Training completed successfully! MAPE: {metrics['mape']:.2f}%")
            
            return {
                'success': True,
                'metrics': metrics,
                'model_path': self.config['model_path'],
                'feature_count': len(self.feature_names),
                'training_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            self.progress_tracker.complete_training(
                success=False,
                error=error_msg
            )
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def _load_data(self, source: str) -> Optional[pd.DataFrame]:
        """Load training data from source"""
        try:
            if source == "database":
                # Load from SQLite database
                import sqlite3
                conn = sqlite3.connect("data/olx_offers.sqlite")
                
                query = """
                SELECT * FROM properties 
                WHERE is_active = 1 
                AND price_usd IS NOT NULL 
                AND price_usd > 0 
                AND area IS NOT NULL 
                AND area > 0
                AND currency = 'USD'
                ORDER BY scraped_at DESC
                """
                
                df = pd.read_sql_query(query, conn)
                conn.close()
                
            elif source.endswith('.csv'):
                df = pd.read_csv(source)
            else:
                raise ValueError(f"Unsupported data source: {source}")
            
            self.logger.info(f"📊 Loaded {len(df)} records from {source}")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error loading data: {str(e)}")
            return None
    
    def _prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features for training"""
        try:
            # Feature engineering
            features_df = self.feature_engineer.create_features(df)
            
            # Target variable
            target = features_df[self.config['target_column']]
            
            # Feature matrix (exclude target)
            features = features_df.drop(columns=[self.config['target_column']])
            
            # Store feature names
            self.feature_names = features.columns.tolist()
            
            self.logger.info(f"🔧 Feature engineering completed: {len(self.feature_names)} features")
            
            return features, target
            
        except Exception as e:
            self.logger.error(f"❌ Error in feature engineering: {str(e)}")
            raise
    
    def _split_data(self, X: pd.DataFrame, y: pd.Series) -> Tuple:
        """Split data into train/test sets with temporal ordering"""
        try:
            # Use time-based split to prevent data leakage
            split_index = int(len(X) * (1 - self.config['test_size']))
            
            X_train = X.iloc[:split_index]
            X_test = X.iloc[split_index:]
            y_train = y.iloc[:split_index]
            y_test = y.iloc[split_index:]
            
            self.logger.info(f"📊 Data split - Train: {len(X_train)}, Test: {len(X_test)}")
            
            return X_train, X_test, y_train, y_test
            
        except Exception as e:
            self.logger.error(f"❌ Error splitting data: {str(e)}")
            raise
    
    def _initialize_automl(self) -> TabularAutoML:
        """Initialize LightAutoML model"""
        try:
            # Create task
            task = Task('reg', metric='mape')
            
            # Initialize AutoML
            automl = TabularAutoML(
                task=task,
                timeout=self.config['timeout'],
                cpu_limit=os.cpu_count(),
                gpu_ids=None,  # Use CPU only for stability
                verbose=1
            )
            
            self.logger.info("🤖 LightAutoML initialized")
            return automl
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing AutoML: {str(e)}")
            raise
    
    def _train_with_progress(self, automl: TabularAutoML, X_train: pd.DataFrame, y_train: pd.Series):
        """Train model with progress monitoring"""
        try:
            # Create progress monitoring
            start_time = time.time()
            
            def progress_callback():
                elapsed = time.time() - start_time
                estimated_total = self.config['timeout']
                progress = min(80.0, 55.0 + (elapsed / estimated_total) * 25.0)
                
                self.progress_tracker.update_progress(
                    stage="model_training",
                    progress=progress,
                    message=f"Training in progress... {elapsed:.0f}s elapsed"
                )
            
            # Start training
            self.logger.info("🏋️ Starting LightAutoML training...")
            
            # Fit model
            model = automl.fit_predict(
                X_train, y_train,
                valid_data=None,  # AutoML will handle validation internally
                verbose=1
            )
            
            self.logger.info("✅ LightAutoML training completed")
            return model
            
        except Exception as e:
            self.logger.error(f"❌ Error during model training: {str(e)}")
            raise
    
    def _evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate trained model"""
        try:
            # Make predictions
            predictions = self.model.predict(X_test)
            
            # Calculate metrics
            mape = mean_absolute_percentage_error(y_test, predictions) * 100
            rmse = np.sqrt(mean_squared_error(y_test, predictions))
            r2 = r2_score(y_test, predictions)
            mae = np.mean(np.abs(y_test - predictions))
            
            metrics = {
                'mape': round(mape, 2),
                'rmse': round(rmse, 2),
                'r2': round(r2, 4),
                'mae': round(mae, 2),
                'target_achieved': mape <= self.config['target_mape'],
                'test_samples': len(X_test),
                'training_date': datetime.now().isoformat()
            }
            
            self.logger.info(f"📊 Model evaluation: MAPE={mape:.2f}%, R²={r2:.4f}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating model: {str(e)}")
            raise
    
    def _save_model_and_results(self, metrics: Dict[str, float]):
        """Save model and training results"""
        try:
            # Ensure directories exist
            os.makedirs(os.path.dirname(self.config['model_path']), exist_ok=True)
            os.makedirs("ml/reports", exist_ok=True)
            
            # Save model
            joblib.dump(self.model, self.config['model_path'])
            self.logger.info(f"💾 Model saved to {self.config['model_path']}")
            
            # Save metrics
            with open(self.config['metrics_path'], 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)
            
            # Save feature importance (if available)
            try:
                if hasattr(self.model, 'feature_importances_'):
                    importance_df = pd.DataFrame({
                        'feature': self.feature_names,
                        'importance': self.model.feature_importances_
                    }).sort_values('importance', ascending=False)
                    
                    importance_df.to_csv(self.config['feature_importance_path'], index=False)
                    self.logger.info(f"📊 Feature importance saved to {self.config['feature_importance_path']}")
            except:
                self.logger.warning("⚠️ Could not extract feature importance")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving model and results: {str(e)}")
            raise


def train_price_model(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main entry point for training price prediction model
    
    Args:
        config: Training configuration
        
    Returns:
        Dict[str, Any]: Training results
    """
    trainer = LightAutoMLTrainer(config)
    return trainer.train_model()


if __name__ == "__main__":
    # Run training standalone
    results = train_price_model()
    print(f"Training results: {results}")
