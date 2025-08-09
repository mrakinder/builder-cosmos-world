"""
LightAutoML Inference Module
Real-time price prediction for individual properties
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List
import warnings
warnings.filterwarnings('ignore')

from .features import FeatureEngineer
from .utils import Logger, ModelEvaluator


class PricePredictionInference:
    """
    Real-time price prediction inference engine
    """
    
    def __init__(self, model_path: str = "models/laml_price_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.logger = Logger("ml/reports/inference.log")
        self.evaluator = ModelEvaluator()
        
        # Model metadata
        self.model_metadata = {}
        self.feature_names = []
        
        # Load model if exists
        self._load_model()
    
    def _load_model(self):
        """Load trained model and metadata"""
        try:
            if not os.path.exists(self.model_path):
                self.logger.warning(f"⚠️ Model file not found: {self.model_path}")
                return False
            
            # Load model
            self.model = joblib.load(self.model_path)
            self.logger.info(f"✅ Model loaded from {self.model_path}")
            
            # Load metadata
            metadata_path = self.model_path.replace('.pkl', '_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.model_metadata = json.load(f)
                self.logger.info("✅ Model metadata loaded")
            
            # Load metrics
            metrics_path = "ml/reports/laml_metrics.json"
            if os.path.exists(metrics_path):
                with open(metrics_path, 'r', encoding='utf-8') as f:
                    self.model_metadata.update(json.load(f))
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error loading model: {str(e)}")
            return False
    
    def predict_price(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict property price with confidence intervals
        
        Args:
            property_data: Property characteristics
            
        Returns:
            Dict[str, Any]: Prediction results
        """
        try:
            if self.model is None:
                return {
                    'success': False,
                    'error': 'Model not loaded. Please train the model first.',
                    'predicted_price': None
                }
            
            # Prepare features
            features_df = self._prepare_inference_features(property_data)
            
            if features_df is None or len(features_df) == 0:
                return {
                    'success': False,
                    'error': 'Failed to prepare features for prediction',
                    'predicted_price': None
                }
            
            # Make prediction
            prediction = self.model.predict(features_df)
            predicted_price = float(prediction[0]) if len(prediction) > 0 else None
            
            if predicted_price is None or predicted_price <= 0:
                return {
                    'success': False,
                    'error': 'Invalid prediction result',
                    'predicted_price': None
                }
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                predicted_price, property_data
            )
            
            # Get feature importance for explanation
            feature_importance = self._get_prediction_explanation(features_df)
            
            # Find similar properties
            similar_properties = self._find_similar_properties(property_data)
            
            result = {
                'success': True,
                'predicted_price': round(predicted_price, 2),
                'currency': 'USD',
                'confidence_intervals': confidence_intervals,
                'feature_importance': feature_importance,
                'similar_properties': similar_properties,
                'model_info': {
                    'model_type': 'LightAutoML',
                    'training_date': self.model_metadata.get('training_date'),
                    'model_mape': self.model_metadata.get('mape'),
                    'target_achieved': self.model_metadata.get('target_achieved', False)
                },
                'prediction_metadata': {
                    'prediction_time': datetime.now().isoformat(),
                    'model_version': self.model_metadata.get('version', '1.0'),
                    'features_used': len(features_df.columns)
                }
            }
            
            self.logger.info(f"✅ Price prediction: ${predicted_price:.2f} for {property_data.get('district', 'unknown')} property")
            
            return result
            
        except Exception as e:
            error_msg = f"Error in price prediction: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'predicted_price': None
            }
    
    def _prepare_inference_features(self, property_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Prepare features for inference"""
        try:
            # Add required fields with defaults
            inference_data = {
                'area': property_data.get('area', 50),
                'rooms': property_data.get('rooms', 2),
                'floor': property_data.get('floor', 1),
                'total_floors': property_data.get('total_floors', 9),
                'district': property_data.get('district', 'Центр'),
                'street': property_data.get('street'),
                'building_type': property_data.get('building_type', 'квартира'),
                'renovation_status': property_data.get('renovation_status', 'хороший'),
                'seller_type': property_data.get('seller_type', 'owner'),
                'listing_type': property_data.get('listing_type', 'sale'),
                'is_promoted': property_data.get('is_promoted', False),
                'title': property_data.get('title', 'Квартира'),
                'description': property_data.get('description', ''),
                'scraped_at': datetime.now(),
                'price_usd': 50000  # Dummy value for feature engineering
            }
            
            # Create features using the same pipeline as training
            features_df = self.feature_engineer.create_inference_features(inference_data)
            
            return features_df
            
        except Exception as e:
            self.logger.error(f"❌ Error preparing inference features: {str(e)}")
            return None
    
    def _calculate_confidence_intervals(self, predicted_price: float, 
                                      property_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence intervals for prediction"""
        try:
            # Simplified confidence intervals based on model MAPE
            model_mape = self.model_metadata.get('mape', 15.0)
            
            # Calculate margin of error (conservative approach)
            margin_percentage = model_mape / 100
            margin = predicted_price * margin_percentage
            
            # 80% confidence interval
            lower_80 = max(0, predicted_price - margin)
            upper_80 = predicted_price + margin
            
            # 95% confidence interval (wider)
            margin_95 = margin * 1.96
            lower_95 = max(0, predicted_price - margin_95)
            upper_95 = predicted_price + margin_95
            
            return {
                'lower_80': round(lower_80, 2),
                'upper_80': round(upper_80, 2),
                'lower_95': round(lower_95, 2),
                'upper_95': round(upper_95, 2),
                'margin_percentage': round(margin_percentage * 100, 1)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating confidence intervals: {str(e)}")
            return {
                'lower_80': predicted_price * 0.85,
                'upper_80': predicted_price * 1.15,
                'lower_95': predicted_price * 0.75,
                'upper_95': predicted_price * 1.25,
                'margin_percentage': 15.0
            }
    
    def _get_prediction_explanation(self, features_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Get feature importance for prediction explanation"""
        try:
            # Load feature importance from training
            importance_path = "ml/reports/laml_feature_importance.csv"
            
            if not os.path.exists(importance_path):
                return []
            
            importance_df = pd.read_csv(importance_path)
            
            # Get top 10 most important features
            top_features = importance_df.head(10)
            
            explanation = []
            for _, row in top_features.iterrows():
                feature_name = row['feature']
                importance = row['importance']
                
                # Get feature value if it exists in current prediction
                feature_value = None
                if feature_name in features_df.columns:
                    feature_value = float(features_df[feature_name].iloc[0])
                
                explanation.append({
                    'feature': feature_name,
                    'importance': round(float(importance), 4),
                    'value': feature_value,
                    'description': self._get_feature_description(feature_name)
                })
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"❌ Error getting prediction explanation: {str(e)}")
            return []
    
    def _get_feature_description(self, feature_name: str) -> str:
        """Get human-readable description of feature"""
        descriptions = {
            'area': 'Площа квартири (м²)',
            'area_log': 'Логарифм площі',
            'rooms_filled': 'Кількість кімнат',
            'district_price_rank': 'Рейтинг району за ціною',
            'location_score': 'Оцінка локації',
            'renovation_score': 'Оцінка ремонту',
            'floor_ratio': 'Відношення поверху до загальної кількості',
            'is_owner': 'Продаж від власника',
            'district_price_usd_mean': 'Середня ціна в районі',
            'area_per_room': 'Площа на кімнату',
            'amenities_count': 'Кількість зручностей'
        }
        
        return descriptions.get(feature_name, feature_name)
    
    def _find_similar_properties(self, property_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar properties for comparison"""
        try:
            # This would typically query the database for similar properties
            # For now, return empty list as we need database integration
            
            # TODO: Implement database query for similar properties
            # Based on: same district, similar area (±20%), similar rooms
            
            return []
            
        except Exception as e:
            self.logger.error(f"❌ Error finding similar properties: {str(e)}")
            return []
    
    def batch_predict(self, properties_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch prediction for multiple properties
        
        Args:
            properties_list: List of property data dictionaries
            
        Returns:
            List[Dict[str, Any]]: List of prediction results
        """
        results = []
        
        for i, property_data in enumerate(properties_list):
            self.logger.info(f"🔮 Predicting price for property {i+1}/{len(properties_list)}")
            
            result = self.predict_price(property_data)
            result['batch_index'] = i
            results.append(result)
        
        self.logger.info(f"✅ Batch prediction completed for {len(properties_list)} properties")
        
        return results
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and information"""
        return {
            'model_loaded': self.model is not None,
            'model_path': self.model_path,
            'model_exists': os.path.exists(self.model_path),
            'model_metadata': self.model_metadata,
            'last_training': self.model_metadata.get('training_date'),
            'model_performance': {
                'mape': self.model_metadata.get('mape'),
                'r2': self.model_metadata.get('r2'),
                'target_achieved': self.model_metadata.get('target_achieved', False)
            }
        }


def predict_property_price(property_data: Dict[str, Any], 
                          model_path: str = "models/laml_price_model.pkl") -> Dict[str, Any]:
    """
    Main entry point for property price prediction
    
    Args:
        property_data: Property characteristics
        model_path: Path to trained model
        
    Returns:
        Dict[str, Any]: Prediction results
    """
    predictor = PricePredictionInference(model_path)
    return predictor.predict_price(property_data)


if __name__ == "__main__":
    # Test prediction
    test_property = {
        'area': 65,
        'rooms': 2,
        'floor': 5,
        'total_floors': 9,
        'district': 'Центр',
        'building_type': 'квартира',
        'renovation_status': 'хороший',
        'seller_type': 'owner'
    }
    
    result = predict_property_price(test_property)
    print(f"Prediction result: {result}")
