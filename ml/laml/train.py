"""
LightAutoML model training module
================================

Trains automated ML model for real estate price prediction.
"""

import os
import sys
import argparse
import json
import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

# LightAutoML imports
try:
    from lightautoml.automl.presets.tabular_presets import TabularAutoML
    from lightautoml.tasks import Task
    from lightautoml.report.report_deco import ReportDeco
except ImportError:
    print("LightAutoML not installed. Installing...")
    os.system("pip install lightautoml")
    from lightautoml.automl.presets.tabular_presets import TabularAutoML
    from lightautoml.tasks import Task
    from lightautoml.report.report_deco import ReportDeco

from .utils import load_data, split_data_by_time, save_model, calculate_metrics
from .features import FeatureEngineer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_price_model(
    data_source: str = 'sqlite',
    data_path: str = 'data/olx_offers.sqlite',
    model_path: str = 'models/laml_price.bin',
    timeout: int = 300,
    cpu_limit: int = 4
) -> dict:
    """
    Train LightAutoML model for price prediction
    
    Args:
        data_source: 'sqlite' or 'csv'
        data_path: Path to data source
        model_path: Where to save trained model
        timeout: Training timeout in seconds
        cpu_limit: CPU cores limit
        
    Returns:
        Training results dictionary
    """
    
    logger.info("Starting LightAutoML model training")
    start_time = datetime.now()
    
    try:
        # Load and prepare data
        logger.info(f"Loading data from {data_source}:{data_path}")
        df = load_data(data_source, data_path)
        
        if len(df) < 50:
            raise ValueError(f"Insufficient data for training: {len(df)} samples (minimum 50 required)")
        
        # Feature engineering
        logger.info("Preparing features...")
        engineer = FeatureEngineer()
        df_processed = engineer.prepare_features(df, is_training=True)
        
        # Split data by time
        train_df, val_df = split_data_by_time(df_processed, train_ratio=0.8)
        
        # Prepare training data
        feature_columns = engineer.get_feature_names()
        X_train = train_df[feature_columns]
        y_train = train_df['price_value_usd']
        X_val = val_df[feature_columns]
        y_val = val_df['price_value_usd']
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Validation set: {len(X_val)} samples")
        logger.info(f"Features: {len(feature_columns)} columns")
        
        # Configure LightAutoML
        task = Task('reg')  # Regression task
        
        automl = TabularAutoML(
            task=task,
            timeout=timeout,
            cpu_limit=cpu_limit,
            general_params={
                'use_algos': [['lgb', 'cb']],  # Use LightGBM and CatBoost
                'nested_cv': False,
                'skip_conn': False
            },
            reader_params={'n_jobs': cpu_limit, 'cv': 3}
        )
        
        # Train model
        logger.info("Training AutoML model...")
        oof_pred = automl.fit_predict(
            train_data=train_df[feature_columns + ['price_value_usd']],
            valid_data=val_df[feature_columns + ['price_value_usd']],
            verbose=1
        )
        
        # Make predictions on validation set
        val_pred = automl.predict(X_val)
        
        # Calculate metrics
        train_metrics = calculate_metrics(y_train.values, oof_pred.data[:, 0])
        val_metrics = calculate_metrics(y_val.values, val_pred.data[:, 0])
        
        logger.info(f"Training MAPE: {train_metrics['mape']:.2f}%")
        logger.info(f"Validation MAPE: {val_metrics['mape']:.2f}%")
        logger.info(f"Training RMSE: ${train_metrics['rmse']:,.0f}")
        logger.info(f"Validation RMSE: ${val_metrics['rmse']:,.0f}")
        
        # Get feature importance
        try:
            feature_importance = automl.get_feature_scores()
            feature_importance_df = pd.DataFrame({
                'feature': feature_importance.index,
                'importance': feature_importance.values
            }).sort_values('importance', ascending=False)
        except:
            logger.warning("Could not extract feature importance")
            feature_importance_df = pd.DataFrame({
                'feature': feature_columns,
                'importance': [0.0] * len(feature_columns)
            })
        
        # Prepare results
        results = {
            'model_type': 'LightAutoML',
            'training_time': str(datetime.now() - start_time),
            'train_samples': len(train_df),
            'val_samples': len(val_df),
            'features_count': len(feature_columns),
            'train_metrics': train_metrics,
            'val_metrics': val_metrics,
            'feature_importance': feature_importance_df.to_dict('records'),
            'model_path': model_path,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save model and metadata
        logger.info(f"Saving model to {model_path}")
        model_data = {
            'automl': automl,
            'feature_engineer': engineer,
            'feature_columns': feature_columns,
            'metadata': results
        }
        save_model(model_data, model_path, results)
        
        # Save reports
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        
        # Save metrics
        metrics_path = reports_dir / 'laml_metrics.json'
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save feature importance
        importance_path = reports_dir / 'laml_feature_importance.csv'
        feature_importance_df.to_csv(importance_path, index=False, encoding='utf-8')
        
        logger.info("Training completed successfully!")
        
        # Check if MAPE acceptance criteria is met
        if val_metrics['mape'] <= 15.0:
            logger.info(f"✅ Model meets acceptance criteria (MAPE ≤ 15%)")
        else:
            logger.warning(f"⚠️ Model MAPE ({val_metrics['mape']:.2f}%) exceeds 15% but model saved anyway")
        
        return results
        
    except Exception as e:
        error_msg = f"Training failed: {str(e)}"
        logger.error(error_msg)
        
        # Save error results
        error_results = {
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        
        reports_dir = Path('reports')
        reports_dir.mkdir(exist_ok=True)
        with open(reports_dir / 'laml_metrics.json', 'w') as f:
            json.dump(error_results, f, indent=2)
        
        raise

def main():
    """CLI interface for model training"""
    parser = argparse.ArgumentParser(description='Train LightAutoML price prediction model')
    parser.add_argument('--src', choices=['sqlite', 'csv'], default='sqlite', 
                       help='Data source type')
    parser.add_argument('--path', default='data/olx_offers.sqlite',
                       help='Path to data source')
    parser.add_argument('--model-path', default='models/laml_price.bin',
                       help='Where to save trained model')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Training timeout in seconds')
    parser.add_argument('--cpu-limit', type=int, default=4,
                       help='CPU cores limit')
    
    args = parser.parse_args()
    
    try:
        results = train_price_model(
            data_source=args.src,
            data_path=args.path,
            model_path=args.model_path,
            timeout=args.timeout,
            cpu_limit=args.cpu_limit
        )
        
        print(f"\n✅ Training completed successfully!")
        print(f"Validation MAPE: {results['val_metrics']['mape']:.2f}%")
        print(f"Validation RMSE: ${results['val_metrics']['rmse']:,.0f}")
        print(f"Model saved to: {results['model_path']}")
        
    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
