"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 3.2.0 (with pigeon logo and OwnerSpace2025)
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import socket
import hashlib
from datetime import datetime
import requests
from supabase import create_client, Client

# Page config
st.set_page_config(page_title="GLOBALINTERNET.PY", page_icon="🕊️", layout="wide")

# --- Supabase client with error handling ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    
    if not url or not key:
        st.warning("⚠️ Supabase credentials not found. User registration/login disabled.")
        return None
    
    if not url.startswith(("http://", "https://")):
        st.error("❌ SUPABASE_URL must start with http:// or https://")
        return None
    
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {e}")
        return None

supabase = init_supabase()

# --- Secrets ---
GLOBAL_PASSWORD = st.secrets.get("GLOBAL_PASSWORD", "20082021")
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")  # <-- OwnerSpace2025

# --- Session state initialization ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "data_comp" not in st.session_state:
    st.session_state.data_comp = 0.0
if "connection_time" not in st.session_state:
    st.session_state.connection_time = time.time()
if "posts" not in st.session_state:
    st.session_state.posts = []
if "profile" not in st.session_state:
    st.session_state.profile = {
        "name": "Guest",
        "bio": "",
        "location": ""
    }
if "owner_space_access" not in st.session_state:
    st.session_state.owner_space_access = False

# --- UI styling with pigeon logo and names ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #f0f4fa 0%, #d9e2ef 100%);
        color: #1e2a3a;
    }
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,168,255,0.3);
    }
    /* Pigeon logo with red/blue gradient */
    .pigeon-logo {
        font-size: 5rem;
        text-align: center;
        background: linear-gradient(135deg, #0044cc 0%, #0044cc 50%, #cc0000 50%, #cc0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
        width: 100%;
    }
    .owner-name {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 600;
        color: #0a2a44;
        margin-top: -10px;
    }
    .collaborators {
        text-align: center;
        font-size: 0.9rem;
        color: #2c3e50;
        background: rgba(255,255,255,0.5);
        padding: 8px 16px;
        border-radius: 40px;
        margin: 10px 0;
        border: 1px solid rgba(0,68,204,0.2);
    }
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
    .post-card {
        background: rgba(255,255,255,0.7);
        backdrop-filter: blur(8px);
        padding: 20px 25px;
        border-radius: 20px;
        border: 1px solid rgba(0,168,255,0.2);
        margin: 15px 0;
        color: #1e2a3a;
    }
    .health-text {
        font-family: 'Courier New', monospace;
        color: #0a2a44;
        background: rgba(255,255,255,0.6);
        backdrop-filter: blur(5px);
        padding: 15px;
        border-radius: 16px;
        border-left: 4px solid #00a8ff;
    }
    .stButton > button {
        background: linear-gradient(105deg, #00a8ff 0%, #0080ff 100%);
        color: white;
        border: none;
        border-radius: 40px;
        padding: 10px 28px;
        font-weight: 600;
        box-shadow: 0 8px 16px rgba(0,128,255,0.2);
    }
    .stButton > button:hover {
        background: linear-gradient(105deg, #0080ff 0%, #0066cc 100%);
        box-shadow: 0 12px 24px rgba(0,128,255,0.3);
        transform: scale(1.02);
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

# --- Supabase auth functions ---
def sign_up(email, password, name):
    if supabase is None:
        st.error("Registration unavailable (Supabase not configured).")
        return False
    try:
        user = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": name}}
        })
        if user.user:
            st.success("Sign-up successful! Please log in.")
            return True
    except Exception as e:
        st.error(f"Sign-up failed: {e}")
        return False

def log_in(email, password):
    if supabase is None:
        st.error("Login unavailable (Supabase not configured).")
        return
    try:
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if user.user:
            st.session_state.logged_in = True
            st.session_state.user = user.user
            st.session_state.profile["name"] = user.user.user_metadata.get("full_name", email)
            st.session_state.profile["email"] = email
            st.session_state.connection_time = time.time()
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def logout():
    if supabase:
        supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.owner_space_access = False
    st.rerun()

# --- Owner Space (using OwnerSpace2025) ---
def owner_space():
    st.header("🕊️ Owner Space")
    if not st.session_state.owner_space_access:
        with st.form("owner_space_login"):
            pwd = st.text_input("Enter Owner Space Password", type="password")
            if st.form_submit_button("Access"):
                if pwd == OWNSPACE_PASSWORD:
                    st.session_state.owner_space_access = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return
    
    st.success("Welcome to the Owner Space!")
    st.markdown("Here you can manage privileged settings.")
    # Add any owner-specific functionality here
    if st.button("Logout from Owner Space"):
        st.session_state.owner_space_access = False
        st.rerun()

# --- Main app pages ---
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

def render_profile():
    st.header("👤 Profile Settings")
    with st.form("profile_form"):
        name = st.text_input("Name", value=st.session_state.profile["name"])
        bio = st.text_area("Bio", value=st.session_state.profile.get("bio", ""))
        loc = st.text_input("Location", value=st.session_state.profile.get("location", ""))
        if st.form_submit_button("💾 Save"):
            st.session_state.profile.update({"name": name, "bio": bio, "location": loc})
            st.success("Profile updated!")

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

# --- Main app with sidebar ---
def main_app():
    with st.sidebar:
        # Pigeon logo and owner name
        st.markdown("<div class='pigeon-logo'>🕊️</div>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes<br>
            Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
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
        st.markdown(f"👤 **Logged in as:** {st.session_state.profile['name']}")
        if st.button("🚪 Logout"):
            logout()
        st.divider()
        
        # Navigation
        pages = {
            "📡 Collaboration Feed": render_feed,
            "🛰️ Satellite Map": render_map,
            "👤 Profile": render_profile,
            "🔐 Owner's Dashboard": render_reclaim,
            "🕊️ Owner Space": owner_space
        }
        choice = st.selectbox("Menu", list(pages.keys()))
    pages[choice]()

# --- Login / Sign-up interface ---
def login_interface():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Pigeon logo and names on login page
        st.markdown("<div style='text-align: center;'><span class='pigeon-logo' style='font-size:6rem;'>🕊️</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #0a2a44;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name' style='font-size:1.8rem;'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators' style='font-size:1rem;'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes · Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("🚀 Login", use_container_width=True):
                    log_in(email, password)

        with tab2:
            with st.form("signup_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("📝 Sign Up", use_container_width=True):
                    if name and email and password:
                        sign_up(email, password, name)
                    else:
                        st.warning("Please fill all fields")

        # Optional admin login
        st.markdown("---")
        with st.expander("Admin Access"):
            admin_pwd = st.text_input("Admin Password", type="password")
            if st.button("Admin Login"):
                if admin_pwd == GLOBAL_PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.user = {"email": "admin@local"}
                    st.session_state.profile["name"] = "Admin"
                    st.session_state.connection_time = time.time()
                    st.rerun()
                else:
                    st.error("Invalid admin password")

# --- Main entry point ---
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
