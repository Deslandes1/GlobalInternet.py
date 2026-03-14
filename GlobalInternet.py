import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
from PIL import Image
import nest_asyncio
from streamlit_autorefresh import st_autorefresh
from supabase import create_client, Client
import hashlib

# Apply nest_asyncio
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="GlobalInternet Fun",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .online-indicator {
        width: 12px;
        height: 12px;
        background-color: #4CAF50;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        box-shadow: 0 0 10px #4CAF50;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.2); }
        100% { opacity: 1; transform: scale(1); }
    }
    .internet-card {
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 5px solid #00b09b;
    }
    .signal-strength {
        height: 8px;
        background: linear-gradient(90deg, #00b09b, #96c93d);
        border-radius: 4px;
        margin: 10px 0;
        transition: width 0.5s;
    }
    .admin-panel {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        border: 2px solid gold;
    }
    .profit-counter {
        font-size: 36px;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        padding: 20px;
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        margin: 10px 0;
        animation: glow 2s infinite;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px #4CAF50; }
        50% { box-shadow: 0 0 20px #4CAF50; }
        100% { box-shadow: 0 0 5px #4CAF50; }
    }
    .connection-status {
        background-color: #1a1a2e;
        color: white;
        padding: 15px;
        border-radius: 10px;
        font-family: monospace;
        border: 1px solid #4CAF50;
    }
    .background-badge {
        background-color: #ffd700;
        color: black;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        animation: pulse 2s infinite;
    }
    .feature-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 4px solid #00b09b;
    }
</style>
""", unsafe_allow_html=True)

# Auto-refresh
try:
    count = st_autorefresh(interval=30000, key="auto_refresh")
except:
    pass

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        # Check if secrets exist
        if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            return create_client(url, key)
        else:
            return None
    except Exception as e:
        st.error(f"Supabase init error: {e}")
        return None

# Hash password for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.connected = False
    st.session_state.current_user = None
    st.session_state.active_connections = {}
    st.session_state.internet_pool = {
        "total_bandwidth": 1000,
        "available_bandwidth": 1000,
        "active_peers": 0,
        "data_transferred": 0,
        "background_sessions": 0
    }
    
    # Owner data
    st.session_state.owner = {
        "name": "Gesner Deslandes",
        "moncash": "50947385663",
        "total_revenue": 0.0,
        "daily_revenue": 0.0,
        "total_data": 0.0,
        "profit_rate": 0.05,
        "transactions": [],
        "auto_payment": False,
        "auto_threshold": 50.0
    }
    
    st.session_state.network = {
        "status": "ACTIVE",
        "peers": 0,
        "latency": random.randint(20, 100),
        "uptime": "99.99%"
    }
    
    st.session_state.demo_mode = False

# Initialize Supabase
supabase = init_supabase()
if supabase:
    st.session_state.supabase_connected = True
    st.session_state.demo_mode = False
else:
    st.session_state.supabase_connected = False
    st.session_state.demo_mode = True

# Header
st.markdown("""
<div class="main-header">
    <h1>🌐 GlobalInternet Fun</h1>
    <p style="font-size: 1.2em; margin-top: 5px;">Created by <strong>Gesner Deslandes, Python Developer</strong></p>
    <p>Providing FREE Internet to Everyone - 24/7 Background Connection Active!</p>
    <h3 style="color: #ffd700;">"Connect once, stay online forever!"</h3>
</div>
""", unsafe_allow_html=True)

# Show demo mode warning if needed
if st.session_state.demo_mode:
    st.warning("⚠️ Running in DEMO MODE - Using guest account only. Add Supabase secrets in Streamlit Cloud for real user accounts.")

# Authentication Section
if not st.session_state.connected:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Feature highlights
        with st.container():
            st.markdown("""
            <div class="feature-card">
                <h4>✨ Why Join GlobalInternet?</h4>
                <p>✓ 100% FREE internet access</p>
                <p>✓ 24/7 background connection</p>
                <p>✓ Works with screen off</p>
                <p>✓ Connect from anywhere</p>
                <p>✓ No data limits</p>
            </div>
            """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        
        with tab1:
            st.markdown("### Login to Your Account")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("🔌 Login & Connect", use_container_width=True):
                if st.session_state.supabase_connected:
                    try:
                        # Hash password and check user
                        hashed_pass = hash_password(login_password)
                        response = supabase.table("users").select("*").eq("username", login_username).execute()
                        
                        if response.data and len(response.data) > 0:
                            user = response.data[0]
                            if user["password"] == hashed_pass:
                                st.session_state.connected = True
                                st.session_state.current_user = login_username
                                
                                # Update last active
                                supabase.table("users").update({
                                    "last_active": datetime.now().isoformat(),
                                    "online": True
                                }).eq("username", login_username).execute()
                                
                                st.balloons()
                                st.success(f"✅ Welcome back, {login_username}!")
                                st.rerun()
                            else:
                                st.error("❌ Incorrect password")
                        else:
                            st.error("❌ User not found")
                    except Exception as e:
                        st.error(f"Login error: {e}")
                else:
                    # Demo mode - use guest account
                    if login_username == "guest" and login_password == "20082021":
                        st.session_state.connected = True
                        st.session_state.current_user = "guest"
                        st.session_state.demo_mode = True
                        st.balloons()
                        st.success("✅ Connected in DEMO MODE!")
                        st.rerun()
                    else:
                        st.error("❌ Demo mode: Use guest / 20082021")
        
        with tab2:
            st.markdown("### Create New Account")
            new_username = st.text_input("Choose Username", key="new_user")
            new_password = st.text_input("Choose Password", type="password", key="new_pass")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pass")
            email = st.text_input("Email Address (optional)")
            
            col_agree1, col_agree2 = st.columns([1,3])
            with col_agree1:
                agree = st.checkbox("I agree")
            with col_agree2:
                st.markdown("to help provide free internet by sharing anonymous usage data")
            
            if st.button("📝 Sign Up & Connect", use_container_width=True):
                if not agree:
                    st.error("Please agree to the terms")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                elif len(new_username) < 3:
                    st.error("Username must be at least 3 characters")
                elif st.session_state.supabase_connected:
                    try:
                        # Check if user exists
                        response = supabase.table("users").select("*").eq("username", new_username).execute()
                        if response.data and len(response.data) > 0:
                            st.error("Username already taken")
                        else:
                            # Create new user
                            hashed_pass = hash_password(new_password)
                            user_data = {
                                "username": new_username,
                                "password": hashed_pass,
                                "email": email,
                                "created_at": datetime.now().isoformat(),
                                "data_used": 0.0,
                                "earnings": 0.0,
                                "last_active": datetime.now().isoformat(),
                                "online": False,
                                "total_sessions": 0,
                                "premium": False
                            }
                            
                            supabase.table("users").insert(user_data).execute()
                            
                            # Auto login
                            st.session_state.connected = True
                            st.session_state.current_user = new_username
                            
                            st.balloons()
                            st.success(f"✅ Account created! Welcome, {new_username}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Signup error: {e}")
                else:
                    st.info("Supabase not connected. Please add your Supabase credentials in Streamlit secrets to enable signup.")
                    st.markdown("""
                    **How to connect Supabase:**
                    1. Go to your app dashboard on Streamlit Cloud
                    2. Click Settings → Secrets
                    3. Add:
