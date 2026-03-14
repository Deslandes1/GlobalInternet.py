"""
GLOBALINTERNET.PY - Advanced Satellite Communication Platform
Author: Gesner Deslandes
Version: 2.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import socket
import hashlib
from datetime import datetime
from typing import Dict, Tuple
from streamlit_option_menu import option_menu

# --- 1. OPTIONAL MODULE IMPORTS WITH FALLBACKS ---
# Plotly for charts
try:
    import plotly.express as px
    PLOTLY_READY = True
except ImportError:
    PLOTLY_READY = False

# Mapping Modules
try:
    import folium
    from streamlit_folium import folium_static
    import geocoder
    MAP_READY = True
except ImportError:
    MAP_READY = False

# --- 2. CONFIGURATION & CONSTANTS ---
st.set_page_config(
    page_title="GLOBALINTERNET.PY",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Security Constants
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"

# Satellite Constants
SATELLITE_POSITIONS = {
    "Starlink-3070": {"lat": 32.7767, "lon": -96.7970, "alt": 550, "status": "active"},
    "Starlink-4182": {"lat": 35.6895, "lon": 139.6917, "alt": 550, "status": "active"},
    "Starlink-5123": {"lat": -33.8688, "lon": 151.2093, "alt": 550, "status": "active"},
    "Starlink-6231": {"lat": 51.5074, "lon": -0.1278, "alt": 550, "status": "active"},
    "Starlink-7342": {"lat": 18.5392, "lon": -72.3350, "alt": 550, "status": "priority"}
}

# --- 3. SESSION STATE INITIALIZATION ---
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_time" not in st.session_state:
        st.session_state.login_time = None
    if "data_comp" not in st.session_state:
        st.session_state.data_comp = 0.0
    if "connection_time" not in st.session_state:
        st.session_state.connection_time = time.time()
    if "posts" not in st.session_state:
        st.session_state.posts = []
    if "profile" not in st.session_state:
        st.session_state.profile = {
            "name": "Gesner Deslandes",
            "bio": "Python Expert | Satellite Communications Specialist",
            "location": "Port-au-Prince, Haiti",
            "join_date": datetime.now().strftime("%Y-%m-%d"),
            "verified": True,
            "connections": 0
        }
init_session_state()

# --- 4. UI STYLING ---
def apply_ui():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(-45deg, #0a0f1e, #1a1f2e, #0b1a2e, #0a1929);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .stMetric {
            background: rgba(10, 25, 47, 0.8);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #00ff88;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
            backdrop-filter: blur(10px);
        }
        .post-card {
            background: rgba(17, 34, 64, 0.9);
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #00a8ff;
            margin-bottom: 20px;
            color: #e0e0e0;
        }
        .health-text {
            font-family: 'Courier New', monospace;
            color: #00ff88;
            font-size: 14px;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid #00ff88;
        }
        .glow-text {
            color: #fff;
            text-shadow: 0 0 10px #00ff88, 0 0 20px #00ff88;
        }
        .stButton > button {
            background: linear-gradient(45deg, #00ff88, #00a8ff);
            color: #0a1929;
            border: none;
            padding: 10px 25px;
            border-radius: 25px;
            font-weight: bold;
        }
        [data-testid="stSidebar"] {
            background: rgba(10, 25, 47, 0.95);
            border-right: 1px solid #00ff88;
        }
        </style>
    """, unsafe_allow_html=True)
apply_ui()

# --- 5. HEALTH MONITORING ---
class SystemHealthMonitor:
    @staticmethod
    def get_network_metrics() -> Tuple[float, str, Dict]:
        start_time = time.time()
        metrics = {"signal_quality": 0, "bandwidth": 0}
        try:
            socket.gethostbyname("google.com")
            latency = round((time.time() - start_time) * 1000, 2)
            if latency < 150:
                signal = "SATELLITE (STARLINK/HIGH-SPEED)"
                metrics["signal_quality"] = 100
                metrics["bandwidth"] = 250
            elif latency < 400:
                signal = "LOCAL DATA (NATCOM/DIGICEL)"
                metrics["signal_quality"] = 70
                metrics["bandwidth"] = 25
            else:
                signal = "LOW SIGNAL / ROAMING"
                metrics["signal_quality"] = 40
                metrics["bandwidth"] = 5
        except:
            latency = 999
            signal = "CONNECTION ERROR"
        return latency, signal, metrics

    @staticmethod
    def get_system_uptime() -> str:
        uptime_seconds = time.time() - st.session_state.connection_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# --- 6. SATELLITE TRACKING ---
class SatelliteTracker:
    @staticmethod
    def create_satellite_map(center_lat: float = 18.5392, center_lon: float = -72.3350):
        if not MAP_READY:
            return None
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=3,
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri'
        )
        for sat_name, pos in SATELLITE_POSITIONS.items():
            color = '#00ff88' if pos['status'] == 'active' else '#ffaa00'
            icon_html = f"""
                <div style="background: radial-gradient(circle, {color}, #000); width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 20px {color};"></div>
            """
            folium.Marker(
                location=[pos['lat'], pos['lon']],
                popup=f"{sat_name}<br>Altitude: {pos['alt']} km",
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)
        folium.CircleMarker(
            location=[center_lat, center_lon],
            radius=20,
            color="#00ff88",
            fill=True,
            fill_color="#00ff88",
            fill_opacity=0.8,
            popup="YOUR LOCATION"
        ).add_to(m)
        return m

