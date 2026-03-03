import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import plotly.graph_objects as go
import firebase_admin
from firebase_admin import credentials, db
import json

# ==========================================
# 1. Page Config & Professional CSS
# ==========================================
st.set_page_config(
    page_title="CRMS6 Air Quality", 
    page_icon="🍃", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make it look like a "Dashboard"
st.markdown("""
<style>
    /* Background & Fonts */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Metrics Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* Remove default padding at top */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Custom Title */
    .dashboard-title {
        font-size: 2rem; 
        font-weight: 800; 
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .dashboard-subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Setup Firebase
# ==========================================
if not firebase_admin._apps:
    try:
        key_dict = json.loads(st.secrets["firebase"]["my_secret_key"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': st.secrets["firebase"]["db_url"]
        })
    except Exception as e:
        st.error(f"⚠️ Firebase Error: {e}")

# ==========================================
# 3. Helper Functions
# ==========================================
def get_aqi_status(pm25):
    if pm25 <= 15: return "ดีมาก (Very Good)", "#3ddc84"   # Green
    elif pm25 <= 25: return "ดี (Good)", "#f5d63d"        # Yellow
    elif pm25 <= 37.5: return "ปานกลาง (Moderate)", "#ff9800" # Orange
    elif pm25 <= 75: return "เริ่มมีผลกระทบ (Unhealthy)", "#ff5722" # Red
    else: return "มีผลกระทบ (Very Unhealthy)", "#b71c1c"  # Purple/Dark Red

def get_realtime_data():
    try:
        ref = db.reference('sensor_data')
        latest_data = ref.order_by_key().limit_to_last(1).get()
        if latest_data:
            for key, val in latest_data.items():
                return val
        return None
    except:
        return None

@st.cache_data(ttl=60)
def get_history(start_dt, end_dt):
    try:
        ref = db.reference('sensor_data')
        all_data = ref.get()
        if not all_data: return pd.DataFrame()
        
        df = pd.DataFrame.from_dict(all_data, orient='index')
        if 'saved_at' not in df.columns: return pd.DataFrame()
        
        df['เวลา'] = pd.to_datetime(df['saved_at'])
        start = pd.to_datetime(start_dt)
        end = pd.to_datetime(end_dt) + timedelta(days=1)
        
        mask = (df['เวลา'] >= start) & (df['เวลา'] <= end)
        filtered = df.loc[mask].copy().sort_values(by='เวลา')
        
        # --- FIX: Rename specific sensor or clean name ---
        if 'NRCT_PM2.5_3' in filtered.columns:
            filtered.rename(columns={'NRCT_PM2.5_3': 'PM2.5'}, inplace=True)
        elif 'pm25' in filtered.columns:
            filtered.rename(columns={'pm25': 'PM2.5'}, inplace=True)
            
        # Ensure numeric
        if 'PM2.5' in filtered.columns:
            filtered['PM2.5'] = pd.to_numeric(filtered['PM2.5'], errors='coerce')
            filtered.dropna(subset=['PM2.5'], inplace=True)
            
        return filtered
    except:
        return pd.DataFrame()

# ==========================================
# 4. Sidebar Controls
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222800.png", width=50)
    st.title("Control Panel")
    
    st.markdown("### 📅 Select Date Range")
    # Default to Feb 2026 based on your Excel data
    default_start = date(2026, 2, 1)
    default_end = date(2026, 3, 1)
    
    start_date = st.date_input("Start Date", default_start)
    end_date = st.date_input("End Date", default_end)
    
    st.info("ℹ️ Data source: Smart PM2.5 Sensor (Model CRMS6)")

# ==========================================
# 5. Main Dashboard Layout
# ==========================================

# Title Section
st.markdown('<div class="dashboard-title">🍃 CRMS6 Air Quality Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Real-time monitoring system for Chiang Rai Municipality School 6</div>', unsafe_allow_html=True)

# Tabs for cleaner look
tab1, tab2 = st.tabs(["📊 Dashboard & Map", "📈 Historical Analysis"])

# --- TAB 1: Real-time Dashboard ---
with tab1:
    # 1. Get Data
    data = get_realtime_data()
    
    if data:
        # Extract values (with default 0 if missing)
        pm25 = float(data.get('pm25', 0))
        temp = float(data.get('temperature', 0))
        hum = float(data.get('humidity', 0))
        last_update = data.get('saved_at', 'Unknown')
        
        status_text, status_color = get_aqi_status(pm25)

        # 2. Top Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("PM 2.5 (µg/m³)", f"{pm25}", delta=None)
        col2.metric("Temperature", f"{temp} °C")
        col3.metric("Humidity", f"{hum} %")
        col4.metric("Last Update", str(last_update).split(" ")[1] if " " in str(last_update) else last_update)

        st.markdown("---")

        # 3. Gauge & Map Row
        c_left, c_right = st.columns([1.5, 1])
        
        with c_left:
            st.markdown("### ⏲️ Current Air Quality Index")
            # Create a professional Gauge Chart
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = pm25,
                title = {'text': f"<b>Status: {status_text}</b>", 'font': {'size': 20, 'color': status_color}},
                delta = {'reference': 37.5, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
                gauge = {
                    'axis': {'range': [0, 150], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': status_color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 25], 'color': '#dcfce7'},
                        {'range': [25, 37.5], 'color': '#fef9c3'},
                        {'range': [37.5, 75], 'color': '#fee2e2'},
                        {'range': [75, 150], 'color': '#ffcdd2'}
                    ],
                }
            ))
            fig_gauge.update_layout(height=400, margin=dict(l=20,r=20,t=50,b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with c_right:
            st.markdown("### 📍 Location")
            # Create a Map (Fixed coords for Chiang Rai School 6)
            # 19.907, 99.833 is approx Chiang Rai City
            map_data = pd.DataFrame({'lat': [19.9076], 'lon': [99.8332]}) 
            st.map(map_data, zoom=14)
            
            st.markdown(f"""
            <div style="background-color: {status_color}33; padding: 15px; border-radius: 10px; border-left: 5px solid {status_color};">
                <h4 style="color: {status_color}; margin:0;">Recommendation</h4>
                <p style="margin-top: 5px;">{ "⚠️ Wear a mask outdoors." if pm25 > 37.5 else "✅ Air is good. Enjoy outdoor activities!" }</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.warning("⏳ Waiting for data... Please ensure your MQTT script is running.")

# --- TAB 2: History ---
with tab2:
    st.markdown("### 📉 Historical Trends")
    
    df_history = get_history(start_date, end_date)
    
    if not df_history.empty and 'PM2.5' in df_history.columns:
        # Create the modern Area Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_history['เวลา'], 
            y=df_history['PM2.5'],
            mode='lines+markers',
            name='PM 2.5',
            line=dict(color='#0ea5e9', width=2),
            marker=dict(size=4, color='#0284c7'),
            fill='tozeroy',
            fillcolor='rgba(14, 165, 233, 0.1)'
        ))
        
        fig.update_layout(
            title="PM 2.5 Levels Over Time",
            xaxis_title="Date/Time",
            yaxis_title="Concentration (µg/m³)",
            template="plotly_white",
            height=450,
            hovermode="x unified",
            xaxis=dict(showgrid=False, rangeslider=dict(visible=True)),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Show Data Table below
        with st.expander("📄 View Raw Data"):
            st.dataframe(df_history[['เวลา', 'PM2.5']].sort_values(by='เวลา', ascending=False), use_container_width=True)
            
    else:
        st.info("No data found for the selected period.")
