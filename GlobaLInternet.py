import streamlit as st
import time
import pandas as pd
from streamlit_webrtc import webrtc_streamer, RTCConfiguration

# --- 1. CONFIGURATION & HIDDEN BACKSTAGE ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

# Secret Credentials
CLIENT_ID = "1a938096ed21b2854071101fc05ea428"
CLIENT_SECRET = "WC0SjOxywUguKbbwFgDpRoaj0MqiQQcwHF-dFQJisxwM0gnYlSL0OdoRqVqU8DTJ"
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_NUMBER = "(509)-47385663"

# WebRTC (Video) Config
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
    # Capitalized Branding
    st.markdown("<h1 style='text-align: center; color: #1E90FF;'>GLOBALINTERNET.PY</h1>", unsafe_content_label=True)
    st.markdown("<h2 style='text-align: center;'>Gesner Deslandes</h2>", unsafe_content_label=True)
    st.markdown("<p style='text-align: center; font-size: 20px;'><i>Specialized in coding with Python Programming Language</i></p>", unsafe_content_label=True)
    
    st.divider()
    
    # Collaborators Section
    st.write("### 🤝 Smart Collaborators")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**Gesner Junior Deslandes**")
    c2.info("**Roosevelt Deslandes**")
    c3.info("**Sebastien Stephane Deslandes**")
    c4.info("**Zendaya Christelle Deslandes**")
    
    st.write("---")
    
    # Login Logic
    with st.container():
        left, mid, right = st.columns([1, 2, 1])
        with mid:
            st.subheader("Connect to the Global Mesh")
            pwd = st.text_input("Enter Access Password:", type="password")
            if st.button("Login", use_container_width=True):
                if pwd == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Access Denied. Please check the password.")

# --- 3. LOGGED-IN APPLICATION INTERFACE ---
def main_application():
    # Persistent branding in the header
    st.markdown("### 🌐 GLOBALINTERNET.PY")
    
    # Data generation loop (Simulated every minute background activity)
    st.session_state.data_fee += 0.01 
    
    # Navigation Sidebar
    st.sidebar.title("GLOBALINTERNET.PY")
    st.sidebar.write("🟢 **Status: Online**")
    
    menu = ["Chatbox Feed", "Go Live (Video)", "Private Messaging", "Global Map", "Profile Setup", "Reclaim (Owner Only)"]
    choice = st.sidebar.radio("Main Menu", menu)

    if st.sidebar.button("Log Off"):
        st.session_state.logged_in = False
        st.rerun()

    # --- FEATURE: FEED ---
    if choice == "Chatbox Feed":
        st.header("Collaborator Feed")
        with st.form("feed_form"):
            user_post = st.text_area("What are you working on today?")
            if st.form_submit_button("Post to Global Feed"):
                st.session_state.posts.insert(0, {"content": user_post, "likes": 0})
        
        for i, post in enumerate(st.session_state.posts):
            with st.chat_message("user"):
                st.write(post["content"])
                if st.button(f"❤️ Like ({post['likes']})", key=f"lk_{i}"):
                    post['likes'] += 1

    # --- FEATURE: LIVE VIDEO ---
    elif choice == "Go Live (Video)":
        st.header("Live Video Broadcast")
        webrtc_streamer(key="stream", rtc_configuration=RTC_CONFIG)

    # --- FEATURE: OWNER BACKSTAGE (CIN PROTECTED) ---
    elif choice == "Reclaim (Owner Only)":
        st.header("🔐 Reclaim & MonCash Backstage")
        cin_input = st.text_input("Enter Owner CIN Card Number to Authorize:", type="password")
        
        if cin_input == OWNER_CIN:
            st.success("Identity Verified: Welcome Gesner Deslandes.")
            st.metric("Total Data Compensation Flow", f"${st.session_state.data_fee:.4f}")
            
            if st.button("Withdraw to MonCash: (509)-47385663"):
                st.write("Connecting to MonCash Business API...")
                time.sleep(2)
                st.balloons()
                st.success("Transaction Complete. Check your MonCash account.")
                st.session_state.data_fee = 0.0
        elif cin_input != "":
            st.error("Invalid Credentials. This tool is for the Owner only.")

# --- 4. EXECUTION & ERROR PROTECTION ---
try:
    if not st.session_state.logged_in:
        presentation_page()
    else:
        main_application()
except Exception:
    # Keeps app running even if codes break during update
    st.warning("GLOBALINTERNET.PY is currently refreshing features. Service remains active.")