# --- 7. COLLABORATION FEED ---
class CollaborationFeed:
    @staticmethod
    def render_feed():
        st.markdown("### 🌐 Global Collaboration Network")
        with st.form("post_form", clear_on_submit=True):
            post_content = st.text_area("Share an update...", height=100)
            if st.form_submit_button("🚀 Broadcast"):
                if post_content:
                    post = {
                        "id": hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8],
                        "user": st.session_state.profile["name"],
                        "content": post_content,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "likes": 0,
                        "comments": []
                    }
                    st.session_state.posts.insert(0, post)
                    st.rerun()
        st.divider()
        for post in st.session_state.posts:
            with st.container():
                st.markdown(f"**{post['user']}** • {post['timestamp']}")
                st.markdown(f"<div class='post-card'>{post['content']}</div>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 8])
                with col1:
                    if st.button(f"👍 {post['likes']}", key=f"like_{post['id']}"):
                        post['likes'] += 1
                        st.rerun()
                st.divider()

# --- 8. OWNER'S RECLAIM ---
class OwnerReclaimSystem:
    @staticmethod
    def render_owner_panel():
        st.markdown("### 🔐 Founder's Command Center")
        session_duration = time.time() - st.session_state.connection_time
        data_comp_rate = 0.035
        st.session_state.data_comp = session_duration * data_comp_rate
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Compensation", f"${st.session_state.data_comp:.4f}")
        with col2:
            st.metric("Session Duration", SystemHealthMonitor.get_system_uptime())
        with col3:
            st.metric("Active Connections", np.random.randint(50, 500))
        
        st.divider()
        st.markdown("### 💰 Withdrawal Options")
        withdrawal_method = st.selectbox("Method", ["MonCash", "Bank Transfer", "Satellite Credit"])
        withdrawal_amount = st.number_input("Amount ($)", min_value=0.0, max_value=float(st.session_state.data_comp))
        
        if st.button("🚀 Initiate Transfer"):
            if withdrawal_amount <= st.session_state.data_comp:
                st.balloons()
                st.success(f"✅ Transferred ${withdrawal_amount:.4f} via {withdrawal_method}")
                st.session_state.data_comp -= withdrawal_amount

# --- 9. PROFILE MANAGEMENT ---
class ProfileManager:
    @staticmethod
    def render_profile_settings():
        st.markdown("### 👤 Satellite Identity Management")
        with st.form("profile_form"):
            st.session_state.profile["name"] = st.text_input("Display Name", value=st.session_state.profile["name"])
            st.session_state.profile["bio"] = st.text_area("Bio", value=st.session_state.profile["bio"])
            st.session_state.profile["location"] = st.text_input("Location", value=st.session_state.profile["location"])
            if st.form_submit_button("💾 Save Changes"):
                st.success("Profile updated!")

# --- 10. MAIN APP ---
def main_app():
    with st.sidebar:
        st.markdown("## 🌐 **GLOBALINTERNET.PY**")
        latency, signal, metrics = SystemHealthMonitor.get_network_metrics()
        uptime = SystemHealthMonitor.get_system_uptime()
        
        st.markdown("### 🛡️ System Health")
        st.markdown(f"""
        <div class='health-text'>
        📡 Signal: {signal}<br>
        ⏱️ Latency: {latency}ms<br>
        🚀 Bandwidth: {metrics['bandwidth']} Mbps<br>
        ⏰ Uptime: {uptime}<br>
        🔒 Status: ENCRYPTED
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 💎 Data Compensation")
        st.markdown(f"💰 **${st.session_state.data_comp:.4f}**")
        
        menu_options = {
            "Collaboration Feed": CollaborationFeed.render_feed,
            "Satellite Tracking Map": render_satellite_map,
            "Profile Settings": ProfileManager.render_profile_settings,
            "Owner's Reclaim": OwnerReclaimSystem.render_owner_panel
        }
        
        choice = option_menu(
            "System Access",
            options=list(menu_options.keys()),
            icons=['📡', '🛰️', '👤', '🔐'],
            menu_icon="cast",
            default_index=0
        )
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    menu_options[choice]()

def render_satellite_map():
    st.markdown("### 🛰️ Global Satellite Network")
    if MAP_READY:
        if st.checkbox("Track my location", value=True):
            try:
                g = geocoder.ip('me')
                center_lat, center_lon = g.latlng if g.ok else (18.5392, -72.3350)
            except:
                center_lat, center_lon = 18.5392, -72.3350
        else:
            center_lat, center_lon = 18.5392, -72.3350
        
        m = SatelliteTracker.create_satellite_map(center_lat, center_lon)
        if m:
            folium_static(m, width=1000, height=600)
    else:
        st.info("🗺️ Satellite map requires: folium, streamlit-folium, geocoder")

# --- 11. LOGIN ---
def login_interface():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='glow-text' style='text-align: center;'>🌐 GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
        st.markdown("---")
        with st.form("login"):
            password = st.text_input("Password", type="password")
            if st.form_submit_button("🚀 Connect"):
                if password == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.connection_time = time.time()
                    st.rerun()
                else:
                    st.error("Invalid password")

# --- 12. RUN ---
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
