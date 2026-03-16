"""
GLOBALINTERNET.PY - Satellite Communication Platform with Real Money Transfers
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Version: 34.0.0 (Real MonCash Integration)

===============================================================================
REQUIRED SETUP FOR REAL MONEY TRANSFERS:
===============================================================================

1. Register for MonCash Business: https://moncash.digicelgroup.com/business
2. Get your Client ID and Client Secret from MonCash dashboard
3. Set up a backend API service (Flask/FastAPI) with these endpoints:
   - POST /api/initiate-payment - Creates payment and returns redirect URL
   - POST /api/webhook/moncash - Receives payment notifications
   - GET /api/balance - Checks your MonCash business balance
   - POST /api/transfer - Initiates P2P transfer

4. Add these to your Streamlit secrets:
   - BACKEND_API_URL (your backend service URL)
   - BACKEND_API_KEY (shared secret for authentication)
   - MONCASH_CLIENT_ID
   - MONCASH_CLIENT_SECRET
   - MONCASH_MODE (sandbox or live)

===============================================================================
"""
import streamlit as st

st.set_page_config(page_title="GLOBALINTERNET.PY", page_icon="🇭🇹", layout="wide")

import pandas as pd
import numpy as np
import time
import socket
import hashlib
from datetime import datetime
import requests
from supabase import create_client, Client
import io
from PIL import Image
import mimetypes
import urllib.parse
import json
import os
import tempfile
import random
import string
import traceback
import hmac

# --- Configuration for Real Payments ---
BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "https://your-backend.com")
BACKEND_API_KEY = st.secrets.get("BACKEND_API_KEY", "")
MONCASH_MODE = st.secrets.get("MONCASH_MODE", "sandbox")  # Change to "live" for production

# --- Supabase client (unchanged) ---
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

# --- Schema detection (unchanged) ---
@st.cache_resource
def check_media_urls_column():
    if supabase is None:
        return False
    try:
        supabase.table("posts").select("media_urls").limit(0).execute()
        return True
    except Exception as e:
        if "column posts.media_urls does not exist" in str(e):
            return False
        else:
            st.warning(f"Unexpected schema check error: {e}")
            return False

MEDIA_URLS_EXISTS = check_media_urls_column()
if not MEDIA_URLS_EXISTS:
    st.warning("⚠️ The 'media_urls' column is missing from the 'posts' table. "
               "Media uploads will be disabled. Please run the SQL setup script to enable them.")

@st.cache_resource
def check_post_media_bucket():
    if supabase is None:
        return False
    try:
        supabase.storage.from_("post_media").list()
        return True
    except Exception as e:
        st.error(f"❌ 'post_media' bucket check failed: {e}")
        return False

POST_MEDIA_BUCKET_OK = check_post_media_bucket() if MEDIA_URLS_EXISTS else False

@st.cache_resource
def check_reactions_table():
    if supabase is None:
        return False
    try:
        supabase.table("reactions").select("id").limit(0).execute()
        return True
    except Exception as e:
        if "relation" in str(e) and "does not exist" in str(e):
            return False
        else:
            return True

REACTIONS_TABLE_EXISTS = check_reactions_table()
if not REACTIONS_TABLE_EXISTS:
    st.warning("⚠️ 'reactions' table is missing. Reactions will be disabled. Please run the SQL setup script.")

@st.cache_resource
def check_share_function():
    if supabase is None:
        return False
    try:
        supabase.rpc("increment_shares", {"post_id": 1}).execute()
        return True
    except Exception as e:
        if "function" in str(e) and "does not exist" in str(e):
            return False
        else:
            return True

SHARE_FUNCTION_EXISTS = check_share_function()
if not SHARE_FUNCTION_EXISTS:
    st.warning("⚠️ 'increment_shares' function is missing. Sharing posts will fail. Please run the SQL setup script.")

# --- Secrets for owner only ---
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")
MONCASH_NUM = st.secrets.get("MONCASH_NUM", "(509)-47385663")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

