"""
Streamlit Public Interface - Module 4
Mobile-responsive web interface for property price evaluation
Target: Response time ≤ 1.5 seconds
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
import sqlite3
import os
from typing import Dict, List, Optional, Any

# Configure page
st.set_page_config(
    page_title="Glow Nest - Оцінка нерухомості Івано-Франківськ",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile responsiveness
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main > div {
        padding-top: 1rem;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* Cards styling */
    .prediction-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .stSelectbox > div > div {
            font-size: 14px;
        }
        
        .stNumberInput > div > div > input {
            font-size: 16px; /* Prevent zoom on iOS */
        }
    }
    
    /* Custom button styling */
    .predict-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin: 1rem 0;
    }
    
    .admin-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(0,0,0,0.7);
        color: white;
        border: none;
        padding: 10px;
        border-radius: 50%;
        cursor: pointer;
        z-index: 1000;
    }
    
    /* Loading animation */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)


class PropertyEvaluator:
    """Property price evaluation engine"""
    
    def __init__(self):
        from cli.db_config import get_db_path
        self.db_path = get_db_path()
        
    def predict_price(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict property price using ML model
        
        Args:
            property_data: Property characteristics
            
        Returns:
            Dict[str, Any]: Prediction results
        """
        try:
            # Start timing
            start_time = time.time()
            
            # Import ML modules
            from ml.laml.infer import predict_property_price
            
            # Make prediction
            prediction_result = predict_property_price(property_data)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            if prediction_result.get('success'):
                prediction_result['response_time'] = round(response_time, 2)
                prediction_result['performance_target_met'] = response_time <= 1.5
            
            return prediction_result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Помилка ��рогнозування: {str(e)}",
                'predicted_price': None
            }
    
    def get_similar_properties(self, property_data: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar properties from database"""
        try:
            if not os.path.exists(self.db_path):
                return []
            
            conn = sqlite3.connect(self.db_path)
            
            # Build query for similar properties
            district = property_data.get('district', 'Центр')
            area = property_data.get('area', 50)
            rooms = property_data.get('rooms', 2)
            
            # Area range: ±20%
            area_min = area * 0.8
            area_max = area * 1.2
            
            query = """
            SELECT title, price_usd, area, rooms, floor, district, 
                   listing_url, scraped_at, seller_type
            FROM properties 
            WHERE is_active = 1 
            AND district = ?
            AND area BETWEEN ? AND ?
            AND (rooms = ? OR rooms IS NULL)
            AND price_usd IS NOT NULL
            ORDER BY ABS(area - ?) ASC
            LIMIT ?
            """
            
            df = pd.read_sql_query(
                query, 
                conn, 
                params=[district, area_min, area_max, rooms, area, limit]
            )
            conn.close()
            
            if len(df) == 0:
                return []
            
            # Convert to list of dictionaries
            similar_properties = []
            for _, row in df.iterrows():
                similar_properties.append({
                    'title': row['title'],
                    'price_usd': row['price_usd'],
                    'area': row['area'],
                    'rooms': row['rooms'],
                    'floor': row['floor'],
                    'district': row['district'],
                    'price_per_sqm': round(row['price_usd'] / row['area'], 2) if row['area'] > 0 else None,
                    'seller_type': '👤 Власник' if row['seller_type'] == 'owner' else '🏢 Агентство',
                    'date': row['scraped_at']
                })
            
            return similar_properties
            
        except Exception as e:
            st.error(f"Помилка пошуку схожих об'єктів: {str(e)}")
            return []
    
    def get_district_stats(self, district: str) -> Dict[str, Any]:
        """Get district statistics"""
        try:
            if not os.path.exists(self.db_path):
                return {}
            
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                COUNT(*) as total_properties,
                AVG(price_usd) as avg_price,
                MIN(price_usd) as min_price,
                MAX(price_usd) as max_price,
                AVG(area) as avg_area,
                AVG(price_usd / area) as avg_price_per_sqm
            FROM properties 
            WHERE is_active = 1 
            AND district = ?
            AND price_usd IS NOT NULL
            AND area IS NOT NULL
            """
            
            result = pd.read_sql_query(query, conn, params=[district])
            conn.close()
            
            if len(result) == 0:
                return {}
            
            stats = result.iloc[0].to_dict()
            
            # Round values
            for key, value in stats.items():
                if pd.notna(value) and key != 'total_properties':
                    stats[key] = round(float(value), 2)
                elif key == 'total_properties':
                    stats[key] = int(value)
            
            return stats
            
        except Exception as e:
            return {}


# Initialize evaluator
@st.cache_resource
def get_evaluator():
    return PropertyEvaluator()


def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: white; font-size: 2.5rem; margin-bottom: 0.5rem;">
                🏠 Glow Nest XGB
            </h1>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.2rem; margin-bottom: 0;">
                Оцінка нерухомості в Івано-Франківську
            </p>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.9rem;">
                Швидка та точна оцінка з використанням машинного навчання
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize evaluator
    evaluator = get_evaluator()
    
    # Main content in container
    with st.container():
        
        # Property evaluation form
        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
        
        st.markdown("### 📝 Введіть характеристики нерухомості")
        
        # Create form columns for mobile responsiveness
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # District selection
            districts = [
                "Центр", "Пасічна", "БАМ", "Каскад", 
                "Залізничний (Вокзал)", "Брати", "Софіївка", 
                "Будівельників", "Набере��на", "Опришівці"
            ]
            
            district = st.selectbox(
                "🏘️ Район",
                districts,
                index=0,
                help="Оберіть район розташування нерухомості"
            )
            
            # Area input
            area = st.number_input(
                "📐 Площа (м²)",
                min_value=10.0,
                max_value=300.0,
                value=60.0,
                step=5.0,
                help="Загальна площа квартири в квадратних метрах"
            )
            
            # Rooms input
            rooms = st.selectbox(
                "🚪 Кількість кімнат",
                [1, 2, 3, 4, 5],
                index=1,
                help="Кількість житлових кімнат (без кухні та ванної)"
            )
        
        with col2:
            # Floor input
            floor = st.number_input(
                "🏢 Пов��рх",
                min_value=1,
                max_value=30,
                value=5,
                step=1,
                help="На якому поверсі розташована квартира"
            )
            
            # Total floors
            total_floors = st.number_input(
                "🏗️ Всього поверхів",
                min_value=1,
                max_value=30,
                value=9,
                step=1,
                help="Загальна кількість поверхів в будинку"
            )
            
            # Building type
            building_type = st.selectbox(
                "🏠 Тип будівлі",
                ["квартира", "новобудова", "вторинка", "котедж"],
                index=0,
                help="Тип нерухомості"
            )
        
        # Additional parameters
        col3, col4 = st.columns([1, 1])
        
        with col3:
            renovation_status = st.selectbox(
                "🔨 Стан ремонту",
                ["євроремонт", "відмінний", "хороший", "косметичний", "потребує ремонту"],
                index=2,
                help="Оцінка стану ремонту"
            )
        
        with col4:
            seller_type = st.selectbox(
                "👤 Тип продавця",
                ["owner", "agency"],
                format_func=lambda x: "👤 Власник" if x == "owner" else "🏢 Агентство",
                index=0,
                help="��то продає нерухомість"
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Predict button
        if st.button("🔮 Оцінити вартість", key="predict_btn", help="Натисніть для отримання оцінки вартості", type="primary"):
            
            # Prepare property data
            property_data = {
                'area': area,
                'rooms': rooms,
                'floor': floor,
                'total_floors': total_floors,
                'district': district,
                'building_type': building_type,
                'renovation_status': renovation_status,
                'seller_type': seller_type,
                'listing_type': 'sale'
            }
            
            # Show loading
            with st.spinner('🔄 Аналізуємо ринок та прогнозуємо ціну...'):
                
                # Make prediction
                prediction_result = evaluator.predict_price(property_data)
                
                if prediction_result.get('success'):
                    
                    # Main prediction result
                    st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                    
                    predicted_price = prediction_result['predicted_price']
                    confidence = prediction_result.get('confidence_intervals', {})
                    
                    # Price display
                    col_price1, col_price2, col_price3 = st.columns([1, 2, 1])
                    
                    with col_price2:
                        st.markdown(f"""
                            <div style="text-align: center; padding: 2rem;">
                                <h2 style="color: #667eea; margin-bottom: 0.5rem;">Оціночна вартість</h2>
                                <h1 style="color: #2d3748; font-size: 3rem; margin: 0;">
                                    ${predicted_price:,.0f}
                                </h1>
                                <p style="color: #666; margin-top: 0.5rem;">
                                    {predicted_price * 28:,.0f} ₴ (за курсом НБУ)
                                </p>
                                <p style="color: #888; font-size: 0.9rem;">
                                    ${predicted_price/area:.0f}/м² • {prediction_result.get('response_time', 0)} с��к
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Confidence intervals
                    if confidence:
                        st.markdown("#### 📊 Діапазон цін")
                        conf_col1, conf_col2, conf_col3 = st.columns([1, 1, 1])
                        
                        with conf_col1:
                            st.metric(
                                "Мінімум (80%)",
                                f"${confidence.get('lower_80', 0):,.0f}",
                                delta=f"{((confidence.get('lower_80', 0) - predicted_price) / predicted_price * 100):+.1f}%"
                            )
                        
                        with conf_col2:
                            st.metric(
                                "Прогноз",
                                f"${predicted_price:,.0f}",
                                delta=None
                            )
                        
                        with conf_col3:
                            st.metric(
                                "Максимум (80%)",
                                f"${confidence.get('upper_80', 0):,.0f}",
                                delta=f"{((confidence.get('upper_80', 0) - predicted_price) / predicted_price * 100):+.1f}%"
                            )
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Feature importance
                    feature_importance = prediction_result.get('feature_importance', [])
                    if feature_importance:
                        st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                        st.markdown("#### 🎯 Що впливає на ціну")
                        
                        # Create importance chart
                        if len(feature_importance) > 0:
                            features_df = pd.DataFrame(feature_importance[:5])  # Top 5
                            
                            fig = px.bar(
                                features_df,
                                x='importance',
                                y='description',
                                orientation='h',
                                title="Топ-5 факторів ціноутворення",
                                color='importance',
                                color_continuous_scale='viridis'
                            )
                            fig.update_layout(
                                height=300,
                                showlegend=False,
                                yaxis_title="",
                                xaxis_title="Вплив на ціну"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                else:
                    st.error(f"❌ {prediction_result.get('error', 'Помилка прогнозування')}")
        
        # District statistics
        if st.checkbox("📈 Показати статистику району", value=False):
            district_stats = evaluator.get_district_stats(district)
            
            if district_stats:
                st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                st.markdown(f"#### 📊 Статистика району {district}")
                
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns([1, 1, 1, 1])
                
                with stat_col1:
                    st.metric(
                        "Всього об'єктів",
                        district_stats.get('total_properties', 0)
                    )
                
                with stat_col2:
                    st.metric(
                        "Середня ціна",
                        f"${district_stats.get('avg_price', 0):,.0f}"
                    )
                
                with stat_col3:
                    st.metric(
                        "Ціна за м²",
                        f"${district_stats.get('avg_price_per_sqm', 0):,.0f}"
                    )
                
                with stat_col4:
                    st.metric(
                        "Середня площа",
                        f"{district_stats.get('avg_area', 0):.0f} м²"
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Similar properties
        if st.checkbox("🔍 Показати схожі об'єкти", value=False):
            property_data = {
                'district': district,
                'area': area,
                'rooms': rooms
            }
            
            similar_properties = evaluator.get_similar_properties(property_data)
            
            if similar_properties:
                st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                st.markdown("#### 🏠 Схожі об'єкти на ринку")
                
                for i, prop in enumerate(similar_properties[:3], 1):
                    with st.expander(f"{i}. {prop['title'][:50]}..."):
                        prop_col1, prop_col2 = st.columns([2, 1])
                        
                        with prop_col1:
                            st.write(f"**Ціна:** ${prop['price_usd']:,.0f}")
                            st.write(f"**Площа:** {prop['area']} м²")
                            st.write(f"**Кімнат:** {prop['rooms'] or 'не вказано'}")
                            st.write(f"**Поверх:** {prop['floor'] or 'не вказано'}")
                        
                        with prop_col2:
                            st.write(f"**За м²:** ${prop['price_per_sqm'] or 0:.0f}")
                            st.write(f"**Продавець:** {prop['seller_type']}")
                            st.write(f"**Район:** {prop['district']}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("🔍 Схожі об'єкти не знайден�� в поточній базі даних")
    
    # Footer
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0; color: rgba(255,255,255,0.6);">
            <hr style="border-color: rgba(255,255,255,0.3);">
            <p>🏠 Glow Nest XGB - Аналіз нерухомості Івано-Франківськ</p>
            <p style="font-size: 0.8rem;">
                Працює на LightAutoML • Prophet • Botasaurus<br>
                Оновлено: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Admin button (mobile-friendly)
    st.markdown("""
        <a href="/admin" target="_blank" class="admin-button" title="Адмін панель">
            ⚙️
        </a>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
