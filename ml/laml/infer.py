"""
LightAutoML inference module
===========================

Makes price predictions using trained LightAutoML model.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

from .utils import load_model, validate_input_data, create_sample_request
from .features import FeatureEngineer

logger = logging.getLogger(__name__)

class PricePredictorLAML:
    """Price predictor using trained LightAutoML model"""
    
    def __init__(self, model_path: str = 'models/laml_price.bin'):
        self.model_path = model_path
        self.model_data = None
        self.automl = None
        self.feature_engineer = None
        self.feature_columns = None
        self.metadata = None
        
        self.load_model()
    
    def load_model(self):
        """Load trained model and components"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.model_data = load_model(self.model_path)
            
            self.automl = self.model_data['automl']
            self.feature_engineer = self.model_data['feature_engineer']
            self.feature_columns = self.model_data['feature_columns']
            self.metadata = self.model_data.get('metadata', {})
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            error_msg = f"Failed to load model: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def predict_single(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict price for a single property
        
        Args:
            property_data: Dictionary with property characteristics
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Validate input
            validated_data = validate_input_data(property_data)
            
            # Prepare features
            df = self.feature_engineer.prepare_single_sample(validated_data)
            X = df[self.feature_columns]
            
            # Make prediction
            prediction = self.automl.predict(X)
            
            # Extract prediction value (handle LightAutoML output format)
            if hasattr(prediction, 'data'):
                price_pred = float(prediction.data[0, 0])
            else:
                price_pred = float(prediction[0])
            
            # Calculate confidence intervals (simplified approach)
            # In production, you might want to use more sophisticated uncertainty estimation
            uncertainty = price_pred * 0.15  # Assume 15% uncertainty
            confidence_lower = max(0, price_pred - uncertainty)
            confidence_upper = price_pred + uncertainty
            
            result = {
                'prediction': {
                    'price_usd': round(price_pred, 0),
                    'confidence_interval': {
                        'lower': round(confidence_lower, 0),
                        'upper': round(confidence_upper, 0)
                    },
                    'uncertainty_pct': 15.0
                },
                'input_data': validated_data,
                'model_info': {
                    'model_type': 'LightAutoML',
                    'features_used': len(self.feature_columns),
                    'training_date': self.metadata.get('timestamp'),
                    'validation_mape': self.metadata.get('val_metrics', {}).get('mape')
                }
            }
            
            logger.info(f"Prediction completed: ${price_pred:,.0f}")
            return result
            
        except Exception as e:
            error_msg = f"Prediction failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def predict_batch(self, properties_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predict prices for multiple properties
        
        Args:
            properties_data: List of property data dictionaries
            
        Returns:
            List of prediction results
        """
        results = []
        
        for i, property_data in enumerate(properties_data):
            try:
                result = self.predict_single(property_data)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to predict property {i}: {str(e)}")
                error_result = {
                    'error': str(e),
                    'input_data': property_data
                }
                results.append(error_result)
        
        return results
    
    def get_feature_importance(self) -> List[Dict[str, Any]]:
        """Get feature importance from metadata"""
        return self.metadata.get('feature_importance', [])
    
    def get_model_metrics(self) -> Dict[str, Any]:
        """Get model validation metrics"""
        return self.metadata.get('val_metrics', {})

def predict_price(
    property_data: Dict[str, Any], 
    model_path: str = 'models/laml_price.bin'
) -> Dict[str, Any]:
    """
    Convenience function for single price prediction
    
    Args:
        property_data: Property characteristics
        model_path: Path to trained model
        
    Returns:
        Prediction result
    """
    predictor = PricePredictorLAML(model_path)
    return predictor.predict_single(property_data)

def main():
    """CLI interface for price prediction"""
    parser = argparse.ArgumentParser(description='Predict property prices using LightAutoML')
    parser.add_argument('--input', required=True,
                       help='JSON file with property data')
    parser.add_argument('--output', default='result.json',
                       help='Output JSON file for results')
    parser.add_argument('--model-path', default='models/laml_price.bin',
                       help='Path to trained model')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample input file')
    
    args = parser.parse_args()
    
    if args.create_sample:
        sample_data = create_sample_request()
        with open('sample_request.json', 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        print("Sample request created: sample_request.json")
        return
    
    try:
        # Load input data
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        # Initialize predictor
        predictor = PricePredictorLAML(args.model_path)
        
        # Handle single property or batch
        if isinstance(input_data, dict):
            result = predictor.predict_single(input_data)
        elif isinstance(input_data, list):
            result = predictor.predict_batch(input_data)
        else:
            raise ValueError("Input must be a dictionary (single property) or list (batch)")
        
        # Save results
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        if isinstance(result, dict) and 'prediction' in result:
            price = result['prediction']['price_usd']
            confidence = result['prediction']['confidence_interval']
            print(f"\n✅ Prediction completed!")
            print(f"Estimated price: ${price:,.0f}")
            print(f"Confidence interval: ${confidence['lower']:,.0f} - ${confidence['upper']:,.0f}")
        elif isinstance(result, list):
            successful = sum(1 for r in result if 'prediction' in r)
            print(f"\n✅ Batch prediction completed!")
            print(f"Successful predictions: {successful}/{len(result)}")
        
        print(f"Results saved to: {args.output}")
        
    except Exception as e:
        print(f"\n❌ Prediction failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
