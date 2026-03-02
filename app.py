import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly.graph_objects as go
import json

# ==========================================
# 1. ตั้งค่าหน้าเพจ & CSS
# ==========================================
st.set_page_config(
    page_title="ระบบรายงานคุณภาพอากาศ", 
    page_icon="☁️", 
    layout="wide",
    initial_sidebar_state="expanded" # เปิด Sidebar ไว้ตั้งแต่เริ่ม
)

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
# 2. เมนูด้านข้าง (Sidebar) จากเว็บเดิม
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222800.png", width=60)
    st.markdown("### ⚙️ การตั้งค่า")
    
    with st.container(border=True):
        start_date = st.date_input("📅 วันที่เริ่มต้น", date.today() - timedelta(days=7))
        end_date = st.date_input("📅 วันที่สิ้นสุด", date.today())
        
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f0f9ff, #e0f2fe); padding: 15px; border-radius: 12px; margin-top: 20px; border: 1px solid #bae6fd;'>
            <p style='color: #0369a1; font-size: 14px; margin: 0; line-height: 1.5;'>
                <b>💡 คำแนะนำ:</b><br>
                เลือกช่วงเวลาที่ต้องการ ระบบจะทำการประมวลผลและอัปเดตข้อมูลย้อนหลังให้ทันที
            </p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. ฟังก์ชันจำลองการดึงข้อมูล API และ Database
# ==========================================
def get_realtime_data_from_api():
    """ดึงข้อมูล ณ เวลาปัจจุบัน (จำลอง API แบบ JSON)"""
    mock_json_response = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "device_id": "SMART_PM25_CR_01",
        "data": {
            "pm25": np.random.randint(20, 80),
            "temperature": round(np.random.uniform(25.0, 35.0), 1),
            "humidity": round(np.random.uniform(40.0, 70.0), 1)
        }
    }
    return mock_json_response["data"]

@st.cache_data
def get_historical_data_from_db(start_dt, end_dt):
    """ดึงข้อมูลย้อนหลังจาก Database สำหรับทำกราฟ"""
    # ถ้าช่วงเวลาผิดพลาด ให้คืนค่าว่าง
    if start_dt > end_dt: return pd.DataFrame()
    
    date_range = pd.date_range(start=start_dt, end=end_dt, freq='H')
    if len(date_range) == 0:
        date_range = pd.date_range(start=start_dt, end=end_dt + timedelta(days=1), freq='H')

    np.random.seed(42)
    time_seq = np.arange(len(date_range))
    pm25 = 40 + 20 * np.sin(time_seq / 10) + np.random.normal(0, 5, len(date_range))
    
    df = pd.DataFrame({
        'เวลา': date_range,
        'PM2.5': np.maximum(5, pm25)
    })
    return df

# ==========================================
# 4. ฟังก์ชันสร้าง UI (Gauge & ข้อแนะนำ)
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
        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-top: 5px; color: #64748b;">
            <span>ดีมาก</span><span>กลาง</span><span>แย่</span>
        </div>
        <div style="margin-top: 10px; font-weight: bold; color: {color};">ระดับ: {status}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_mask_recommendation(pm25_val):
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
# 5. โครงสร้างหน้าเว็บ (Layout)
# ==========================================

# ตรวจสอบความถูกต้องของวันที่จาก Sidebar ก่อนแสดงผล
if start_date > end_date:
    st.error("⚠️ กรุณาเลือกวันที่เริ่มต้น ให้ก่อนหรือเท่ากับวันที่สิ้นสุด ในเมนูด้านซ้ายมือ")
else:
    # --- ส่วนหัว (Header) ---
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        # 🖼️ กำหนด width คงที่ที่ 100px เพื่อไม่ให้รูปใหญ่เกินไปเวลาซูม
        st.image("https://upload.wikimedia.org/wikipedia/th/b/b5/CRMS6_logo.png", width=100) 

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

    st.write("") 

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
        # 🖼️ กำหนด width คงที่ (เช่น 350px) เพื่อไม่ให้แผนที่ใหญ่ล้นจอ
        st.image("https://i.imgur.com/rr7521d.jpeg", width=350)

    st.divider()

    # --- Section 3: ข้อมูลย้อนหลัง (Database/กราฟ) ---
    st.markdown("### 📊 ข้อมูลย้อนหลัง")

    # ดึงข้อมูลตามวันที่ที่เลือกจาก Sidebar
    df_history = get_historical_data_from_db(start_date, end_date)

    if not df_history.empty:
        with st.container(border=True):
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_history['เวลา'], 
                y=df_history['PM2.5'],
                mode='lines',
                line=dict(color='#334155', width=2),
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
    else:
        st.info("ไม่มีข้อมูลในข่วงเวลาที่เลือก")
