import streamlit as st
import pandas as pd
import time

# --- VIDEO MODULE ENGINE ---
try:
    from streamlit_webrtc import webrtc_streamer, RTCConfiguration
    VIDEO_READY = True
except ImportError:
    VIDEO_READY = False

# --- 1. INTERFACE STYLING (Global Map Background) ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

def apply_global_theme():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-image: url("https://images.unsplash.com/photo-1521295121783-8a321d551ad2?q=80&w=2070&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        [data-testid="stSidebar"] {
            background-color: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
        }
        .stMarkdown, h1, h2, h3, p, label {
            color: white !important;
        }
        div[data-testid="stMetricValue"] {
            color: #2ecc71 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_global_theme()

# --- 2. BACKSTAGE DATA & SECURITY ---
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_BIZ_NUM = "(509)-47385663"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "data_compensation" not in st.session_state:
    st.session_state.data_compensation = 0.0
if "posts" not in st.session_state:
    st.session_state.posts = []
if "profile" not in st.session_state:
    st.session_state.profile = {"name": "Gesner Deslandes", "bio": "Python Programming Specialist"}

# --- 3. APP MODULES ---

def login_screen():
    st.markdown("<h1 style='text-align: center;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Gesner Deslandes</h2>", unsafe_allow_html=True)
    st.write("---")
    st.info("### Gesner Deslandes is specialized in coding with Python Programming language.")
    
    st.write("#### 👨‍💻 Smart Collaborators:")
    cols = st.columns(4)
    names = ["Gesner Junior Deslandes", "Roosevelt Deslandes", "Sebastien Stephane Deslandes", "Zendaya Christelle Deslandes"]
    for i, name in enumerate(names):
        cols[i].code(name)

    with st.container():
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            pwd = st.text_input("Global Password:", type="password")
            if st.button("Unlock GLOBALINTERNET.PY", use_container_width=True):
                if pwd == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Access Denied.")

def main_system():
    st.sidebar.title("GLOBALINTERNET.PY")
    st.sidebar.write(f"Logged in as: **{st.session_state.profile['name']}**")
    
    # Background Data Accumulation (1 minute simulation logic)
    st.session_state.data_compensation += 0.015 
    
    menu = ["Chatbox Feed", "Live Video", "Global Map", "Profile Setup", "Owner's Reclaim"]
    choice = st.sidebar.radio("Main Menu", menu)

    if choice == "Chatbox Feed":
        st.header("Global Collaborator Chatbox")
        with st.form("feed"):
            msg = st.text_area("Share a post:")
            if st.form_submit_button("Post"):
                st.session_state.posts.insert(0, {"user": st.session_state.profile["name"], "text": msg})
        for p in st.session_state.posts:
            st.chat_message("user").write(f"**{p['user']}**: {p['text']}")

    elif choice == "Live Video":
        st.header("Go Live & Group Video")
        if VIDEO_READY:
            webrtc_streamer(key="live-video", rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]})
        else:
            st.warning("Video drivers are loading. Check requirements.txt on GitHub.")

    elif choice == "Global Map":
        st.header("Collaborator Locations")
        # Ensure column names are 'lat' and 'lon' for functional map
        coords = pd.DataFrame({'lat': [18.53, 19.75, 40.71, 48.85], 'lon': [-72.33, -72.2, -74.00, 2.35]})
        st.map(coords)

    elif choice == "Profile Setup":
        st.header("Setup Professional Account")
        st.session_state.profile["name"] = st.text_input("Full Name:", value=st.session_state.profile["name"])
        st.session_state.profile["bio"] = st.text_area("Specialization:", value=st.session_state.profile["bio"])
        if st.button("Update Profile"):
            st.success("Profile saved successfully.")

    elif choice == "Owner's Reclaim":
        st.header("🔐 Owner's Reclaim")
        st.write("Feature active 24/7 for Gesner Deslandes.")
        verify_cin = st.text_input("Enter Owner Credentials (CIN):", type="password")
        
        if verify_cin == OWNER_CIN:
            st.success("Identity Verified. Access to Payment Platform Granted.")
            st.metric("Total Data Compensation Flow", f"${st.session_state.data_compensation:.4f}")
            if st.button("Process Withdrawal to Moncash"):
                st.info(f"Connecting to Moncash Business Number: {MONCASH_BIZ_NUM}")
                time.sleep(2)
                st.balloons()
                st.success("Transaction running... Money sent to your business account.")
                st.session_state.data_compensation = 0.0
        elif verify_cin:
            st.error("Unauthorized. Only the founder can access Owner's Reclaim.")

# --- 4. EXECUTION ---
if not st.session_state.logged_in:
    login_screen()
else:
    main_system()
