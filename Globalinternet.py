"""
Home Sweet Home - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 76.5.0 (App renamed, light blue/red theme, global password from secrets)
"""
import streamlit as st
import smtplib
from email.message import EmailMessage
import pandas as pd
import numpy as np
import time
import socket
import hashlib
from datetime import datetime, timedelta
import requests
from supabase import create_client, Client
import io
from PIL import Image
import urllib.parse
import json
import os
import random
import string
import traceback
import re
import base64

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Home Sweet Home", page_icon="🏠", layout="wide")

# ====== GLOBAL APP PASSWORD PROTECTION (from secrets) ======
APP_PASSWORD = st.secrets.get("APP_PASSWORD")  # Set this in your secrets to enable

if APP_PASSWORD:
    if "app_authenticated" not in st.session_state:
        st.session_state.app_authenticated = False

    if not st.session_state.app_authenticated:
        st.markdown(
            """
            <style>
                .stApp { background: linear-gradient(145deg, #E3F2FD, #FFCDD2); }
                .login-box { max-width: 400px; margin: 100px auto; padding: 30px; background: rgba(255,255,255,0.7); border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); text-align: center; }
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.image("https://github.com/Deslandes1/Let-s-Learn-Mathematics-with-Gesner/blob/main/Gesner%20Deslandes.png?raw=true", width=100)
            st.markdown("### 🔐 Home Sweet Home")
            st.markdown("Enter the app password to continue.")
            with st.form("app_password_form"):
                pwd = st.text_input("Password", type="password", placeholder="Enter app password")
                if st.form_submit_button("🔓 Unlock"):
                    if pwd == APP_PASSWORD:
                        st.session_state.app_authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Invalid password")
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

# ====== KEEP‑ALIVE PING HANDLER ======
try:
    query_params = st.query_params
    if "ping" in query_params and query_params["ping"] == "1":
        st.markdown("OK")
        st.stop()
except AttributeError:
    pass

# --- Supabase client ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.warning("⚠️ Supabase credentials not found.")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {e}")
        return None

supabase = init_supabase()

# --- Secrets for owner only ---
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")
MONCASH_NUM = st.secrets.get("MONCASH_NUM", "(509)-47385663")
UNIBANK_ACCOUNT = st.secrets.get("UNIBANK_ACCOUNT", "105-2016-16594727")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

# Optional backend settings
BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "https://your-backend.com")
BACKEND_API_KEY = st.secrets.get("BACKEND_API_KEY", "")
MONCASH_MODE = st.secrets.get("MONCASH_MODE", "live")
MONCASH_API_KEY = st.secrets.get("MONCASH_API_KEY", "")
MONCASH_API_SECRET = st.secrets.get("MONCASH_API_SECRET", "")
EXCHANGE_RATE_API = st.secrets.get("EXCHANGE_RATE_API", "https://api.exchangerate-api.com/v4/latest/USD")

# Optional email settings
SMTP_SERVER = st.secrets.get("SMTP_SERVER")
SMTP_PORT = st.secrets.get("SMTP_PORT")
SMTP_USERNAME = st.secrets.get("SMTP_USERNAME")
SMTP_PASSWORD = st.secrets.get("SMTP_PASSWORD")
EMAIL_FROM = st.secrets.get("EMAIL_FROM")
EMAIL_TO = st.secrets.get("EMAIL_TO")

# --- Session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
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
if "replying_to" not in st.session_state:
    st.session_state.replying_to = {}
# --- Friend/Chat state ---
if "notifications" not in st.session_state:
    st.session_state.notifications = []
if "unread_count" not in st.session_state:
    st.session_state.unread_count = 0
if "friend_requests" not in st.session_state:
    st.session_state.friend_requests = []
if "friends" not in st.session_state:
    st.session_state.friends = []
if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None
if "call_room" not in st.session_state:
    st.session_state.call_room = None
if "in_call" not in st.session_state:
    st.session_state.in_call = False
if "viewing_profile" not in st.session_state:
    st.session_state.viewing_profile = None
# --- Live gifts state ---
if "live_gifts" not in st.session_state:
    st.session_state.live_gifts = []
if "exchange_rate" not in st.session_state:
    st.session_state.exchange_rate = 100  # default 1 USD = 100 HTG (fallback)
# --- Background state ---
if "background_url" not in st.session_state:
    st.session_state.background_url = None
# --- Language state ---
if "language" not in st.session_state:
    st.session_state.language = "en"
# --- Edit post state ---
if "editing_post" not in st.session_state:
    st.session_state.editing_post = None

# --- Language dictionary (unchanged, but we'll keep it as is) ---
LANG = {
    # ... (ALL LANGUAGE DICTIONARIES REMAIN THE SAME, just replace "GLOBALINTERNET.PY" with "Home Sweet Home" in the app title and footer strings)
    # To save space in this response, I'm omitting the full dict here but in the actual file you keep it exactly as provided.
    # I'll add the changes in the relevant places below.
}

def t(key):
    """Translate a key using the current language."""
    return LANG.get(st.session_state.language, LANG["en"]).get(key, key)

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

# --- Token refresh function (unchanged) ---
def refresh_supabase_session():
    if supabase is None or not st.session_state.refresh_token:
        return False
    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        if new_session and new_session.user:
            st.session_state.user = new_session.user
            st.session_state.refresh_token = new_session.session.refresh_token
            profile = get_or_create_profile(new_session.user.id, new_session.user.email or new_session.user.phone)
            st.session_state.profile = profile
            return True
        else:
            return False
    except Exception as e:
        st.session_state.last_error = f"Token refresh failed: {e}"
        return False

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
                st.session_state.refresh_token = refresh_token
                profile = get_or_create_profile(user.user.id, user.user.email or user.user.phone)
                st.session_state.profile = profile
                st.session_state.connection_time = time.time()
                st.session_state.posts = load_posts()
                st.session_state.live_sessions = load_live_sessions()
                load_friend_data()
                st.session_state.notifications = load_notifications(user.user.id)
                st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
        except Exception as e:
            st.session_state.last_error = str(e)

# --- Token refresh on each run (unchanged) ---
if st.session_state.logged_in and supabase and st.session_state.refresh_token:
    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        if new_session and new_session.user:
            st.session_state.user = new_session.user
            st.session_state.refresh_token = new_session.session.refresh_token
    except Exception:
        pass

# ====== UI STYLING (UPDATED: light blue & red gradient) ======
st.markdown("""
    <style>
    .stApp [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #E3F2FD 0%, #FFCDD2 100%);
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
        padding: 8px 20px;
        font-weight: 600;
        box-shadow: 0 8px 16px rgba(0,128,255,0.2);
        transition: all 0.2s;
        font-size: 0.9rem;
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
        margin-bottom: 10px;
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
    video {
        max-width: 100%;
        max-height: 60vh;
        width: auto;
        height: auto;
        object-fit: contain;
        border-radius: 12px;
    }
    img {
        max-width: 100%;
        max-height: 60vh;
        width: auto;
        height: auto;
        object-fit: contain;
        border-radius: 12px;
    }
    .comment-section {
        margin-top: 20px;
        background: rgba(255,255,255,0.5);
        padding: 15px;
        border-radius: 16px;
    }
    .friend-count {
        font-size: 1.2rem;
        font-weight: bold;
        color: #0a2a44;
    }
    .gift-button {
        background: linear-gradient(145deg, #ffd700, #ffa500);
        color: #000;
        font-weight: bold;
        border: none;
        border-radius: 30px;
        padding: 5px 15px;
        margin: 5px;
        cursor: pointer;
    }
    .gift-button:hover {
        background: linear-gradient(145deg, #ffa500, #ff8c00);
    }
    /* Mobile adjustments */
    @media (max-width: 768px) {
        .stButton > button {
            padding: 6px 12px;
            font-size: 0.8rem;
        }
        .post-card {
            padding: 12px 15px;
        }
        .stMetric {
            padding: 12px;
        }
        .haiti-symbol {
            font-size: 3rem;
        }
        .owner-name {
            font-size: 1.2rem;
        }
        .collaborators {
            font-size: 0.8rem;
            padding: 6px 10px;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: unset !important;
        }
        .row-widget.stRadio > div {
            flex-direction: column;
        }
    }
    /* Login page fixes */
    .stTextInput > div > div > input {
        color: #1e2a3a !important;
        background-color: rgba(255,255,255,0.9) !important;
        border: 1px solid rgba(0,168,255,0.3) !important;
        border-radius: 40px !important;
        padding: 10px 20px !important;
    }
    .stTextArea > div > textarea {
        color: #1e2a3a !important;
        background-color: rgba(255,255,255,0.9) !important;
        border: 1px solid rgba(0,168,255,0.3) !important;
        border-radius: 20px !important;
    }
    .stRadio > div {
        color: #1e2a3a !important;
    }
    .stRadio label {
        color: #1e2a3a !important;
    }
    .stTabs [data-baseweb="tab-list"] button {
        color: #1e2a3a !important;
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #0080ff !important;
        font-weight: bold;
    }
    h1, h2, h3 {
        color: #0a2a44 !important;
    }
    .stAlert {
        background-color: rgba(255,255,255,0.7) !important;
        color: #1e2a3a !important;
    }
    a {
        color: #0080ff !important;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    /* New: Home Sweet Home themed header */
    .home-title {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #BBDEFB, #FFCDD2);
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .home-title h1 {
        margin: 0;
        font-size: 2.8rem;
        color: #0a2a44;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .home-title p {
        margin: 0.3rem 0 0;
        opacity: 0.85;
        color: #1e2a3a;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS (all the existing ones, unchanged) ==========
# I'm omitting them in this response for brevity, but they remain identical.
# The only change is in the UI strings: replace "GLOBALINTERNET.PY" with "Home Sweet Home" in translations and main UI.
# For the purpose of this answer, I'll show the main changes in the main_app and login_interface functions.

# ... (all helper functions like make_clickable, get_youtube_id, etc. are unchanged)

# ========== PAGE RENDERING FUNCTIONS (with name changes) ==========

def main_app():
    with st.sidebar:
        # --- Debug: show refresh token status (remove after fixing) ---
        if st.session_state.logged_in:
            st.success("✅ Logged in")
            if st.session_state.refresh_token:
                st.info("🔑 Refresh token present")
            else:
                st.warning("⚠️ No refresh token")
        else:
            st.info("🔓 Not logged in")
            try:
                cookie_token = st.query_params.get("cookie_sb_refresh_token", [None])[0]
                if cookie_token:
                    st.info("🍪 Refresh token found in cookie")
                else:
                    st.info("🍪 No refresh token cookie")
            except:
                pass
        st.divider()

        st.markdown("<div class='haiti-symbol'>🇭🇹</div>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes<br>
            Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        if st.session_state.unread_count > 0:
            st.sidebar.markdown(f"🔔 **Notifications** <span class='notification-badge'>({st.session_state.unread_count})</span>", unsafe_allow_html=True)

        if st.session_state.profile and st.session_state.profile.get("is_live"):
            st.markdown(f"🔴 **{t('you_are_live')}**")
            if st.button(t("end_live_session")):
                for ls in st.session_state.live_sessions:
                    if ls["user_id"] == st.session_state.user.id:
                        end_live_session(ls["id"])
                        st.rerun()
                        break
        else:
            with st.expander(t("go_live")):
                st.markdown(f"**{t('select_platform')}:**")
                method = st.radio(t("select_platform"), [t("external_platform"), t("in_app_camera")], index=0)
                platform = None
                if method == t("external_platform"):
                    st.markdown(f"**{t('select_platform')}:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("📺 YouTube", key="yt"):
                            platform = "YouTube"
                    with col2:
                        if st.button("📘 Facebook", key="fb"):
                            platform = "Facebook"
                    with col3:
                        if st.button("🎮 Twitch", key="tw"):
                            platform = "Twitch"
                else:
                    platform = "inapp"

                if platform:
                    st.markdown(f"**Selected: {platform if platform != 'inapp' else t('in_app_camera')}**")
                    with st.form("go_live_form"):
                        title = st.text_input(t("live_title"))
                        if st.form_submit_button(t("create_live_session")):
                            if title:
                                session_id = create_live_session(
                                    title, 
                                    platform, 
                                    method='external' if platform != 'inapp' else 'inapp'
                                )
                                if session_id:
                                    if platform == 'inapp':
                                        st.success(t("you_are_live"))
                                    else:
                                        st.success(t("you_are_live"))
                                        st.info(f"**Stream Key:** `{st.session_state.stream_key}`")
                                        st.markdown(f"**Start streaming on {platform}:** [Click here](https://www.{platform.lower()}.com/live)")
                                    st.rerun()
                            else:
                                st.warning("Please enter a title")

        st.divider()

        lat, sig, qual = get_network_status()
        st.markdown(f"### {t('system_health')}")
        st.markdown(f"""
        <div class='health-text'>
        {t('signal')}: {sig}<br>
        {t('latency')}: {lat}ms<br>
        {t('quality')}: {qual}%<br>
        {t('uptime')}: {get_uptime()}<br>
        {t('encrypted')}
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown(f"{t('compensation')}: ${st.session_state.data_comp:.4f}")
        st.divider()
        if st.session_state.profile:
            st.markdown(f"{t('logged_in_as')}: {st.session_state.profile.get('full_name', 'User')}")
        if st.button(t("logout")):
            logout()
        st.divider()

        pages = {
            t("feed"): render_feed,
            t("friends_chat"): render_friends_page,
            t("satellite_map"): render_map,
            t("profile"): render_profile,
            t("owner_space"): owner_space
        }
        choice = st.selectbox(t("feed"), list(pages.keys()))
    pages[choice]()

# --- Login Interface (updated title and background) ---
def login_interface():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center;'><span class='haiti-symbol' style='font-size:6rem;'>🇭🇹</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #0a2a44;'>🏠 Home Sweet Home</h1>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name' style='font-size:1.8rem;'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators' style='font-size:1rem;'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes · Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        # Language selector
        lang_options = {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "pt": "Português",
            "ru": "Русский",
            "ar": "العربية",
            "zh": "中文",
            "hi": "हिन्दी"
        }
        selected_lang = st.selectbox("Language / Langue / Idioma", options=list(lang_options.keys()), format_func=lambda x: lang_options[x], index=0)
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

        auth_method = st.radio(t("login_title"), [t("email_method"), t("phone_method")], horizontal=True)

        if auth_method == t("email_method"):
            tab1, tab2, tab3 = st.tabs([t("login_title"), t("signup_title"), t("forgot_password")])
            with tab1:
                with st.form("login_email"):
                    email = st.text_input(t("email"))
                    password = st.text_input(t("password"), type="password")
                    remember = st.checkbox(t("remember_me"))
                    if st.form_submit_button(t("login_button"), use_container_width=True):
                        if email and password:
                            log_in_email(email, password, remember)
                        else:
                            st.warning("Please enter email and password")
            with tab2:
                with st.form("signup_email"):
                    full_name = st.text_input(t("full_name"))
                    email = st.text_input(t("email"))
                    password = st.text_input(t("password"), type="password")
                    if st.form_submit_button(t("signup_button"), use_container_width=True):
                        if full_name and email and password:
                            sign_up_email(email, password, full_name)
                        else:
                            st.warning("Please fill all fields")
            with tab3:
                with st.form("reset_email"):
                    reset_email = st.text_input(t("email"))
                    if st.form_submit_button(t("send_reset_link"), use_container_width=True):
                        if reset_email:
                            reset_password_email(reset_email)
                        else:
                            st.warning("Please enter your email")
        else:
            st.info("Phone users: You will receive a 6‑digit OTP each time you log in.")
            if not st.session_state.phone_otp_sent:
                with st.form("phone_request"):
                    phone = st.text_input(t("phone_number"))
                    remember = st.checkbox(t("remember_me"))
                    if st.form_submit_button(t("send_otp"), use_container_width=True):
                        if phone:
                            if send_phone_otp(phone):
                                st.session_state.phone_otp_sent = True
                                st.session_state.temp_phone = phone
                                st.session_state.phone_remember = remember
                                st.rerun()
                        else:
                            st.warning("Please enter a phone number")
            else:
                st.write(f"OTP sent to **+{st.session_state.temp_phone}**")
                with st.form("phone_verify"):
                    otp = st.text_input(t("enter_otp"))
                    if st.form_submit_button(t("verify_login"), use_container_width=True):
                        if otp:
                            remember = st.session_state.get("phone_remember", False)
                            verify_phone_otp(st.session_state.temp_phone, otp, remember)
                        else:
                            st.warning("Please enter the OTP")
                if st.button(t("back_resend")):
                    st.session_state.phone_otp_sent = False
                    st.session_state.temp_phone = ""
                    st.rerun()

# ---------- MAIN ENTRY ----------
if __name__ == "__main__":
    # Show the app header (Home Sweet Home) only if we are not in global password prompt
    if st.session_state.get("app_authenticated", False) or not APP_PASSWORD:
        st.markdown("""
        <div class="home-title">
            <h1>🏠 Home Sweet Home</h1>
            <p>Your satellite communication & social platform</p>
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
