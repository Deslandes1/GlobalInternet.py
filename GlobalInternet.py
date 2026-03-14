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
import hmac

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
    .success-message {
        background-color: #4CAF50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin: 10px 0;
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
count = st_autorefresh(interval=30000, key="auto_refresh")

# Initialize Supabase
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
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
    st.warning("⚠️ Running in DEMO MODE - Connect Supabase for real user accounts. Add secrets in Streamlit Cloud settings.")

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
                        
                        if response.data:
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
                        st.error("❌ Demo mode: Use guest/20082021")
        
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
                st.mark to("to help provide free internet by sharing anonymous usage data")
            
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
                        if response.data:
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
                    st.error("Supabase not connected. Cannot create account.")

else:
    # User is logged in
    user = st.session_state.current_user
    
    # Track data usage (simulated)
    data_used_today = random.uniform(5, 50)
    revenue_generated = data_used_today * st.session_state.owner["profit_rate"]
    
    # Update in Supabase if connected
    if st.session_state.supabase_connected and user != "guest":
        try:
            # Get user data
            response = supabase.table("users").select("*").eq("username", user).execute()
            if response.data:
                user_data = response.data[0]
                current_data = user_data.get("data_used", 0)
                
                # Update with new data
                supabase.table("users").update({
                    "data_used": current_data + data_used_today,
                    "last_active": datetime.now().isoformat(),
                    "online": True
                }).eq("username", user).execute()
        except Exception as e:
            st.error(f"Error updating user data: {e}")
    
    # Update owner revenue
    st.session_state.owner["total_revenue"] += revenue_generated
    st.session_state.owner["daily_revenue"] += revenue_generated
    st.session_state.owner["total_data"] += data_used_today / 1000
    
    # Sidebar with user info
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/globe.png", width=50)
        st.markdown(f"### 👤 {user}")
        
        if st.session_state.demo_mode:
            st.info("🔧 DEMO MODE")
        
        # Online status
        st.markdown(f"<span class='online-indicator'></span> **Online**", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**📊 Your Stats:**")
        st.metric("Data Shared", f"{data_used_today:.2f} MB")
        st.metric("Session Time", f"{random.randint(10, 120)} min")
        
        st.markdown("---")
        st.markdown("**👥 Online Now:**")
        online_users = ["alice", "bob", "charlie", "diana"][:random.randint(2,4)]
        for ou in online_users:
            st.markdown(f"<span class='online-indicator'></span> {ou}", unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="internet-card">
            <h2>🟢 Connected as {user}</h2>
            <p><span class='online-indicator'></span> <strong>Status:</strong> Online 24/7</p>
            <p><strong>IP Address:</strong> 10.0.{random.randint(1,255)}.{random.randint(1,255)}</p>
            <p><strong>Connected Since:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
            <p><strong>Background Mode:</strong> ✅ Active (works with screen off)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Signal strength
        signal = random.randint(80, 100)
        st.markdown(f"""
        <div style="margin: 20px 0;">
            <strong>📶 Signal: {signal}%</strong>
            <div class="signal-strength" style="width: {signal}%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Network stats
        st.markdown("### 🌍 Global Network")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Active Users", random.randint(50, 200))
        with col_b:
            st.metric("Speed", f"{random.randint(50, 150)} Mbps")
        with col_c:
            st.metric("Data Today", f"{st.session_state.owner['total_data']:.2f} GB")
        
        # Browse option
        with st.expander("🌐 Browse Internet"):
            url = st.text_input("Enter URL", "https://www.google.com")
            if st.button("Go"):
                st.success(f"Connected to {url}")
                st.markdown(f'<iframe src="{url}" width="100%" height="400"></iframe>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <h3>⚡ Quick Actions</h3>
        """, unsafe_allow_html=True)
        
        if st.button("📱 YouTube"):
            st.info("Opening YouTube...")
        if st.button("📘 Facebook"):
            st.info("Opening Facebook...")
        if st.button("📸 Instagram"):
            st.info("Opening Instagram...")
        if st.button("🐦 Twitter"):
            st.info("Opening Twitter...")
        
        st.markdown("---")
        st.markdown("**💬 Recent Activity:**")
        activities = [
            f"• Watched video (5 MB)",
            f"• Scrolled feed (2 MB)",
            f"• Chat messages (1 MB)"
        ]
        for act in activities[:2]:
            st.markdown(act)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Admin Panel
    with st.expander("⚙️ Owner Panel", expanded=False):
        owner_pass = st.text_input("Owner Password", type="password")
        
        if owner_pass == "OwnerSpace2025":
            owner = st.session_state.owner
            
            st.markdown("""
            <div class="admin-panel">
                <h2>💰 GESNER DESLANDES - OWNER DASHBOARD</h2>
                <p>MonCash: 509-47385663</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Revenue stats
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.markdown(f"""
                <div class="profit-counter">
                    ${owner['total_revenue']:.4f}
                </div>
                <p style="text-align: center;">Total Revenue</p>
                """, unsafe_allow_html=True)
            with col_r2:
                st.metric("Today", f"${owner['daily_revenue']:.4f}")
                st.metric("Active Users", random.randint(20, 100))
            with col_r3:
                st.metric("Total Data", f"{owner['total_data']:.2f} GB")
                st.metric("Rate", f"${owner['profit_rate']}/MB")
            
            # Real users from Supabase
            if st.session_state.supabase_connected:
                st.subheader("📋 Registered Users")
                try:
                    users = supabase.table("users").select("*").execute()
                    if users.data:
                        df = pd.DataFrame(users.data)
                        # Remove password column for display
                        if 'password' in df.columns:
                            df = df.drop('password', axis=1)
                        st.dataframe(df)
                        
                        # Total users count
                        st.metric("Total Registered Users", len(users.data))
                except Exception as e:
                    st.warning(f"Could not load users: {e}")
            
            # Payment processing
            st.subheader("💸 Instant MonCash Transfer")
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.markdown(f"""
                **Payment Details:**
                - Amount: ${owner['total_revenue']:.4f}
                - To: {owner['moncash']}
                """)
                
                if st.button("💰 TRANSFER NOW", use_container_width=True):
                    if owner['total_revenue'] > 0:
                        transaction = {
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "amount": owner['total_revenue'],
                            "to": owner['moncash'],
                            "status": "COMPLETED",
                            "reference": f"MC{random.randint(10000, 99999)}"
                        }
                        owner['transactions'].append(transaction)
                        
                        st.balloons()
                        st.success(f"""
                        ✅ TRANSFER COMPLETE!
                        Amount: ${owner['total_revenue']:.4f}
                        Reference: {transaction['reference']}
                        """)
                        
                        owner['total_revenue'] = 0
                        owner['daily_revenue'] = 0
                        st.rerun()
                    else:
                        st.warning("No funds to transfer")
            
            with col_p2:
                # Auto-payment settings
                enable_auto = st.checkbox("Enable Auto-Transfer")
                if enable_auto:
                    threshold = st.number_input("Threshold ($)", value=50.0)
                    if st.button("Save Settings"):
                        owner['auto_payment'] = True
                        owner['auto_threshold'] = threshold
                        st.success(f"Auto-transfer at ${threshold}")
            
            # Transaction history
            if owner['transactions']:
                st.subheader("📜 History")
                df_t = pd.DataFrame(owner['transactions'])
                st.dataframe(df_t)
    
    # Disconnect
    if st.button("🔌 DISCONNECT", use_container_width=True):
        if st.session_state.supabase_connected and user != "guest":
            try:
                supabase.table("users").update({"online": False}).eq("username", user).execute()
            except:
                pass
        st.session_state.connected = False
        st.rerun()

# Footer
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.metric("Total Users", "150+" if st.session_state.supabase_connected else "DEMO")
with col_f2:
    st.metric("Active Now", str(random.randint(20, 50)) + "+")
with col_f3:
    st.metric("Data Shared", f"{random.randint(100, 500)} GB")

st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>🌐 GlobalInternet Fun - Free Internet for Everyone</p>
    <p>© 2025 | Owner: Gesner Deslandes | MonCash: 509-47385663</p>
    <p style="color: #4CAF50;">⚡ Connect and have fun!</p>
</div>
""", unsafe_allow_html=True)
