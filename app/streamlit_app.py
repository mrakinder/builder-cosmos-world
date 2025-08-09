"""
Streamlit Public Interface for Property Price Estimation
========================================================

Web application for users to estimate real estate prices in Ivano-Frankivsk.
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ml.laml.infer import PricePredictorLAML
    from ml.laml.utils import validate_input_data
except ImportError:
    st.error("ML modules not found. Please ensure the project is properly set up.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Glow Nest XGB - Оцінка нерухомості",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile responsiveness
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        border: none;
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e5e7eb;
        margin: 0.5rem 0;
    }
    
    .price-result {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .feature-importance {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4f46e5;
        margin: 0.5rem 0;
    }
    
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_districts_and_streets():
    """Load available districts and streets from database"""
    try:
        db_path = Path("data/olx_offers.sqlite")
        if not db_path.exists():
            return [], {}
        
        with sqlite3.connect(db_path) as conn:
            # Get districts
            districts_query = """
            SELECT DISTINCT district 
            FROM offers 
            WHERE district IS NOT NULL AND is_active = 1
            ORDER BY district
            """
            districts_df = pd.read_sql_query(districts_query, conn)
            districts = districts_df['district'].tolist()
            
            # Get streets by district
            streets_query = """
            SELECT DISTINCT district, street 
            FROM offers 
            WHERE district IS NOT NULL AND street IS NOT NULL AND is_active = 1
            ORDER BY district, street
            """
            streets_df = pd.read_sql_query(streets_query, conn)
            streets_by_district = {}
            for district in districts:
                district_streets = streets_df[streets_df['district'] == district]['street'].tolist()
                streets_by_district[district] = district_streets
            
            return districts, streets_by_district
            
    except Exception as e:
        st.error(f"Помилка завантаження даних: {str(e)}")
        return [], {}

@st.cache_data(ttl=300)
def load_feature_importance():
    """Load feature importance from model training"""
    try:
        importance_path = Path("reports/laml_feature_importance.csv")
        if importance_path.exists():
            df = pd.read_csv(importance_path)
            return df.head(10)  # Top 10 features
    except:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_similar_properties(district, area_range=(50, 80), rooms=2):
    """Load similar properties from database"""
    try:
        db_path = Path("data/olx_offers.sqlite")
        if not db_path.exists():
            return pd.DataFrame()
        
        with sqlite3.connect(db_path) as conn:
            query = """
            SELECT title, price_value, area_total, rooms, floor, street, 
                   building_type, renovation, seller_type, scraped_at, url
            FROM offers 
            WHERE district = ? 
              AND is_active = 1 
              AND price_value IS NOT NULL
              AND area_total BETWEEN ? AND ?
              AND rooms = ?
              AND price_currency = 'USD'
            ORDER BY scraped_at DESC 
            LIMIT 10
            """
            
            area_min, area_max = area_range
            similar_df = pd.read_sql_query(query, conn, params=[district, area_min, area_max, rooms])
            return similar_df
            
    except Exception:
        return pd.DataFrame()

def predict_price(property_data):
    """Make price prediction using trained model"""
    try:
        model_path = Path("models/laml_price.bin")
        if not model_path.exists():
            st.error("Модель не знайдена. Будь ласка, спочатку навчіть модель.")
            return None
        
        predictor = PricePredictorLAML(str(model_path))
        result = predictor.predict_single(property_data)
        return result
        
    except Exception as e:
        st.error(f"Помилка прогнозування: {str(e)}")
        return None

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="color: #1f2937; margin-bottom: 0.5rem;">🏠 Glow Nest XGB</h1>
        <p style="color: #6b7280; font-size: 1.2rem;">Оцінка нерухомості в Івано-Франківську</p>
        <p style="color: #9ca3af;">Автоматичний прогноз цін за допомогою машинного навчання</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    districts, streets_by_district = load_districts_and_streets()
    
    if not districts:
        st.warning("⚠️ Дані не знайдені. Будь ласка, спочатку запустіть парсинг OLX.")
        st.markdown("""
        ### Як розпочати:
        1. Запустіть парсинг: `python cli.py scrape --mode sale --pages 5`
        2. Навчіть модель: `python -m ml.laml.train --src sqlite --path data/olx_offers.sqlite`
        3. Оновіть цю сторінку
        """)
        return
    
    # Main content in columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📊 Введіть дані про квартиру")
        
        # Form for property data
        with st.form("property_form"):
            # District selection
            selected_district = st.selectbox(
                "🏘️ Район",
                options=districts,
                index=0 if districts else None,
                help="Оберіть район Івано-Франківська"
            )
            
            # Street selection
            available_streets = streets_by_district.get(selected_district, [])
            selected_street = st.selectbox(
                "🛣️ Вулиця (опціонально)",
                options=[""] + available_streets,
                help="Оберіть вулицю або залиште порожнім"
            )
            
            # Property characteristics
            col_a, col_b = st.columns(2)
            
            with col_a:
                rooms = st.selectbox(
                    "🚪 Кількість кімнат",
                    options=[1, 2, 3, 4, 5],
                    index=1,  # Default: 2 rooms
                    help="Кількість кімнат у квартирі"
                )
                
                area_total = st.number_input(
                    "📐 Загальна площа (м²)",
                    min_value=15.0,
                    max_value=300.0,
                    value=65.0,
                    step=1.0,
                    help="Загальна площа квартири"
                )
                
                floor = st.number_input(
                    "🏢 Поверх",
                    min_value=1,
                    max_value=50,
                    value=5,
                    step=1,
                    help="На якому поверсі знаходиться квартира"
                )
            
            with col_b:
                floors_total = st.number_input(
                    "🏗️ Поверховість будинку",
                    min_value=1,
                    max_value=50,
                    value=9,
                    step=1,
                    help="Загальна кількість поверхів у будинку"
                )
                
                building_type = st.selectbox(
                    "🧱 Тип будинку",
                    options=["панель", "цегла", "монолітно-цегляний", "новобудова", "блок"],
                    index=0,
                    help="Тип будівлі"
                )
                
                renovation = st.selectbox(
                    "🎨 Ремонт",
                    options=["косметичний", "євроремонт", "під ремонт", "дизай��ерський", "без ремонту"],
                    index=0,
                    help="Стан ремонту квартири"
                )
            
            # Submit button
            submitted = st.form_submit_button(
                "💰 Оцінити вартість",
                use_container_width=True
            )
    
    with col2:
        st.markdown("### 🎯 Результат оцінки")
        
        if submitted:
            # Prepare data for prediction
            property_data = {
                "district": selected_district,
                "street": selected_street if selected_street else "",
                "rooms": rooms,
                "area_total": float(area_total),
                "floor": floor,
                "floors_total": floors_total,
                "building_type": building_type,
                "renovation": renovation,
                "seller_type": "owner"
            }
            
            # Make prediction
            with st.spinner("⏳ Обробляємо дані..."):
                result = predict_price(property_data)
            
            if result and 'prediction' in result:
                prediction = result['prediction']
                price = prediction['price_usd']
                confidence = prediction['confidence_interval']
                
                # Display result
                st.markdown(f"""
                <div class="price-result">
                    <h2 style="margin: 0; font-size: 2.5rem;">${price:,.0f}</h2>
                    <p style="margin: 0.5rem 0; opacity: 0.9; font-size: 1.1rem;">
                        Прогнозована вартість
                    </p>
                    <p style="margin: 0; opacity: 0.8;">
                        Довірчий інтервал: ${confidence['lower']:,.0f} - ${confidence['upper']:,.0f}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Price per square meter
                price_per_sqm = price / area_total
                st.metric(
                    "📏 Ціна за м²",
                    f"${price_per_sqm:,.0f}",
                    help="Вартість одного квадратного метра"
                )
                
                # Model info
                model_info = result.get('model_info', {})
                if model_info.get('validation_mape'):
                    st.info(f"📊 Точність моделі: {model_info['validation_mape']:.1f}% MAPE")
            
            else:
                st.error("❌ Не вдалося зробити прогноз. Перевірте дані або навчіть модель.")
    
    # Additional information section
    st.markdown("---")
    
    # Feature importance
    feature_importance_df = load_feature_importance()
    if not feature_importance_df.empty:
        st.markdown("### 📈 Найважливіші фактори ціни")
        
        fig = px.bar(
            feature_importance_df.head(5),
            x='importance',
            y='feature',
            orientation='h',
            title="Топ-5 факторів, що впливають на ціну",
            color='importance',
            color_continuous_scale='viridis'
        )
        fig.update_layout(
            height=300,
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Similar properties
    if submitted and selected_district:
        similar_properties = load_similar_properties(
            selected_district, 
            (area_total - 10, area_total + 10), 
            rooms
        )
        
        if not similar_properties.empty:
            st.markdown("### 🏘️ Схожі оголошення")
            
            for _, prop in similar_properties.head(5).iterrows():
                with st.expander(f"{prop['title'][:50]}... - ${prop['price_value']:,.0f}"):
                    col_a, col_b = st.columns([2, 1])
                    
                    with col_a:
                        st.write(f"**Площа:** {prop['area_total']} м²")
                        st.write(f"**Кімнат:** {prop['rooms']}")
                        st.write(f"**Поверх:** {prop['floor']}")
                        if prop['street']:
                            st.write(f"**Вулиця:** {prop['street']}")
                        if prop['building_type']:
                            st.write(f"**Тип:** {prop['building_type']}")
                    
                    with col_b:
                        price_per_sqm_prop = prop['price_value'] / prop['area_total']
                        st.metric("Ціна за м²", f"${price_per_sqm_prop:,.0f}")
                        
                        if prop['url'] and prop['url'] != 'manual_entry':
                            st.markdown(f"[🔗 Переглянути на OLX]({prop['url']})")
    
    # Footer
    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    
    with col_f1:
        if st.button("🔧 Адмін панель", use_container_width=True):
            st.markdown("""
            <script>
                window.open('/admin', '_blank');
            </script>
            """, unsafe_allow_html=True)
    
    with col_f2:
        if st.button("📊 Статистика", use_container_width=True):
            st.markdown("""
            <script>
                window.open('/statistics', '_blank');
            </script>
            """, unsafe_allow_html=True)
    
    with col_f3:
        st.markdown(f"*Оновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}*")

if __name__ == "__main__":
    main()