# --- New: Real payment tracking in session state ---
if "real_balance" not in st.session_state:
    st.session_state.real_balance = 0.0
if "pending_transactions" not in st.session_state:
    st.session_state.pending_transactions = []
if "last_balance_check" not in st.session_state:
    st.session_state.last_balance_check = None

# --- New: Payment processing functions ---
def get_real_balance():
    """
    Fetch real MonCash business balance from backend API.
    Returns tuple (success: bool, balance: float, message: str)
    """
    if not BACKEND_API_URL:
        return False, 0.0, "Backend API not configured"
    
    try:
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{BACKEND_API_URL}/api/balance",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, float(data.get("balance", 0)), "Success"
        else:
            return False, 0.0, f"API Error: {response.status_code}"
    except Exception as e:
        return False, 0.0, str(e)

def initiate_withdrawal(amount, method, phone_number=None, bank_details=None):
    """
    Initiate a real money transfer to MonCash or bank account.
    Returns tuple (success: bool, transaction_id: str, message: str)
    """
    if not BACKEND_API_URL:
        return False, "", "Backend API not configured"
    
    try:
        headers = {
            "X-API-Key": BACKEND_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "amount": amount,
            "method": method.lower(),
            "owner_cin": OWNER_CIN
        }
        
        if method == "MonCash" and phone_number:
            payload["recipient_phone"] = phone_number
        elif method == "Bank Transfer" and bank_details:
            payload["bank_details"] = bank_details
        
        response = requests.post(
            f"{BACKEND_API_URL}/api/transfer",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get("transaction_id", ""), data.get("message", "Transfer initiated")
        else:
            return False, "", f"API Error: {response.status_code}"
    except Exception as e:
        return False, "", str(e)

def verify_transaction(transaction_id):
    """
    Verify the status of a transaction.
    Returns tuple (success: bool, status: str, details: dict)
    """
    if not BACKEND_API_URL:
        return False, "error", {}
    
    try:
        headers = {"X-API-Key": BACKEND_API_KEY}
        response = requests.get(
            f"{BACKEND_API_URL}/api/transaction/{transaction_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get("status", "unknown"), data
        else:
            return False, "error", {}
    except Exception as e:
        return False, "error", {"error": str(e)}

# --- Cookie helpers (unchanged) ---
def set_cookie(name, value, days=30):
    js = f"""
    <script>
    function setCookie(name, value, days) {{
        var expires = "";
        if (days) {{
            var date = new Date();
            date.setTime(date.getTime() + (days*24*60*60*1000));
            expires = "; expires=" + date.toUTCString();
        }}
        document.cookie = name + "=" + (value || "")  + expires + "; path=/";
    }}
    setCookie("{name}", "{value}", {days});
    </script>
    """
    st.components.v1.html(js, height=0)

def get_cookie(name):
    cookie_val = None
    try:
        params = st.query_params
        if f"cookie_{name}" in params:
            cookie_val = params[f"cookie_{name}"][0]
    except:
        try:
            params = st.experimental_get_query_params()
            if f"cookie_{name}" in params:
                cookie_val = params[f"cookie_{name}"][0]
        except:
            pass
    return cookie_val

def inject_cookie_reader():
    js = """
    <script>
    function getCookie(name) {
        var nameEQ = name + "=";
        var ca = document.cookie.split(';');
        for(var i=0;i < ca.length;i++) {
            var c = ca[i];
            while (c.charAt(0)==' ') c = c.substring(1,c.length);
            if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
        }
        return null;
    }
    var refreshToken = getCookie("sb_refresh_token");
    if (refreshToken) {
        var url = new URL(window.location.href);
        url.searchParams.set('cookie_sb_refresh_token', refreshToken);
        window.history.replaceState({}, '', url);
    }
    </script>
    """
    st.components.v1.html(js, height=0)

# --- Session state (add payment tracking) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "data_comp" not in st.session_state:
    st.session_state.data_comp = 0.0
if "connection_time" not in st.session_state:
    st.session_state.connection_time = time.time()
if "posts" not in st.session_state:
    st.session_state.posts = []
if "owner_space_access" not in st.session_state:
    st.session_state.owner_space_access = False
if "phone_otp_sent" not in st.session_state:
    st.session_state.phone_otp_sent = False
if "temp_phone" not in st.session_state:
    st.session_state.temp_phone = ""
if "viewing_live" not in st.session_state:
    st.session_state.viewing_live = None
if "live_sessions" not in st.session_state:
    st.session_state.live_sessions = []
if "reset_email_sent" not in st.session_state:
    st.session_state.reset_email_sent = False
if "stream_key" not in st.session_state:
    st.session_state.stream_key = None
if "selected_platform" not in st.session_state:
    st.session_state.selected_platform = None
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "real_balance" not in st.session_state:
    st.session_state.real_balance = 0.0
if "pending_transactions" not in st.session_state:
    st.session_state.pending_transactions = []
if "last_balance_check" not in st.session_state:
    st.session_state.last_balance_check = None
if "withdrawal_in_progress" not in st.session_state:
    st.session_state.withdrawal_in_progress = False
if "current_transaction" not in st.session_state:
    st.session_state.current_transaction = None

# --- Restore session from cookie (unchanged) ---
if not st.session_state.logged_in and supabase:
    inject_cookie_reader()
    refresh_token = get_cookie("sb_refresh_token")
    if refresh_token:
        try:
            user = supabase.auth.get_user(refresh_token)
            if user.user:
                st.session_state.logged_in = True
                st.session_state.user = user.user
                profile = get_or_create_profile(user.user.id, user.user.email or user.user.phone)
                st.session_state.profile = profile
                st.session_state.connection_time = time.time()
                st.session_state.posts = load_posts()
                st.session_state.live_sessions = load_live_sessions()
        except Exception as e:
            st.session_state.last_error = str(e)

# --- UI styling (with zoom adjustment) ---
st.markdown("""
    <style>
    html {
        font-size: 14px;
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #f0f4fa 0%, #d9e2ef 100%);
        color: #1e2a3a;
    }
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,168,255,0.3);
    }
    .haiti-symbol {
        font-size: 4rem;
        text-align: center;
        background: linear-gradient(135deg, #00209F 0%, #00209F 50%, #D21034 50%, #D21034 100%);
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
    }
    .post-card {
        background: rgba(255,255,255,0.7);
        backdrop-filter: blur(8px);
        padding: 20px 25px;
        border-radius: 20px;
        border: 1px solid rgba(0,168,255,0.2);
        margin: 15px 0;
        color: #1e2a3a;
        transition: transform 0.2s;
    }
    .post-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 25px rgba(0,0,0,0.1);
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
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(105deg, #0080ff 0%, #0066cc 100%);
        box-shadow: 0 12px 24px rgba(0,128,255,0.3);
        transform: scale(1.02);
    }
    .live-badge {
        background-color: #ff4444;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 8px;
    }
    .green-dot {
        height: 12px;
        width: 12px;
        background-color: #00ff88;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }
    .private-badge {
        background-color: #ffaa00;
        color: #1e2a3a;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 8px;
    }
    .comment-indent {
        margin-left: 2rem;
        border-left: 2px solid #ddd;
        padding-left: 1rem;
    }
    .comment-meta {
        font-size: 0.8rem;
        color: #666;
    }
    .delete-confirm {
        background-color: #ffdddd;
        border-left: 3px solid red;
        padding: 10px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #ffdddd;
        border-left: 6px solid #ff4444;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        font-family: monospace;
        white-space: pre-wrap;
    }
    .transaction-success {
        background-color: #ddffdd;
        border-left: 6px solid #44ff44;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .transaction-pending {
        background-color: #ffffdd;
        border-left: 6px solid #ffaa00;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper functions (unchanged from previous version, load_posts, create_post, etc.) ---
# [All your existing helper functions remain exactly the same - get_or_create_profile, 
#  update_profile, upload_avatar, upload_post_media, delete_post, load_posts, 
#  create_post, toggle_reaction, share_post, add_comment, load_comments, 
#  delete_comment, like_comment, create_live_session, etc.]

# ... (keep all your existing helper functions unchanged) ...

# --- Updated Owner Space with Real Money Transfers ---
def owner_space():
    st.header("🕊️ Owner Space (Private)")
    
    if not st.session_state.owner_space_access:
        with st.form("owner_space_login"):
            pwd = st.text_input("Enter Owner Space Password", type="password")
            if st.form_submit_button("Access"):
                if pwd == OWNSPACE_PASSWORD:
                    st.session_state.owner_space_access = True
                    # Initialize real balance on first access
                    if st.session_state.last_balance_check is None:
                        with st.spinner("Checking MonCash balance..."):
                            success, balance, msg = get_real_balance()
                            if success:
                                st.session_state.real_balance = balance
                                st.session_state.last_balance_check = datetime.now()
                            else:
                                st.warning(f"Could not fetch real balance: {msg}")
                    st.rerun()
                else:
                    st.error("Invalid password")
        return

    # --- Real balance display with refresh button ---
    col_balance, col_refresh = st.columns([3, 1])
    with col_balance:
        # Format balance with commas for thousands
        balance_str = f"${st.session_state.real_balance:,.2f}"
        st.metric("MonCash Business Balance", balance_str, delta=None)
        
        if st.session_state.last_balance_check:
            st.caption(f"Last updated: {st.session_state.last_balance_check.strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col_refresh:
        if st.button("🔄 Refresh Balance", use_container_width=True):
            with st.spinner("Fetching latest balance..."):
                success, balance, msg = get_real_balance()
                if success:
                    st.session_state.real_balance = balance
                    st.session_state.last_balance_check = datetime.now()
                    st.success("Balance updated!")
                else:
                    st.error(f"Failed to refresh: {msg}")
            st.rerun()
    
    st.divider()
    
    # --- Compensation display (from app usage) ---
    duration = time.time() - st.session_state.connection_time
    simulated_comp = duration * 0.035  # This is separate from real balance
    st.subheader("📊 App Usage Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Simulated Compensation", f"${simulated_comp:.4f}")
    with col2:
        st.metric("Uptime", get_uptime())
    with col3:
        st.metric("Network Users", np.random.randint(100, 500))
    
    st.divider()
    
    # --- Real Withdrawal Section ---
    st.subheader("💰 Withdraw Funds to Your Accounts")
    st.markdown(f"**Your MonCash Business Number:** `{MONCASH_NUM}`")
    st.markdown(f"**Your CIN:** `{OWNER_CIN}`")
    
    # Check if backend is configured
    if not BACKEND_API_URL:
        st.error("⚠️ Backend API not configured. Please set BACKEND_API_URL in secrets.")
        st.info("To enable real transfers, you need to set up a backend service that handles MonCash API calls.")
        if st.button("View Backend Setup Guide"):
            st.markdown("""
            ### Backend Setup Requirements
            1. Create a Flask/FastAPI application
            2. Install dependencies: `pip install requests python-dotenv`
            3. Implement MonCash OAuth2 flow
            4. Add endpoints for balance, transfer, and webhooks
            5. Deploy to a secure server with HTTPS
            6. Add your backend URL to Streamlit secrets
            """)
        return
    
    # Withdrawal form
    with st.form("real_withdrawal_form"):
        st.markdown("### Transfer to Your Account")
        
        method = st.selectbox(
            "Transfer Method",
            ["MonCash", "Bank Transfer"],
            help="Choose how you want to receive the funds"
        )
        
        amount = st.number_input(
            "Amount ($)",
            min_value=1.0,
            max_value=float(st.session_state.real_balance),
            value=min(10.0, float(st.session_state.real_balance)),
            step=10.0,
            format="%.2f"
        )
        
        # Conditional fields based on method
        phone_number = None
        bank_details = None
        
        if method == "MonCash":
            phone_number = st.text_input(
                "Your MonCash Phone Number",
                value=M
