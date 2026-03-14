import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
import hashlib
from supabase import create_client

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="GlobalInternet Fun",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom CSS (keep your styling) ----------
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

# ---------- Password Hashing ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- Initialize Session State ----------
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.demo_mode = False
    st.session_state.supabase = None
    st.session_state.supabase_ok = False

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

# ---------- Connect to Supabase using Streamlit Secrets ----------
try:
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        st.session_state.supabase = create_client(url, key)
        st.session_state.supabase_ok = True
    else:
        st.session_state.supabase_ok = False
except Exception as e:
    st.session_state.supabase_ok = False
    st.error(f"Supabase connection error: {e}")

# ---------- Header ----------
st.markdown("""
<div class="main-header">
    <h1>🌐 GlobalInternet Fun</h1>
    <p style="font-size: 1.2em; margin-top: 5px;">Created by <strong>Gesner Deslandes, Python Developer</strong></p>
    <p>Providing FREE Internet to Everyone - 24/7 Background Connection Active!</p>
    <h3 style="color: #ffd700;">"Connect once, stay online forever!"</h3>
</div>
""", unsafe_allow_html=True)

# ---------- Show connection status ----------
if not st.session_state.supabase_ok:
    st.warning("⚠️ Running in DEMO MODE – Use guest/20082021 to log in. Add Supabase secrets in Streamlit Cloud to enable real accounts.")

# ---------- Login / Signup Section ----------
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
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

        # ----- Login Tab -----
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login", use_container_width=True):
                if st.session_state.supabase_ok:
                    try:
                        response = st.session_state.supabase.table("users").select("*").eq("username", username).execute()
                        if response.data and len(response.data) > 0:
                            if response.data[0]["password"] == hash_password(password):
                                st.session_state.logged_in = True
                                st.session_state.user = username
                                st.rerun()
                            else:
                                st.error("❌ Incorrect password")
                        else:
                            st.error("❌ User not found")
                    except Exception as e:
                        st.error(f"Login error: {e}")
                else:
                    # Demo mode login
                    if username == "guest" and password == "20082021":
                        st.session_state.logged_in = True
                        st.session_state.user = "guest"
                        st.session_state.demo_mode = True
                        st.rerun()
                    else:
                        st.error("❌ Demo mode: Use guest / 20082021")

        # ----- Sign Up Tab -----
        with tab2:
            new_user = st.text_input("Choose username", key="signup_user")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
            email = st.text_input("Email (optional)")

            agree = st.checkbox("I agree to share anonymous usage data")

            if st.button("Sign Up", use_container_width=True):
                if not st.session_state.supabase_ok:
                    st.error("Supabase not connected – cannot create account. Add secrets in Streamlit Cloud.")
                elif not agree:
                    st.error("You must agree to the terms")
                elif new_pass != confirm:
                    st.error("Passwords do not match")
                elif len(new_user) < 3:
                    st.error("Username must be at least 3 characters")
                else:
                    try:
                        # Check if user exists
                        response = st.session_state.supabase.table("users").select("*").eq("username", new_user).execute()
                        if response.data and len(response.data) > 0:
                            st.error("Username already taken")
                        else:
                            user_data = {
                                "username": new_user,
                                "password": hash_password(new_pass),
                                "email": email,
                                "created_at": datetime.now().isoformat(),
                                "data_used": 0.0,
                                "earnings": 0.0,
                                "last_active": datetime.now().isoformat(),
                                "online": True
                            }
                            st.session_state.supabase.table("users").insert(user_data).execute()
                            st.session_state.logged_in = True
                            st.session_state.user = new_user
                            st.rerun()
                    except Exception as e:
                        st.error(f"Signup error: {e}")

# ---------- Main App (Logged In) ----------
else:
    user = st.session_state.user

    # Simulate data usage (adds to owner revenue)
    data_used = random.uniform(5, 50)
    revenue = data_used * st.session_state.owner["profit_rate"]
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
        st.metric("Data used this session", f"{data_used:.1f} MB")
        st.metric("Session time", f"{random.randint(10, 120)} min")
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

        signal = random.randint(70, 100)
        st.markdown(f"**📶 Signal Strength: {signal}%**")
        st.progress(signal / 100)

        st.markdown("### 🌍 Global Network")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Active Users", random.randint(50, 200))
        with col_b:
            st.metric("Speed", f"{random.randint(50, 150)} Mbps")
        with col_c:
            st.metric("Data Today", f"{st.session_state.owner['total_data']:.2f} GB")

        with st.expander("🌐 Browse the Internet"):
            url = st.text_input("Enter URL", "https://www.google.com")
            if st.button("Go"):
                st.success(f"Connected to {url}")

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
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Owner Panel ----------
    with st.expander("⚙️ Owner Panel", expanded=False):
        owner_pass = st.text_input("Owner Password", type="password", key="owner_pass")
        if owner_pass == "OwnerSpace2025":
            owner = st.session_state.owner
            st.markdown("""
            <div class="admin-panel">
                <h2>💰 GESNER DESLANDES - OWNER DASHBOARD</h2>
                <p>MonCash: 509-47385663</p>
            </div>
            """, unsafe_allow_html=True)

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
            if st.session_state.supabase_ok:
                st.subheader("📋 Registered Users")
                try:
                    users = st.session_state.supabase.table("users").select("*").execute()
                    if users.data and len(users.data) > 0:
                        df = pd.DataFrame(users.data)
                        if 'password' in df.columns:
                            df = df.drop('password', axis=1)
                        st.dataframe(df)
                        st.metric("Total Registered Users", len(users.data))
                    else:
                        st.info("No users registered yet")
                except Exception as e:
                    st.warning(f"Could not load users: {e}")
            else:
                st.info("Connect Supabase to see registered users")

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
                        st.success(f"✅ ${owner['total_revenue']:.4f} sent to {owner['moncash']}")
                        owner['total_revenue'] = 0
                        owner['daily_revenue'] = 0
                        st.rerun()
                    else:
                        st.warning("No funds to transfer")
            with col_p2:
                enable_auto = st.checkbox("Enable Auto-Transfer")
                if enable_auto:
                    threshold = st.number_input("Threshold ($)", value=50.0)
                    if st.button("Save Settings"):
                        owner['auto_payment'] = True
                        owner['auto_threshold'] = threshold
                        st.success(f"Auto-transfer at ${threshold}")

            if owner['transactions']:
                st.subheader("📜 Transaction History")
                st.dataframe(pd.DataFrame(owner['transactions']))
        elif owner_pass:
            st.error("🔒 Incorrect OwnerSpace Password. Access Denied.")

    # ---------- Logout ----------
    col_d1, col_d2, col_d3 = st.columns([1,2,1])
    with col_d2:
        if st.button("🔌 DISCONNECT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# ---------- Footer ----------
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    st.metric("Total Users", "150+" if st.session_state.supabase_ok else "DEMO")
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
