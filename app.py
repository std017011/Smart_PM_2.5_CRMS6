import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
import plotly.graph_objects as go
import firebase_admin
from firebase_admin import credentials, db
import json

# ==========================================
# 0. Setup Firebase for Streamlit Cloud
# ==========================================
if not firebase_admin._apps:
    key_dict = json.loads(st.secrets["firebase"]["my_secret_key"])
    cred = credentials.Certificate(key_dict)
    firebase_admin.initialize_app(cred, {
        'databaseURL': st.secrets["firebase"]["db_url"]
    })

# ==========================================
# 1. Page Config
# ==========================================
st.set_page_config(page_title="ระบบรายงานคุณภาพอากาศ", page_icon="☁️", layout="wide")

st.markdown("""
<style>
    .main-title { font-weight: 700; font-size: 1.8rem; margin-bottom: 0; }
    .sub-title { color: #64748b; font-size: 1.1rem; margin-top: 5px; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    div[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Sidebar
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222800.png", width=60)
    st.markdown("### ⚙️ การตั้งค่า")
    
    st.info("💡 เลือกช่วงเวลาที่มีข้อมูล (เช่น ปี 2026)")
    with st.container(border=True):
        # I changed the default date to start near your Excel data just in case
        start_date = st.date_input("📅 วันที่เริ่มต้น", date(2026, 2, 1))
        end_date = st.date_input("📅 วันที่สิ้นสุด", date(2026, 3, 1))

# ==========================================
# 3. Data Functions
# ==========================================
def get_realtime_data_from_api():
    try:
        ref = db.reference('sensor_data')
        latest_data = ref.order_by_key().limit_to_last(1).get()
        if latest_data:
            for key, val in latest_data.items():
                return val
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def get_historical_data_from_db(start_dt, end_dt):
    if start_dt > end_dt: return pd.DataFrame()
        
    ref = db.reference('sensor_data')
    all_data = ref.get()
    if not all_data: return pd.DataFrame()
        
    df = pd.DataFrame.from_dict(all_data, orient='index')
    if 'saved_at' not in df.columns: return pd.DataFrame()
        
    df['เวลา'] = pd.to_datetime(df['saved_at'])
    
    start_datetime = pd.to_datetime(start_dt)
    end_datetime = pd.to_datetime(end_dt) + timedelta(days=1)
    
    mask = (df['เวลา'] >= start_datetime) & (df['เวลา'] <= end_datetime)
    filtered_df = df.loc[mask].copy().sort_values(by='เวลา')
    
    if 'pm25' in filtered_df.columns:
        filtered_df.rename(columns={'pm25': 'PM2.5'}, inplace=True)
    
    # --- FIX 1: Ensure PM2.5 is a Number and drop empty rows ---
    if 'PM2.5' in filtered_df.columns:
        filtered_df['PM2.5'] = pd.to_numeric(filtered_df['PM2.5'], errors='coerce')
        filtered_df.dropna(subset=['PM2.5'], inplace=True)
        
    return filtered_df

# ==========================================
# 4. UI Functions
# ==========================================
def render_aqi_gauge(pm25_val):
    if pm25_val <= 37.5:
        status, color, icon, width = "ดีมาก", "#10b981", "😊", "20%"
    elif pm25_val <= 75:
        status, color, icon, width = "ปานกลาง", "#f59e0b", "😐", "50%"
    else:
        status, color, icon, width = "มีผลกระทบ (แย่)", "#ef4444", "😷", "90%"

    html = f"""
    <div style="text-align: center; padding: 10px;">
        <div style="font-size: 2rem; margin-bottom: 5px;">{icon}</div>
        <div style="background-color: #e2e8f0; border-radius: 10px; height: 20px; width: 100%; position: relative;">
            <div style="background-color: {color}; height: 100%; width: {width}; border-radius: 10px; transition: 0.5s;"></div>
        </div>
        <div style="margin-top: 10px; font-weight: bold; color: {color};">ระดับ: {status}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_mask_recommendation(pm25_val):
    if pm25_val > 37.5:
        bg, text, msg = "#fee2e2", "#991b1b", "⚠️ <b>ควรสวมหน้ากากอนามัย</b>"
    else:
        bg, text, msg = "#dcfce7", "#166534", "✅ <b>อากาศดี</b>"
    html = f'<div style="background-color: {bg}; color: {text}; padding: 20px; border-radius: 10px; text-align: center; height: 100%; display: flex; align-items: center; justify-content: center;"><span style="font-size: 1.1rem;">{msg}</span></div>'
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 5. Main Layout
# ==========================================
if start_date > end_date:
    st.error("⚠️ Error: Start date must be before end date.")
else:
    st.markdown("<h1 class='main-title'>รายงานค่าฝุ่น PM 2.5 และสภาพอากาศ</h1>", unsafe_allow_html=True)
    st.divider()

    current_data = get_realtime_data_from_api()
    
    if current_data:
        pm25_now = current_data.get('pm25', 0) 
        temp_now = current_data.get('temperature', 0)
        hum_now = current_data.get('humidity', 0)

        col1, col2, col3 = st.columns([1.2, 1.5, 1.2])
        with col1:
            with st.container(border=True):
                st.markdown("**ค่าฝุ่น PM 2.5**")
                st.metric(label="", value=f"{pm25_now} µg/m³", label_visibility="collapsed")
        with col2:
            with st.container(border=True):
                st.markdown("**คุณภาพอากาศ**")
                render_aqi_gauge(pm25_now)
        with col3:
            with st.container(border=True):
                st.markdown("**ข้อแนะนำ**")
                render_mask_recommendation(pm25_now)

        col4, col5 = st.columns([1, 1.5])
        with col4:
            st.markdown("### 🌡️ ค่าอื่นๆ")
            with st.container(border=True):
                c1, c2 = st.columns(2)
                c1.metric("อุณหภูมิ", f"{temp_now} °C")
                c2.metric("ความชื้น", f"{hum_now} %")
        with col5:
             st.markdown("### 🗺️ แผนที่เชียงราย")
             st.image("https://i.imgur.com/rr7521d.jpeg", width=350)
    else:
        st.warning("กำลังรอข้อมูลจากเซ็นเซอร์ (Waiting for sensor data...)")

    st.divider()

    st.markdown("### 📊 ข้อมูลย้อนหลัง")
    df_history = get_historical_data_from_db(start_date, end_date)

    if not df_history.empty and 'PM2.5' in df_history.columns:
with st.container(border=True):
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_history['เวลา'], 
                y=df_history['PM2.5'],
                mode='lines+markers',      # <--- Added +markers (dots)
                marker=dict(size=4),       # <--- Set dot size
                fill='tozeroy',
                fillcolor='rgba(59, 130, 246, 0.2)', # Transparent blue fill
                name='PM2.5'
            ))
            
            # --- FIX 3: Add a zoom-in slider at the bottom! ---
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                margin=dict(l=20, r=20, t=20, b=20), 
                height=400,
                xaxis=dict(rangeslider=dict(visible=True)) # Zoom slider turned ON
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("ไม่มีข้อมูลในฐานข้อมูล (No data available in Database yet)")
