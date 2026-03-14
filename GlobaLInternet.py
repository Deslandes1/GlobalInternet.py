"""
GLOBALINTERNET.PY - Satellite Communication Platform
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
import requests

# Page config
st.set_page_config(
    page_title="GLOBALINTERNET.PY",
    page_icon="🌐",
    layout="wide"
)

# Constants
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"

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
        "name": "Gesner Deslandes",
        "bio": "Satellite Communications Specialist",
        "location": "Port-au-Prince, Haiti"
    }

# UI Styling
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a1929 0%, #1a1f2e 100%);
    }
    .stMetric {
        background: rgba(10, 25, 47, 0.8);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #00ff88;
    }
    .post-card {
        background: rgba(17, 34, 64, 0.9);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #00a8ff;
        margin: 10px 0;
        color: white;
    }
    .health-text {
        font-family: monospace;
        color: #00ff88;
        background: rgba(0,0,0,0.5);
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #00ff88;
    }
    .stButton > button {
        background: linear-gradient(45deg, #00ff88, #00a8ff);
        color: black;
        border: none;
        border-radius: 25px;
    }
    </style>
""", unsafe_allow_html=True)

# Health monitoring
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

# Collaboration Feed
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

# Satellite Map (Simplified)
def render_map():
    st.header("🛰️ Satellite Network")
    
    # Satellite data
    sats = {
        "Starlink-1": {"lat": 32.77, "lon": -96.79, "status": "Active"},
        "Starlink-2": {"lat": 35.68, "lon": 139.69, "status": "Active"},
        "Starlink-3": {"lat": 51.50, "lon": -0.12, "status": "Active"},
        "Starlink-4": {"lat": 18.53, "lon": -72.33, "status": "Priority"}
    }
    
    # Display as table
    df = pd.DataFrame([
        {"Satellite": name, "Latitude": data["lat"], "Longitude": data["lon"], "Status": data["status"]}
        for name, data in sats.items()
    ])
    st.dataframe(df, use_container_width=True)
    
    # Stats
    st.divider()
    cols = st.columns(4)
    for i, (name, data) in enumerate(sats.items()):
        with cols[i % 4]:
            st.metric(name, data["status"], f"{data['lat']:.1f}°, {data['lon']:.1f}°")

# Profile Settings
def render_profile():
    st.header("👤 Profile Settings")
    
    with st.form("profile_form"):
        name = st.text_input("Name", value=st.session_state.profile["name"])
        bio = st.text_area("Bio", value=st.session_state.profile["bio"])
        loc = st.text_input("Location", value=st.session_state.profile["location"])
        
        if st.form_submit_button("💾 Save"):
            st.session_state.profile.update({"name": name, "bio": bio, "location": loc})
            st.success("Profile updated!")

# Owner's Reclaim
def render_reclaim():
    st.header("🔐 Owner's Dashboard")
    
    # Update compensation
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
    
    # Withdrawal
    st.subheader("💰 Withdraw Funds")
    method = st.selectbox("Method", ["MonCash", "Bank Transfer", "Crypto"])
    amount = st.number_input("Amount ($)", 0.0, float(st.session_state.data_comp))
    
    if st.button("🚀 Transfer", use_container_width=True):
        if amount > 0:
            st.balloons()
            st.success(f"Transferred ${amount:.2f} via {method}")
            st.session_state.data_comp -= amount

# Main app
def main():
    with st.sidebar:
        st.title("🌐 GLOBALINTERNET.PY")
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
    
    # Render selected page
    pages[choice]()

# Login
def login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🌐 GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
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

# Run
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login()
    else:
        main()
