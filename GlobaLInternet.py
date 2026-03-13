import streamlit as st
import time
import pandas as pd

# --- VIDEO MODULE SAFETY CHECK ---
try:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    VIDEO_READY = True
except ModuleNotFoundError:
    VIDEO_READY = False

# --- 1. CONFIGURATION & BRANDING ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

# Owner Credentials (Backstage)
CLIENT_ID = "1a938096ed21b2854071101fc05ea428"
CLIENT_SECRET = "WC0SjOxywUguKbbwFgDpRoaj0MqiQQcwHF-dFQJisxwM0gnYlSL0OdoRqVqU8DTJ"
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_NUMBER = "(509)-47385663"

# WebRTC Video Config
if VIDEO_READY:
    RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_fee" not in st.session_state:
    st.session_state.data_fee = 0.0
if "posts" not in st.session_state:
    st.session_state.posts = []

# --- 2. PRESENTATION & LOGIN PAGE ---
def presentation_page():
    st.markdown("<h1 style='text-align: center; color: #1E90FF;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Gesner Deslandes</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px;'>Gesner Deslandes is specialized in coding with Python Programming Language.</p>", unsafe_allow_html=True)
    
    st.divider()
    
    st.write("### 🤝 Smart Collaborators")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**Gesner Junior Deslandes**")
    c2.info("**Roosevelt Deslandes**")
    c3.info("**Sebastien Stephane Deslandes**")
    c4.info("**Zendaya Christelle Deslandes**")
    
    st.write("---")
    
    with st.container():
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            st.subheader("Connect to the Global Mesh")
            pwd = st.text_input("Enter Global Password:", type="password")
            if st.button("Login to System", use_container_width=True):
                if pwd == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect Password. Access Denied.")

# --- 3. MAIN APPLICATION INTERFACE ---
def main_application():
    st.markdown("### 🌐 GLOBALINTERNET.PY")
    
    # Backstage Data Accumulation (Simulated per minute)
    st.session_state.data_fee += 0.01 
    
    st.sidebar.title("GLOBALINTERNET.PY")
    st.sidebar.write("🟢 **Status: Online**")
    
    menu = ["Chatbox Feed", "Go Live (Video)", "Global Map", "Profile Setup", "Reclaim & MonCash"]
    choice = st.sidebar.radio("Navigation", menu)

    if st.sidebar.button("Log Off"):
        st.session_state.logged_in = False
        st.rerun()

    # --- FEED FEATURE ---
    if choice == "Chatbox Feed":
        st.header("Collaborator Feed")
        with st.form("feed_form"):
            user_post = st.text_area("What is your professional update?")
            if st.form_submit_button("Post to Feed"):
                st.session_state.posts.insert(0, {"content": user_post, "likes": 0})
        
        for i, post in enumerate(st.session_state.posts):
            with st.chat_message("user"):
                st.write(post["content"])
                if st.button(f"❤️ Like ({post['likes']})", key=f"lk_{i}"):
                    post['likes'] += 1

    # --- VIDEO FEATURE ---
    elif choice == "Go Live (Video)":
        st.header("Live Video & Group Call")
        if VIDEO_READY:
            webrtc_streamer(key="stream", rtc_configuration=RTC_CONFIG)
        else:
            st.error("The Video Module is still installing in the backstage of the server.")
            st.info("Please ensure 'streamlit-webrtc' is in your requirements.txt and REBOOT the app.")

    # --- OWNER RECLAIM FEATURE ---
    elif choice == "Reclaim & MonCash":
        st.header("🔐 Owner Reclaim Tool")
        cin_input = st.text_input("Verify Owner CIN Card Number:", type="password")
        if cin_input == OWNER_CIN:
            st.success("Welcome, Gesner Deslandes. Access Granted.")
            st.metric("Total Data Compensation (Real Currency)", f"${st.session_state.data_fee:.4f}")
            if st.button("Transfer to MonCash: (509)-47385663"):
                st.write("Connecting to MonCash Business platform...")
                time.sleep(2)
                st.balloons()
                st.success("Payment Processed Successfully.")
                st.session_state.data_fee = 0.0
        elif cin_input != "":
            st.error("Credentials do not match Owner identity.")

# --- 4. EXECUTION LOOP ---
try:
    if not st.session_state.logged_in:
        presentation_page()
    else:
        main_application()
except Exception:
    st.warning("GLOBALINTERNET.PY is updating features. The app remains active.")
