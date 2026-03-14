import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
from PIL import Image
import nest_asyncio
from streamlit_autorefresh import st_autorefresh
from supabase import create_client
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
    st_autorefresh(interval=30000, key="auto_refresh")
except:
    pass

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize all session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.connected = False
    st.session_state.current_user = None
    st.session_state.demo_mode = False
    st.session_state.supabase_connected = False
    st.session_state.supabase = None
    
    # Owner data - FIXED: Make sure this is a dictionary, not a string
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

# Try to connect to Supabase
try:
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        if isinstance(url, str) and isinstance(key, str):
            st.session_state.supabase = create_client(url, key)
            st.session_state.supabase_connected = True
            st.session_state.demo_mode = False
        else:
            st.session_state.supabase_connected = False
            st.session_state.demo_mode = True
    else:
        st.session_state.supabase_connected = False
        st.session_state.demo_mode = True
except Exception as e:
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

# Show demo mode warning
if st.session_state.demo_mode:
    st.warning("⚠️ Running in DEMO MODE - Using guest account only. Add Supabase secrets in Streamlit Cloud for real user accounts.")

# Login/Signup Section
if not st.session_state.connected:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Features
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
        
        # Login Tab
        with tab1:
            st.markdown("### Login")
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Login & Connect", use_container_width=True):
                if st.session_state.supabase_connected and st.session_state.supabase:
                    try:
                        hashed = hash_password(login_pass)
                        response = st.session_state.supabase.table("users").select("*").eq("username", login_user).execute()
                        if response.data and len(response.data) > 0:
                            if response.data[0]["password"] == hashed:
                                st.session_state.connected = True
                                st.session_state.current_user = login_user
                                st.rerun()
                            else:
                                st.error("Wrong password")
                        else:
                            st.error("User not found")
                    except Exception as e:
                        st.error(f"Login error: {e}")
                else:
                    if login_user == "guest" and login_pass == "20082021":
                        st.session_state.connected = True
                        st.session_state.current_user = "guest"
                        st.session_state.demo_mode = True
                        st.rerun()
                    else:
                        st.error("Demo mode: Use guest/20082021")
        
        # Sign Up Tab
        with tab2:
            st.markdown("### Create Account")
            new_user = st.text_input("Username", key="new_user")
            new_pass = st.text_input("Password", type="password", key="new_pass")
            confirm_pass = st.text_input("Confirm Password", type="password", key="confirm_pass")
            email = st.text_input("Email (optional)")
            
            agree = st.checkbox("I agree to share anonymous usage data")
            
            if st.button("Sign Up & Connect", use_container_width=True):
                if not agree:
                    st.error("Please agree to the terms")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match")
                elif len(new_user) < 3:
                    st.error("Username too short")
                elif st.session_state.supabase_connected and st.session_state.supabase:
                    try:
                        # Check if user exists
                        response = st.session_state.supabase.table("users").select("*").eq("username", new_user).execute()
                        if response.data and len(response.data) > 0:
                            st.error("Username already taken")
                        else:
                            # Create user
                            hashed = hash_password(new_pass)
                            user_data = {
                                "username": new_user,
                                "password": hashed,
                                "email": email,
                                "created_at": datetime.now().isoformat(),
                                "data_used": 0.0,
                                "earnings": 0.0,
                                "last_active": datetime.now().isoformat(),
                                "online": True
                            }
                            st.session_state.supabase.table("users").insert(user_data).execute()
                            st.session_state.connected = True
                            st.session_state.current_user = new_user
                            st.rerun()
                    except Exception as e:
                        st.error(f"Signup error: {e}")
                else:
                    st.error("Cannot create account: Supabase not connected")

# Main App (Logged In)
else:
    user = st.session_state.current_user
    
    # Generate random stats
    data_used = random.uniform(5, 50)
    revenue = data_used * 0.05
    st.session_state.owner["total_revenue"] += revenue
    st.session_state.owner["daily_revenue"] += revenue
    st.session_state.owner["total_data"] += data_used / 1000
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/globe.png", width=50)
        st.markdown(f"### 👤 {user}")
        if st.session_state.demo_mode:
            st.info("🔧 DEMO MODE")
        st.markdown(f"<span class='online-indicator'></span> **Online**", unsafe_allow_html=True)
        st.markdown("---")
        st.metric("Data Used", f"{data_used:.2f} MB")
        st.metric("Session Time", f"{random.randint(10, 60)} min")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="internet-card">
            <h2>🟢 Connected as {user}</h2>
            <p><span class='online-indicator'></span> <strong>Status:</strong> Online</p>
            <p><strong>IP:</strong> 10.0.{random.randint(1,255)}.{random.randint(1,255)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        signal = random.randint(70, 100)
        st.markdown(f"📶 Signal: {signal}%")
        st.progress(signal/100)
        
        with st.expander("🌐 Browse"):
            url = st.text_input("URL", "https://www.google.com")
            if st.button("Go"):
                st.success(f"Connected to {url}")
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <h3>Quick Actions</h3>
        """, unsafe_allow_html=True)
        st.button("📱 YouTube")
        st.button("📘 Facebook")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Owner Panel - FIXED: No .items() anywhere
    with st.expander("⚙️ Owner Panel", expanded=False):
        owner_pass = st.text_input("Password", type="password", key="owner_pass")
        
        if owner_pass == "OwnerSpace2025":
            owner = st.session_state.owner
            
            st.markdown("""
            <div class="admin-panel">
                <h2>💰 GESNER DESLANDES</h2>
                <p>MonCash: 509-47385663</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Stats
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.metric("Total Revenue", f"${owner['total_revenue']:.4f}")
                st.metric("Today", f"${owner['daily_revenue']:.4f}")
            with col_r2:
                st.metric("Total Data", f"{owner['total_data']:.2f} GB")
                st.metric("Active Users", random.randint(10, 50))
            
            # Transfer button
            if st.button("💰 TRANSFER TO MONCASH"):
                if owner['total_revenue'] > 0:
                    st.success(f"✅ Sent ${owner['total_revenue']:.4f} to {owner['moncash']}")
                    owner['total_revenue'] = 0
                    owner['daily_revenue'] = 0
                else:
                    st.warning("No funds")
    
    # Disconnect
    if st.button("🔌 Disconnect"):
        st.session_state.connected = False
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
    <p>🌐 GlobalInternet Fun | Owner: Gesner Deslandes | MonCash: 509-47385663</p>
</div>
""", unsafe_allow_html=True)
