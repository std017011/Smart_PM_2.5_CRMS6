import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta
import plotly.graph_objects as go # ใช้ graph_objects เพื่อปรับแต่งกราฟได้ละเอียดขึ้น

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(
    page_title="Air Quality & Weather Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 🎨 ปรับแต่ง CSS แบบ Premium Modern UI
# ==========================================
st.markdown("""
<style>
    /* ปรับระยะขอบของหน้า */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* ปรับแต่งส่วนหัวของเว็บให้ดูมีมิติ */
    .main-title {
        background: -webkit-linear-gradient(45deg, #0ea5e9, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0px;
    }
    
    /* ปรับแต่งค่าตัวเลข Metric ให้ดู Premium */
    div[data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #0f172a;
    }
    
    /* ปรับแต่ง Delta (การเพิ่ม/ลด) ให้ดูเนียนตา */
    div[data-testid="stMetricDelta"] svg {
        width: 20px;
        height: 20px;
    }

    /* ปรับแต่งกรอบ (Cards) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid rgba(148, 163, 184, 0.2);
        transition: transform 0.2s ease-in-out;
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* Dark Mode Adjustments */
    @media (prefers-color-scheme: dark) {
        div[data-testid="stMetricValue"] { color: #f8fafc; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #1e293b;
            border: 1px solid #334155;
        }
    }
</style>
""", unsafe_allow_html=True)

# 2. ส่วนหัวของเว็บไซต์
st.markdown("<h1 class='main-title'><span class='material-icons'></span> ระบบรายงานคุณภาพอากาศและสภาพอากาศ</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 1.1rem; margin-top: -5px;'>แดชบอร์ดติดตามข้อมูลแบบเรียลไทม์ พร้อมการวิเคราะห์แนวโน้มย้อนหลัง</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True) # เว้นระยะห่างเล็กน้อยแทน st.divider()

# 3. เมนูด้านข้าง
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3222/3222800.png", width=60) # เพิ่ม Icon สวยๆ
    st.markdown("### ⚙️ การตั้งค่า")
    
    with st.container(border=True):
        start_date = st.date_input("📅 วันที่เริ่มต้น", date.today() - timedelta(days=7))
        end_date = st.date_input("📅 วันที่สิ้นสุด", date.today())
        
    st.markdown("""
        <div style='background: linear-gradient(135deg, #f0f9ff, #e0f2fe); padding: 15px; border-radius: 12px; margin-top: 20px; border: 1px solid #bae6fd;'>
            <p style='color: #0369a1; font-size: 14px; margin: 0; line-height: 1.5;'>
                <b>💡 คำแนะนำ:</b><br>
                เลือกช่วงเวลาที่ต้องการ ระบบจะทำการประมวลผลและอัปเดตข้อมูลให้ทันที
            </p>
        </div>
    """, unsafe_allow_html=True)

# 4. ฟังก์ชันดึงข้อมูล (จำลอง) แบบเนียนขึ้น
@st.cache_data
def fetch_data_from_api(start, end):
    date_range = pd.date_range(start=start, end=end, freq='H')
    
    # สร้างข้อมูลแบบมีแนวโน้มให้ดูสมจริงขึ้น (Sine wave + Noise)
    np.random.seed(42)
    time_seq = np.arange(len(date_range))
    pm25 = 50 + 30 * np.sin(time_seq / 10) + np.random.normal(0, 10, len(date_range))
    temp = 28 + 5 * np.sin(time_seq / 12) + np.random.normal(0, 2, len(date_range))
    humid = 65 + 15 * np.cos(time_seq / 12) + np.random.normal(0, 5, len(date_range))
    
    data = pd.DataFrame({
        'เวลา': date_range,
        'PM2.5': np.maximum(5, pm25), # ไม่ให้ค่าติดลบ
        'อุณหภูมิ': temp,
        'ความชื้น': np.clip(humid, 20, 100) # ให้อยู่ระหว่าง 20-100%
    })
    return data

# ปรับปรุง Badge ให้ดู Modern มากขึ้น
def get_aqi_badge(pm25_val):
    if pm25_val <= 37.5:
        bg, text, icon = "#dcfce7", "#166534", "🌿 ดีมาก"
    elif pm25_val <= 75:
        bg, text, icon = "#fef08a", "#854d0e", "⚠️ ปานกลาง"
    else:
        bg, text, icon = "#fee2e2", "#991b1b", "🚨 มีผลกระทบ"
        
    return f"""
    <div style='display: flex; align-items: center; justify-content: center; height: 100%; padding-top: 10px;'>
        <div style='background-color: {bg}; color: {text}; padding: 8px 16px; border-radius: 30px; 
        font-weight: 700; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid {text}20;'>
            {icon}
        </div>
    </div>
    """

# 5. แสดงผล
if start_date > end_date:
    st.error("⚠️ กรุณาเลือกวันที่เริ่มต้น ให้ก่อนหรือเท่ากับวันที่สิ้นสุด")
else:
    df = fetch_data_from_api(start_date, end_date)
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    
    st.markdown("#### 📍 สถานการณ์ปัจจุบัน")
    
    # --- 5.1 สร้าง Cards แบบ Premium ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        with st.container(border=True):
            st.markdown("<p style='color:#64748b; font-size:14px; font-weight: 600; margin-bottom:0px;'>🌫️ ฝุ่น PM2.5</p>", unsafe_allow_html=True)
            st.metric(label="PM2.5", value=f"{latest['PM2.5']:.1f} µg/m³", delta=f"{(latest['PM2.5'] - previous['PM2.5']):.1f} (1 ชม.)", delta_color="inverse", label_visibility="collapsed")
            
    with col2:
        with st.container(border=True):
            st.markdown("<p style='color:#64748b; font-size:14px; font-weight: 600; margin-bottom:0px;'>🛡️ คุณภาพอากาศ</p>", unsafe_allow_html=True)
            st.markdown(get_aqi_badge(latest['PM2.5']), unsafe_allow_html=True)

    with col3:
        with st.container(border=True):
            st.markdown("<p style='color:#64748b; font-size:14px; font-weight: 600; margin-bottom:0px;'>🌡️ อุณหภูมิ</p>", unsafe_allow_html=True)
            st.metric(label="อุณหภูมิ", value=f"{latest['อุณหภูมิ']:.1f} °C", delta=f"{(latest['อุณหภูมิ'] - previous['อุณหภูมิ']):.1f} °C", delta_color="normal", label_visibility="collapsed")

    with col4:
        with st.container(border=True):
            st.markdown("<p style='color:#64748b; font-size:14px; font-weight: 600; margin-bottom:0px;'>💧 ความชื้น</p>", unsafe_allow_html=True)
            st.metric(label="ความชื้น", value=f"{latest['ความชื้น']:.1f} %", delta=f"{(latest['ความชื้น'] - previous['ความชื้น']):.1f} %", delta_color="off", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- 5.2 กราฟข้อมูลย้อนหลัง (เปลี่ยนมาใช้ graph_objects เพื่อความเนียน) ---
    st.markdown("#### 📊 ข้อมูลและแนวโน้มย้อนหลัง")
    
    tab1, tab2 = st.tabs(["🌫️ ข้อมูลฝุ่น PM2.5", "🌡️ ข้อมูลอุณหภูมิและความชื้น"])
    
    # การตั้งค่า Layout พื้นฐานของกราฟ
    chart_layout = dict(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
        height=380,
        hovermode="x unified",
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='rgba(128, 128, 128, 0.1)'), # สีเส้นตารางจางๆ รองรับทั้ง Dark/Light mode
        font=dict(family="sans-serif")
    )
    
    with tab1:
        with st.container(border=True):
            fig_pm = go.Figure()
            # ใช้ Spline เพื่อให้เส้นโค้งมน และเพิ่ม Gradient fill ด้านล่าง
            fig_pm.add_trace(go.Scatter(
                x=df['เวลา'], y=df['PM2.5'],
                fill='tozeroy',
                mode='lines',
                line=dict(color='#0ea5e9', width=3, shape='spline'),
                fillcolor='rgba(14, 165, 233, 0.15)',
                name='PM2.5',
                hovertemplate='%{y:.1f} µg/m³<extra></extra>'
            ))
            fig_pm.update_layout(**chart_layout)
            st.plotly_chart(fig_pm, use_container_width=True, config={'displayModeBar': False})
        
    with tab2:
        with st.container(border=True):
            fig_weather = go.Figure()
            # เส้นอุณหภูมิ
            fig_weather.add_trace(go.Scatter(
                x=df['เวลา'], y=df['อุณหภูมิ'],
                mode='lines',
                line=dict(color='#f97316', width=3, shape='spline'),
                name='อุณหภูมิ (°C)'
            ))
            # เส้นความชื้น (แยกแกน Y ถ้าต้องการ แต่ในที่นี้วาดรวมกันเพื่อให้สอดคล้องกับโค้ดเดิม)
            fig_weather.add_trace(go.Scatter(
                x=df['เวลา'], y=df['ความชื้น'],
                mode='lines',
                line=dict(color='#3b82f6', width=3, shape='spline', dash='dot'),
                name='ความชื้น (%)'
            ))
            
            # ปรับแต่ง Layout เพิ่มเติมสำหรับ Tab 2
            layout_weather = chart_layout.copy()
            layout_weather['legend'] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            fig_weather.update_layout(**layout_weather)
            
            st.plotly_chart(fig_weather, use_container_width=True, config={'displayModeBar': False})
