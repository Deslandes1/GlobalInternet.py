import streamlit as st
import pandas as pd
import time
import socket
from datetime import datetime

# --- 1. ROBUST MODULE IMPORTS ---
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    VIDEO_READY = True
except Exception: VIDEO_READY = False

try:
    from streamlit_folium import folium_static
    import folium
    MAP_READY = True
except Exception: MAP_READY = False

# --- 2. THEME & INTERFACE ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

def apply_ui():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
            background-size: cover; background-attachment: fixed;
        }
        .stMetric { background: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; border: 1px solid #00FF00; }
        .post-card { background: rgba(0,0,0,0.8); padding: 20px; border-radius: 15px; border: 1px solid #1E90FF; margin-bottom: 15px; }
        .health-text { font-family: monospace; color: #00FF00; font-size: 14px; }
        </style>
    """, unsafe_allow_html=True)

apply_ui()

# --- 3. BACKSTAGE LOGIC & PERSISTENCE ---
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_BIZ_NUM = "(509)-47385663"

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "data_comp" not in st.session_state: st.session_state.data_comp = 0.0
if "posts" not in st.session_state: st.session_state.posts = []
if "profile" not in st.session_state:
    st.session_state.profile = {"name": "Gesner Deslandes", "bio": "Python Expert", "visibility": "Public"}

# Silent Transaction Accumulator
if st.session_state.logged_in:
    st.session_state.data_comp += 0.035 

# --- 4. HEALTH MONITOR LOGIC ---
def get_health_metrics():
    # Simulated signal strength based on server response
    start_time = time.time()
    try:
        socket.gethostbyname("google.com")
        latency = round((time.time() - start_time) * 1000, 2)
    except: latency = 999
    
    if latency < 150: signal = "SATELLITE (STARLINK/HIGH-SPEED)"
    elif latency < 400: signal = "LOCAL DATA (NATCOM/DIGICEL)"
    else: signal = "LOW SIGNAL / ROAMING"
    return latency, signal

# --- 5. APPLICATION MODULES ---

def main_app():
    # Sidebar: Identity & Health Monitor
    st.sidebar.title("💎 GLOBALINTERNET.PY")
    latency, signal = get_health_metrics()
    
    st.sidebar.markdown(f"### 🛡️ System Health")
    st.sidebar.markdown(f"<p class='health-text'>Signal: {signal}<br>Latency: {latency}ms<br>Status: ENCRYPTED</p>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    menu = ["Collaboration Feed", "Satellite Tracking Map", "Live Broadcast", "Profile Settings", "Owner's Reclaim"]
    choice = st.sidebar.selectbox("System Access", menu)

    # --- FEED ---
    if choice == "Collaboration Feed":
        st.header("🌐 Collaboration Feed")
        with st.form("post_form", clear_on_submit=True):
            user_msg = st.text_area("Broadcast professional status:")
            if st.form_submit_button("Broadcast"):
                st.session_state.posts.insert(0, {"user": st.session_state.profile["name"], "text": user_msg, "likes": 0, "comments": []})
        
        for i, p in enumerate(st.session_state.posts):
            st.markdown(f"<div class='post-card'><b>👤 {p['user']}</b><br>{p['text']}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 6])
            if c1.button(f"👍 {p['likes']}", key=f"lk_{i}"):
                p['likes'] += 1
                st.rerun()

    # --- SATELLITE MAP ---
    elif choice == "Satellite Tracking Map":
        st.header("🛰️ Active Satellite Map")
        if MAP_READY:
            m = folium.Map(location=[18.5392, -72.3350], zoom_start=4, tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", attr="Esri")
            folium.CircleMarker(
                location=[18.5392, -72.3350], radius=15, color="#00FF00", fill=True, fill_color="#00FF00", fill_opacity=0.8,
                popup=f"{st.session_state.profile['name']} - LIVE SIGNAL"
            ).add_to(m)
            folium_static(m, width=1000)
        else: st.error("Map components failed. Please refresh.")

    # --- BROADCAST ---
    elif choice == "Live Broadcast":
        st.header("📹 Live Broadcast")
        if VIDEO_READY:
            rtc_config = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
            webrtc_streamer(key="broadcast", mode=WebRtcMode.SENDRECV, rtc_configuration=rtc_config)
        else: st.error("Video drivers not active.")

    # --- PROFILE ---
    elif choice == "Profile Settings":
        st.header("👤 Account Settings")
        st.session_state.profile["name"] = st.text_input("Display Name:", value=st.session_state.profile["name"])
        st.session_state.profile["bio"] = st.text_area("Professional Bio:", value=st.session_state.profile["bio"])
        if st.button("Save & Sync"): st.success("Profile saved.")

    # --- RECLAIM ---
    elif choice == "Owner's Reclaim":
        st.header("🔐 Founder Backstage")
        cin = st.text_input("Enter Owner CIN:", type="password")
        if cin == OWNER_CIN:
            st.metric("Total Data Compensation", f"${st.session_state.data_comp:.4f}")
            if st.button("Transfer to MonCash"):
                st.balloons()
                st.session_state.data_comp = 0.0

# --- EXECUTION ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
    with st.columns([1,1,1])[1]:
        pwd = st.text_input("Password:", type="password")
        if st.button("Login"):
            if pwd == GLOBAL_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
else:
    main_app()
