import streamlit as st
import time
import pandas as pd

# Safety Check for Video Module
try:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    WEBRTC_AVAILABLE = True
except ModuleNotFoundError:
    WEBRTC_AVAILABLE = False

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

# Secret Credentials
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_NUMBER = "(509)-47385663"

# WebRTC (Video) Config
if WEBRTC_AVAILABLE:
    RTC_CONFIG = RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})

# State Management
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
    st.markdown("<p style='text-align: center;'><i>Specialized in coding with Python Programming Language</i></p>", unsafe_allow_html=True)
    st.divider()
    
    st.write("### 🤝 Smart Collaborators")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**Gesner Junior Deslandes**")
    c2.info("**Roosevelt Deslandes**")
    c3.info("**Sebastien Stephane Deslandes**")
    c4.info("**Zendaya Christelle Deslandes**")
    
    with st.container():
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            pwd = st.text_input("Enter Access Password:", type="password")
            if st.button("Login", use_container_width=True):
                if pwd == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Incorrect Password.")

# --- 3. MAIN APPLICATION ---
def main_application():
    st.sidebar.title("GLOBALINTERNET.PY")
    st.session_state.data_fee += 0.01 
    
    menu = ["Chatbox Feed", "Go Live (Video)", "Reclaim (Owner Only)"]
    choice = st.sidebar.radio("Main Menu", menu)

    if choice == "Chatbox Feed":
        st.header("Collaborator Feed")
        with st.form("feed_form"):
            user_post = st.text_area("Post a message:")
            if st.form_submit_button("Post"):
                st.session_state.posts.insert(0, {"content": user_post, "likes": 0})
        
        for i, post in enumerate(st.session_state.posts):
            with st.chat_message("user"):
                st.write(post["content"])
                if st.button(f"❤️ {post['likes']}", key=f"lk_{i}"):
                    post['likes'] += 1

    elif choice == "Go Live (Video)":
        st.header("Live Video Broadcast")
        if WEBRTC_AVAILABLE:
            webrtc_streamer(key="stream", rtc_configuration=RTC_CONFIG)
        else:
            st.error("Video Module not installed. Please check your requirements.txt file on GitHub.")

    elif choice == "Reclaim (Owner Only)":
        st.header("🔐 Reclaim Backstage")
        cin_input = st.text_input("Enter CIN Number:", type="password")
        if cin_input == OWNER_CIN:
            st.success("Welcome Gesner Deslandes.")
            st.metric("Compensation Flow", f"${st.session_state.data_fee:.4f}")
            if st.button("Send to MonCash"):
                st.success("Funds sent to (509)-47385663")
                st.session_state.data_fee = 0.0

# --- 4. EXECUTION ---
if not st.session_state.logged_in:
    presentation_page()
else:
    main_application()
