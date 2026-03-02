import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly.graph_objects as go
import json

# ==========================================
# 1. ตั้งค่าหน้าเพจ & CSS
# ==========================================
st.set_page_config(page_title="ระบบรายงานคุณภาพอากาศ", page_icon="☁️", layout="wide")

st.markdown("""
<style>
    /* ปรับแต่ง CSS พื้นฐานให้ดู Modern ขึ้น */
    .main-title { font-weight: 700; font-size: 1.8rem; color: #1e293b; margin-bottom: 0; }
    .sub-title { color: #64748b; font-size: 1.1rem; margin-top: 5px; }
    
    /* กรอบข้อมูล (Cards) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        background-color: #ffffff;
    }
    
    /* ตัวเลข Metric */
    div[data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; color: #0f172a; }
    
    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
        .main-title { color: #f8fafc; }
        div[data-testid="stVerticalBlockBorderWrapper"] { background-color: #1e293b; border: 1px solid #334155; }
        div[data-testid="stMetricValue"] { color: #f8fafc; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ฟังก์ชันจำลองการดึงข้อมูล (เตรียมไว้สำหรับอนาคต)
# ==========================================

def get_realtime_data_from_api():
    """
    ฟังก์ชันสำหรับดึงข้อมูล ณ เวลาปัจจุบัน (จำลอง API แบบ JSON)
    ในอนาคต: ใช้ requests.get('YOUR_API_URL').json()
    """
    # โครงสร้าง JSON จำลอง
    mock_json_response = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "device_id": "SMART_PM25_CR_01",
        "data": {
            "pm25": np.random.randint(20, 80), # จำลองค่า PM 2.5 ปัจจุบัน
            "temperature": round(np.random.uniform(25.0, 35.0), 1),
            "humidity": round(np.random.uniform(40.0, 70.0), 1)
        }
    }
    # Parse JSON string/dict
    return mock_json_response["data"]

@st.cache_data
def get_historical_data_from_db(start_dt, end_dt):
    """
    ฟังก์ชันสำหรับดึงข้อมูลย้อนหลังจาก Database (จำลอง DataFrame)
    ในอนาคต: ใช้ pd.read_sql("SELECT * FROM air_quality WHERE ...", engine)
    """
    date_range = pd.date_range(start=start_dt, end=end_dt, freq='H')
    np.random.seed(42)
    time_seq = np.arange(len(date_range))
    
    # สร้างข้อมูลแบบมีแนวโน้ม
    pm25 = 40 + 20 * np.sin(time_seq / 10) + np.random.normal(0, 5, len(date_range))
    
    df = pd.DataFrame({
        'เวลา': date_range,
        'PM2.5': np.maximum(5, pm25)
    })
    return df

# ==========================================
# 3. ฟังก์ชันสร้าง UI อุปกรณ์เสริม (Gauge & ข้อแนะนำ)
# ==========================================

def render_aqi_gauge(pm25_val):
    """สร้าง Gauge คุณภาพอากาศตามภาพร่าง (ดีมาก, กลาง, แย่)"""
    if pm25_val <= 37.5:
        status, color, icon, width = "ดีมาก", "#10b981", "😊", "20%" # สีเขียว
    elif pm25_val <= 75:
        status, color, icon, width = "ปานกลาง", "#f59e0b", "😐", "50%" # สีส้ม
    else:
        status, color, icon, width = "มีผลกระทบ (แย่)", "#ef4444", "😷", "90%" # สีแดง

    html = f"""
    <div style="text-align: center; padding: 10px;">
        <div style="font-size: 2rem; margin-bottom: 5px;">{icon}</div>
        <div style="background-color: #e2e8f0; border-radius: 10px; height: 20px; width: 100%; position: relative;">
            <div style="background-color: {color}; height: 100%; width: {width}; border-radius: 10px; transition: 0.5s;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-top: 5px; color: #64748b;">
            <span>ดีมาก</span>
            <span>กลาง</span>
            <span>แย่</span>
        </div>
        <div style="margin-top: 10px; font-weight: bold; color: {color};">ระดับ: {status}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_mask_recommendation(pm25_val):
    """สร้างกล่องคำแนะนำการสวมหน้ากาก"""
    if pm25_val > 37.5:
        bg, text, msg = "#fee2e2", "#991b1b", "⚠️ <b>ควรสวมหน้ากากอนามัย</b><br>หลีกเลี่ยงกิจกรรมกลางแจ้ง"
    else:
        bg, text, msg = "#dcfce7", "#166534", "✅ <b>อากาศดี</b><br>สามารถทำกิจกรรมกลางแจ้งได้ปกติ"
        
    html = f"""
    <div style="background-color: {bg}; color: {text}; padding: 20px; border-radius: 10px; text-align: center; height: 100%; display: flex; align-items: center; justify-content: center;">
        <span style="font-size: 1.1rem;">{msg}</span>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 4. โครงสร้างหน้าเว็บ (Layout)
# ==========================================

# --- ส่วนหัว (Header) ตรงตาม Draft ---
col_logo, col_title = st.columns([1, 8])
with col_logo:
    # 🖼️ ใส่รูป Logo โรงเรียนตรงนี้ (กำหนดความกว้างตายตัวที่ 100px)
    st.image("https://upload.wikimedia.org/wikipedia/th/b/b5/CRMS6_logo.png", width=120)

with col_title:
    st.markdown("<h1 class='main-title'>รายงานค่าฝุ่น PM 2.5 และสภาพอากาศ</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>จากเครื่อง Smart PM 2.5 ณ โรงเรียนเทศบาล 6 นครเชียงราย อ.เมือง จ.เชียงราย</p>", unsafe_allow_html=True)

st.divider()

# --- ดึงข้อมูล Real-time ---
current_data = get_realtime_data_from_api()
pm25_now = current_data['pm25']

# --- Section 1: สถานการณ์ปัจจุบัน ---
st.markdown("### 📍 สถานการณ์ปัจจุบัน")
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

st.write("") # เว้นบรรทัด

# --- Section 2: ค่าอื่นๆ & แผนที่ ---
col4, col5 = st.columns([1, 1.5])

with col4:
    st.markdown("### 🌡️ ค่าอื่นๆ")
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.metric("อุณหภูมิ", f"{current_data['temperature']} °C")
        c2.metric("ความชื้น", f"{current_data['humidity']} %")

with col5:
    st.markdown("### 🗺️ แผนที่เชียงราย")
    
    # เทคนิคจัดรูปให้อยู่ตรงกลาง
    _, map_center, _ = st.columns([1, 4, 1]) 
    with map_center:
        st.image("https://i.imgur.com/rr7521d.jpeg", width=400)

st.divider()

# --- Section 3: ข้อมูลย้อนหลัง (Database/กราฟ) ---
st.markdown("### 📊 ข้อมูลย้อนหลัง")

# วันที่สำหรับดึงจาก Database
start_date = date.today() - timedelta(days=3)
end_date = date.today() + timedelta(days=1)

# ดึงข้อมูลจากฐานข้อมูลจำลอง
df_history = get_historical_data_from_db(start_date, end_date)

with st.container(border=True):
    # วาดกราฟเส้นตามภาพร่าง
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_history['เวลา'], 
        y=df_history['PM2.5'],
        mode='lines',
        line=dict(color='#334155', width=2), # สีเทาเข้มๆ ให้เหมือนลายเส้นวาด
        fill='tozeroy',
        fillcolor='rgba(226, 232, 240, 0.5)',
        name='PM2.5'
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)')
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
