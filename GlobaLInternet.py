import streamlit as st
import pandas as pd
import time

# --- 1. VIDEO MODULE CHECK ---
try:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    VIDEO_READY = True
except ImportError:
    VIDEO_READY = False

# --- 2. CONFIGURATION & BACKGROUND ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

def add_bg_map():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-image: url("https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=2070&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }
        [data-testid="stSidebar"] {
            background-color: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        .stMarkdown, h1, h2, h3, p {
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_map()

# Credentials
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"

# --- 3. SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_fee" not in st.session_state:
    st.session_state.data_fee = 0.0
if "posts" not in st.session_state:
    st.session_state.posts = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {"name": "Gesner Deslandes", "bio": "Python Expert"}

# --- 4. NAVIGATION PAGES ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Gesner Deslandes</h3>", unsafe_allow_html=True)
    st.write("---")
    st.write("### 👥 Smart Collaborators")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("Gesner Junior Deslandes")
    c2.info("Roosevelt Deslandes")
    c3.info("Sebastien Stephane Deslandes")
    c4.info("Zendaya Christelle Deslandes")
    
    with st.columns([1,2,1])[1]:
        pwd = st.text_input("System Access Password:", type="password")
        if st.button("Enter Global Network"):
            if pwd == GLOBAL_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Access Key.")

def main_app():
    st.sidebar.title("GLOBALINTERNET.PY")
    st.session_state.data_fee += 0.005 # Auto-accumulate data reward
    
    menu = ["Chatbox Feed", "Go Live (Video)", "Global Map", "Profile Setup", "Reclaim & MonCash"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "Chatbox Feed":
        st.header("Global Collaborator Feed")
        with st.form("post_form", clear_on_submit=True):
            msg = st.text_area("Update your status:")
            if st.form_submit_button("Broadcast Message"):
                st.session_state.posts.insert(0, {"text": msg, "user": st.session_state.user_profile["name"]})
        for p in st.session_state.posts:
            st.chat_message("user").write(f"**{p['user']}**: {p['text']}")

    elif choice == "Go Live (Video)":
        st.header("Live Video Connection")
        if VIDEO_READY:
            webrtc_streamer(key="global-video", rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
        else:
            st.error("Video drivers not yet installed on server. Check requirements.txt.")

    elif choice == "Global Map":
        st.header("User Connection Points")
        # Ensure column names are 'lat' and 'lon' for st.map
        map_points = pd.DataFrame({'lat': [18.5392, 19.75, 40.71], 'lon': [-72.335, -72.2, -74.00]})
        st.map(map_points)

    elif choice == "Profile Setup":
        st.header("👤 Your Profile")
        st.session_state.user_profile["name"] = st.text_input("Name:", value=st.session_state.user_profile["name"])
        st.session_state.user_profile["bio"] = st.text_area("Professional Bio:", value=st.session_state.user_profile["bio"])
        if st.button("Save Changes"):
            st.success("Profile synchronized with global database.")

    elif choice == "Reclaim & MonCash":
        st.header("🔐 Secure Reclaim Tool")
        cin = st.text_input("Enter Owner CIN:", type="password")
        if cin == OWNER_CIN:
            st.metric("Total Data Reward", f"${st.session_state.data_fee:.4f}")
            if st.button("Payout to MonCash: (509)-47385663"):
                st.balloons()
                st.success("Transferring... Funds cleared to Gesner Deslandes.")
                st.session_state.data_fee = 0.0

# --- 5. EXECUTION ---
if not st.session_state.logged_in:
    login_page()
else:
    main_app()
