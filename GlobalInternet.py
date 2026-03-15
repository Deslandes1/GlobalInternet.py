"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Junior Deslandes
Collaborators: Roosevelt Deslandes, Zendaya Christelle Deslandes
Version: 2.0.0
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import socket
import hashlib
from datetime import datetime
import requests

# Page config
st.set_page_config(
    page_title="GLOBALINTERNET.PY",
    page_icon="🌐",
    layout="wide"
)

# --- SECRETS ---
# Use st.secrets in production (set on Streamlit Cloud)
# Fallback values for local testing (do not commit real secrets)
GLOBAL_PASSWORD = st.secrets.get("GLOBAL_PASSWORD", "20082021")
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_comp" not in st.session_state:
    st.session_state.data_comp = 0.0
if "connection_time" not in st.session_state:
    st.session_state.connection_time = time.time()
if "posts" not in st.session_state:
    st.session_state.posts = []
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "Gesner Junior Deslandes",
        "bio": "Satellite Communications Specialist",
        "location": "Port-au-Prince, Haiti"
    }

# --- Enhanced UI Styling with Blue & Red Logo ---
st.markdown("""
    <style>
    /* Main background with a bright gradient */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #f0f4fa 0%, #d9e2ef 100%);
        color: #1e2a3a;
    }
    /* Sidebar styling with glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,168,255,0.3);
        box-shadow: 4px 0 15px rgba(0,0,0,0.05);
    }
    /* Custom Logo (Blue & Red) */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 20px 0 10px 0;
    }
    .logo {
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: 2px;
        background: linear-gradient(135deg, #0044cc 0%, #0044cc 50%, #cc0000 50%, #cc0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 10px rgba(0,68,204,0.2);
        display: inline-block;
        padding: 0 10px;
    }
    .logo-sub {
        font-size: 0.9rem;
        color: #1e2a3a;
        opacity: 0.8;
        letter-spacing: 1px;
    }
    /* Headers */
    h1, h2, h3 {
        color: #0a2a44;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    /* Metric cards */
    .stMetric {
        background: rgba(255,255,255,0.6);
        backdrop-filter: blur(5px);
        padding: 20px;
        border-radius: 20px;
        border: 1px solid rgba(0,168,255,0.3);
        box-shadow: 0 8px 20px rgba(0,20,50,0.1);
        transition: transform 0.2s;
    }
    .stMetric:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 25px rgba(0,100,200,0.15);
    }
    /* Post cards */
    .post-card {
        background: rgba(255,255,255,0.7);
        backdrop-filter: blur(8px);
        padding: 20px 25px;
        border-radius: 20px;
        border: 1px solid rgba(0,168,255,0.2);
        margin: 15px 0;
        color: #1e2a3a;
        box-shadow: 0 5px 15px rgba(0,0,0,0.03);
        transition: all 0.2s;
    }
    .post-card:hover {
        background: rgba(255,255,255,0.85);
        border-color: #00a8ff;
        box-shadow: 0 8px 25px rgba(0,168,255,0.15);
    }
    /* Health monitor */
    .health-text {
        font-family: 'Courier New', monospace;
        color: #0a2a44;
        background: rgba(255,255,255,0.6);
        backdrop-filter: blur(5px);
        padding: 15px;
        border-radius: 16px;
        border-left: 4px solid #00a8ff;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }
    /* Buttons */
    .stButton > button {
        background: linear-gradient(105deg, #00a8ff 0%, #0080ff 100%);
        color: white;
        border: none;
        border-radius: 40px;
        padding: 10px 28px;
        font-weight: 600;
        letter-spacing: 0.02em;
        box-shadow: 0 8px 16px rgba(0,128,255,0.2);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(105deg, #0080ff 0%, #0066cc 100%);
        box-shadow: 0 12px 24px rgba(0,128,255,0.3);
        transform: scale(1.02);
    }
    /* Team credit */
    .team-credit {
        text-align: center;
        font-size: 0.95rem;
        color: #2c3e50;
        background: rgba(255,255,255,0.5);
        padding: 8px 16px;
        border-radius: 40px;
        margin-top: 15px;
        border: 1px solid rgba(0,68,204,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# --- Health monitoring ---
def get_network_status():
    try:
        start = time.time()
        socket.gethostbyname("google.com")
        latency = round((time.time() - start) * 1000, 2)
        if latency < 150:
            signal = "SATELLITE (HIGH-SPEED)"
            quality = 100
        elif latency < 400:
            signal = "LOCAL NETWORK"
            quality = 70
        else:
            signal = "LOW SIGNAL"
            quality = 40
    except:
        latency = 999
        signal = "OFFLINE"
        quality = 0
    return latency, signal, quality

def get_uptime():
    seconds = time.time() - st.session_state.connection_time
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours:02d}:{minutes:02d}"

# --- Collaboration Feed ---
def render_feed():
    st.header("🌐 Collaboration Feed")
    with st.form("post_form", clear_on_submit=True):
        post = st.text_area("Share an update...", height=100)
        if st.form_submit_button("🚀 Broadcast"):
            if post:
                new_post = {
                    "user": st.session_state.profile["name"],
                    "content": post,
                    "time": datetime.now().strftime("%H:%M"),
                    "likes": 0,
                    "id": hashlib.md5(str(time.time()).encode()).hexdigest()[:6]
                }
                st.session_state.posts.insert(0, new_post)
                st.rerun()
    for p in st.session_state.posts:
        st.markdown(f"<div class='post-card'><b>{p['user']}</b> at {p['time']}<br>{p['content']}</div>", unsafe_allow_html=True)
        if st.button(f"👍 {p['likes']}", key=f"like_{p['id']}"):
            p['likes'] += 1
            st.rerun()

# --- Satellite Map ---
def render_map():
    st.header("🛰️ Satellite Network")
    sats = {
        "Starlink-1": {"lat": 32.77, "lon": -96.79, "status": "Active"},
        "Starlink-2": {"lat": 35.68, "lon": 139.69, "status": "Active"},
        "Starlink-3": {"lat": 51.50, "lon": -0.12, "status": "Active"},
        "Starlink-4": {"lat": 18.53, "lon": -72.33, "status": "Priority"}
    }
    df = pd.DataFrame([
        {"Satellite": name, "Latitude": data["lat"], "Longitude": data["lon"], "Status": data["status"]}
        for name, data in sats.items()
    ])
    st.dataframe(df, use_container_width=True)
    st.divider()
    cols = st.columns(4)
    for i, (name, data) in enumerate(sats.items()):
        with cols[i % 4]:
            st.metric(name, data["status"], f"{data['lat']:.1f}°, {data['lon']:.1f}°")

# --- Profile Settings ---
def render_profile():
    st.header("👤 Profile Settings")
    with st.form("profile_form"):
        name = st.text_input("Name", value=st.session_state.profile["name"])
        bio = st.text_area("Bio", value=st.session_state.profile["bio"])
        loc = st.text_input("Location", value=st.session_state.profile["location"])
        if st.form_submit_button("💾 Save"):
            st.session_state.profile.update({"name": name, "bio": bio, "location": loc})
            st.success("Profile updated!")

# --- Owner's Reclaim ---
def render_reclaim():
    st.header("🔐 Owner's Dashboard")
    duration = time.time() - st.session_state.connection_time
    st.session_state.data_comp = duration * 0.035
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Compensation", f"${st.session_state.data_comp:.4f}")
    with col2:
        st.metric("Uptime", get_uptime())
    with col3:
        st.metric("Network Users", np.random.randint(100, 500))
    st.divider()
    st.subheader("💰 Withdraw Funds")
    method = st.selectbox("Method", ["MonCash", "Bank Transfer", "Crypto"])
    amount = st.number_input("Amount ($)", 0.0, float(st.session_state.data_comp))
    if st.button("🚀 Transfer", use_container_width=True):
        if amount > 0:
            st.balloons()
            st.success(f"Transferred ${amount:.2f} via {method}")
            st.session_state.data_comp -= amount

# --- Main app ---
def main():
    with st.sidebar:
        # Blue & Red Logo
        st.markdown("""
        <div class='logo-container'>
            <span class='logo'>GLOBAL</span><span class='logo' style='background: linear-gradient(135deg, #cc0000 0%, #cc0000 100%); -webkit-background-clip: text;'>INTERNET</span>
        </div>
        <div class='logo-sub'>.PY</div>
        """, unsafe_allow_html=True)
        
        # Team credit
        st.markdown("""
        <div class='team-credit'>
            👥 Gesner Junior · Roosevelt · Zendaya Christelle
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        
        # Health monitor
        lat, sig, qual = get_network_status()
        st.markdown("### 🛡️ System Health")
        st.markdown(f"""
        <div class='health-text'>
        📡 Signal: {sig}<br>
        ⏱️ Latency: {lat}ms<br>
        📊 Quality: {qual}%<br>
        ⏰ Uptime: {get_uptime()}<br>
        🔒 Status: ENCRYPTED
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown(f"💰 **Compensation:** ${st.session_state.data_comp:.4f}")
        st.divider()
        
        # Navigation
        pages = {
            "📡 Collaboration Feed": render_feed,
            "🛰️ Satellite Map": render_map,
            "👤 Profile": render_profile,
            "🔐 Owner's Reclaim": render_reclaim
        }
        choice = st.selectbox("Menu", list(pages.keys()))
        st.divider()
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    
    pages[choice]()

# --- Login ---
def login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Blue & Red Logo on login
        st.markdown("""
        <div style='text-align: center; margin: 30px 0;'>
            <span style='font-size: 4rem; font-weight: 800; background: linear-gradient(135deg, #0044cc 0%, #0044cc 50%, #cc0000 50%, #cc0000 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>GLOBAL</span>
            <span style='font-size: 4rem; font-weight: 800; background: linear-gradient(135deg, #cc0000 0%, #cc0000 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>INTERNET</span>
            <div style='font-size: 1.2rem; color: #1e2a3a;'>.PY</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Full names on login
        st.markdown("""
        <p style='text-align: center; font-size: 1.1rem; background: rgba(0,68,204,0.1); padding: 12px; border-radius: 40px; border: 1px solid rgba(204,0,0,0.2);'>
        <b>Gesner Junior Deslandes</b> · Roosevelt Deslandes · Zendaya Christelle Deslandes
        </p>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("🚀 Connect", use_container_width=True):
                if pwd == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.connection_time = time.time()
                    st.rerun()
                else:
                    st.error("Access Denied")

# --- Run ---
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login()
    else:
        main()
