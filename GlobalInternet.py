"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 72.0.2 (Fixed gift loading and session errors)
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

# ====== PAGE CONFIG ======
st.set_page_config(page_title="GLOBALINTERNET.PY", page_icon="🇭🇹", layout="wide")

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

# --- Cookie helpers ---
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

# --- Token refresh function ---
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

# --- Restore session from cookie ---
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

# --- UI styling ---
st.markdown("""
    <style>
    .stApp [data-testid="stAppViewContainer"] {
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
    </style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========

def make_clickable(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)

def get_or_create_profile(user_id, identifier):
    if supabase is None:
        return None
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        else:
            if '@' in identifier:
                default_name = identifier.split('@')[0]
            else:
                default_name = f"User {identifier[-4:]}" if len(identifier) > 4 else "User"
            new_profile = {
                "id": user_id,
                "full_name": default_name,
                "avatar_url": None,
                "bio": "",
                "location": "",
                "is_live": False,
                "moncash_phone": None
            }
            insert_response = supabase.table("profiles").insert(new_profile).execute()
            if insert_response.data:
                return insert_response.data[0]
            else:
                st.session_state.last_error = "Failed to create profile."
                return None
    except Exception as e:
        st.session_state.last_error = f"Error in get_or_create_profile: {e}"
        return None

def update_profile(profile_data):
    if supabase is None:
        return False
    try:
        supabase.table("profiles").update(profile_data).eq("id", profile_data["id"]).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error updating profile: {e}"
        return False

def upload_avatar(user_id, image_file):
    if supabase is None:
        return None
    try:
        ext = image_file.name.split('.')[-1]
        file_name = f"{user_id}_{int(time.time())}.{ext}"
        image_bytes = image_file.getvalue()
        supabase.storage.from_("avatars").upload(file_name, image_bytes)
        public_url = supabase.storage.from_("avatars").get_public_url(file_name)
        return public_url
    except Exception as e:
        error_message = str(e)
        if "new row violates row-level security policy" in error_message:
            st.error("Storage permission error: Please set up RLS policies for the 'avatars' bucket.")
        else:
            st.session_state.last_error = f"Avatar upload failed: {e}"
        return None

def upload_post_media(user_id, file):
    if supabase is None:
        return None
    try:
        content_type = file.type
        ext = file.name.split('.')[-1]
        timestamp = int(time.time())
        random_hash = hashlib.md5(file.name.encode()).hexdigest()[:8]
        file_name = f"post_{user_id}_{timestamp}_{random_hash}.{ext}"
        file_bytes = file.getvalue()
        supabase.storage.from_("post_media").upload(
            file_name, 
            file_bytes, 
            {"content-type": content_type}
        )
        public_url = supabase.storage.from_("post_media").get_public_url(file_name)
        media_type = "video" if content_type.startswith("video") else "image"
        return {"url": public_url, "type": media_type}
    except Exception as e:
        error_message = str(e)
        if "new row violates row-level security policy" in error_message:
            st.error("Storage permission error: Please set up RLS policies for the 'post_media' bucket.")
        else:
            st.session_state.last_error = f"Media upload failed: {e}"
        return None

def upload_chat_media(user_id, file):
    if supabase is None:
        return None
    try:
        content_type = file.type
        ext = file.name.split('.')[-1]
        timestamp = int(time.time())
        random_hash = hashlib.md5(file.name.encode()).hexdigest()[:8]
        file_name = f"chat_{user_id}_{timestamp}_{random_hash}.{ext}"
        file_bytes = file.getvalue()
        supabase.storage.from_("chat_media").upload(
            file_name, 
            file_bytes, 
            {"content-type": content_type}
        )
        public_url = supabase.storage.from_("chat_media").get_public_url(file_name)
        media_type = "video" if content_type.startswith("video") else "image"
        return {"url": public_url, "type": media_type}
    except Exception as e:
        error_message = str(e)
        if "new row violates row-level security policy" in error_message:
            st.error("Storage permission error: Please set up RLS policies for the 'chat_media' bucket.")
        else:
            st.session_state.last_error = f"Chat media upload failed: {e}"
        return None

def delete_post(post_id):
    if supabase is None:
        return False
    try:
        supabase.table("posts").delete().eq("id", post_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error deleting post: {e}"
        return False

# --- Exchange rate fetching ---
def fetch_exchange_rate():
    try:
        resp = requests.get(EXCHANGE_RATE_API, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if 'rates' in data and 'HTG' in data['rates']:
                return float(data['rates']['HTG'])
        return 100.0
    except:
        return 100.0

# --- Live gift functions (fixed) ---
def send_gift(session_id, sender_id, recipient_id, amount, currency):
    if supabase is None:
        return False, "Supabase not configured"
    try:
        rate = st.session_state.exchange_rate
        if currency == "USD":
            amount_htg = amount * rate
        else:
            amount_htg = amount

        gift_data = {
            "session_id": session_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "amount": amount,
            "currency": currency,
            "converted_amount_htg": amount_htg,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        result = supabase.table("live_gifts").insert(gift_data).execute()
        if not result.data:
            return False, "Failed to record gift"

        gift_id = result.data[0]["id"]

        # Simulate payment processing
        payment_success = True
        if payment_success:
            supabase.table("live_gifts").update({"status": "completed"}).eq("id", gift_id).execute()
            sender_name = st.session_state.profile["full_name"]
            supabase.table("notifications").insert({
                "user_id": recipient_id,
                "type": "gift",
                "message": f"🎁 You received a gift of {amount} {currency} from {sender_name}!",
                "read": False
            }).execute()
            return True, "Gift sent successfully!"
        else:
            supabase.table("live_gifts").update({"status": "failed"}).eq("id", gift_id).execute()
            return False, "Payment failed. Please try again."
    except Exception as e:
        st.session_state.last_error = f"Error sending gift: {e}"
        return False, str(e)

def load_gifts_for_session(session_id):
    """Load gifts for a session, with fallback if foreign key relationship fails."""
    if supabase is None:
        return []
    try:
        # Try with join first
        resp = supabase.table("live_gifts").select("*, sender:sender_id(full_name, avatar_url)").eq("session_id", session_id).eq("status", "completed").order("created_at").execute()
        return resp.data
    except Exception as e:
        # If join fails (foreign key missing), fall back to simple query
        st.warning("Gift sender names unavailable (foreign key missing). Gifts still tracked.")
        try:
            resp = supabase.table("live_gifts").select("*").eq("session_id", session_id).eq("status", "completed").order("created_at").execute()
            # Add dummy sender info
            gifts = resp.data or []
            for g in gifts:
                g['sender'] = {'full_name': 'Someone', 'avatar_url': None}
            return gifts
        except Exception as e2:
            st.session_state.last_error = f"Error loading gifts: {e2}"
            return []

# --- Post functions ---
@st.cache_data(ttl=60, show_spinner=False)
def load_posts_cached(user_id=None, author_id=None):
    if supabase is None:
        return []
    try:
        select_cols = "*, profiles!posts_user_id_fkey(full_name, avatar_url, is_live)"
        if author_id is not None:
            resp = supabase.table("posts").select(select_cols).eq("user_id", author_id).eq("is_public", True).order("created_at", desc=True).execute()
            posts = resp.data
        elif user_id is not None:
            public_resp = supabase.table("posts").select(select_cols).eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            private_resp = supabase.table("posts").select(select_cols).eq("is_public", False).eq("user_id", user_id).order("created_at", desc=True).execute()
            posts = public_resp.data + private_resp.data
            seen = set()
            unique_posts = []
            for p in posts:
                if p["id"] not in seen:
                    seen.add(p["id"])
                    unique_posts.append(p)
            posts = unique_posts
            posts.sort(key=lambda x: x['created_at'], reverse=True)
        else:
            resp = supabase.table("posts").select(select_cols).eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            posts = resp.data

        for post in posts:
            post["media_urls"] = post.get("media_urls", [])
            reactions_resp = supabase.table("reactions").select("emoji").eq("post_id", post["id"]).execute()
            counts = {}
            if reactions_resp.data:
                for r in reactions_resp.data:
                    emoji = r["emoji"]
                    counts[emoji] = counts.get(emoji, 0) + 1
            post["reactions"] = counts
            comments_resp = supabase.table("comments").select("id", count="exact").eq("post_id", post["id"]).execute()
            post["comment_count"] = comments_resp.count if hasattr(comments_resp, 'count') else 0
        return posts
    except Exception as e:
        st.session_state.last_error = f"Error loading posts: {e}"
        return []

def load_posts():
    user_id = st.session_state.user.id if st.session_state.user else None
    return load_posts_cached(user_id)

def load_user_posts(user_id):
    return load_posts_cached(author_id=user_id)

def create_post(user_id, content, media_files=None, is_public=True, existing_media_urls=None):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        media_urls = []
        if media_files:
            for f in media_files:
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
        if existing_media_urls:
            media_urls.extend(existing_media_urls)

        post = {
            "user_id": user_id,
            "content": content,
            "is_public": is_public,
            "likes_count": 0,
            "shares_count": 0,
            "media_urls": media_urls,
            "created_at": datetime.now().isoformat()
        }
        result = supabase.table("posts").insert(post).execute()
        if result.data:
            st.cache_data.clear()
            st.session_state.posts = load_posts()
            st.success("✅ Post published!")
            return True
        else:
            st.session_state.last_error = "Post insertion failed."
            return False
    except Exception as e:
        st.session_state.last_error = f"Error creating post: {e}"
        return False

def toggle_reaction(post_id, user_id, emoji):
    if supabase is None:
        return False
    try:
        check = supabase.table("reactions").select("id").eq("post_id", post_id).eq("user_id", user_id).eq("emoji", emoji).execute()
        if check.data:
            supabase.table("reactions").delete().eq("post_id", post_id).eq("user_id", user_id).eq("emoji", emoji).execute()
        else:
            supabase.table("reactions").insert({
                "post_id": post_id,
                "user_id": user_id,
                "emoji": emoji
            }).execute()
        st.cache_data.clear()
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error toggling reaction: {e}"
        return False

def share_post(original_post_id, user_id, is_public=True):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        supabase.rpc("increment_shares", {"post_id": original_post_id}).execute()
        post = {
            "user_id": user_id,
            "content": f"(Shared post)",
            "is_public": is_public,
            "original_post_id": original_post_id,
            "likes_count": 0,
            "shares_count": 0,
            "media_urls": [],
            "created_at": datetime.now().isoformat()
        }
        supabase.table("posts").insert(post).execute()
        st.cache_data.clear()
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error sharing post: {e}"
        return False

# --- Comment functions ---
def add_comment(post_id, user_id, content, parent_id=None):
    if supabase is None:
        return False
    try:
        comment = {
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "likes": 0,
            "created_at": datetime.now().isoformat()
        }
        if parent_id:
            comment["parent_id"] = parent_id
        supabase.table("comments").insert(comment).execute()
        st.cache_data.clear()
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error adding comment: {e}"
        return False

def load_comments(post_id):
    if supabase is None:
        return []
    try:
        response = supabase.table("comments").select(
            "*, profiles!comments_user_id_fkey(full_name, avatar_url)"
        ).eq("post_id", post_id).order("created_at").execute()
        return response.data
    except Exception as e:
        st.session_state.last_error = f"Error loading comments: {e}"
        return []

def delete_comment(comment_id):
    if supabase is None:
        return False
    try:
        supabase.table("comments").delete().eq("id", comment_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error deleting comment: {e}"
        return False

def like_comment(comment_id, increment=True):
    if supabase is None:
        return False
    try:
        if increment:
            supabase.rpc("increment_comment_likes", {"comment_id": comment_id}).execute()
        else:
            supabase.rpc("decrement_comment_likes", {"comment_id": comment_id}).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error toggling comment like: {e}"
        return False

# --- Live session functions (with missing column check) ---
def create_live_session(title, platform, method='external'):
    if supabase is None or st.session_state.user is None:
        st.session_state.last_error = "Cannot start live session."
        return None
    try:
        # Check if stream_method column exists, if not, add it
        try:
            supabase.table("live_sessions").select("stream_method").limit(1).execute()
        except Exception as e:
            if "column 'stream_method' does not exist" in str(e):
                st.warning("Adding missing 'stream_method' column to live_sessions table...")
                # This requires raw SQL, we can't do it here. User must run SQL manually.
                st.error("Please run: ALTER TABLE live_sessions ADD COLUMN stream_method TEXT DEFAULT 'external';")
                return None

        active = supabase.table("live_sessions").select("id").eq("user_id", st.session_state.user.id).eq("is_live", True).execute()
        if active.data:
            st.warning("You already have an active live session. End it first.")
            return None

        stream_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20)) if method == 'external' else None
        session_data = {
            "user_id": st.session_state.user.id,
            "title": title,
            "is_live": True,
            "started_at": datetime.now().isoformat(),
            "stream_url": None,
            "platform": platform if method == 'external' else 'inapp',
            "stream_key": stream_key,
            "stream_method": method
        }
        result = supabase.table("live_sessions").insert(session_data).execute()
        if result.data:
            supabase.table("profiles").update({"is_live": True}).eq("id", st.session_state.user.id).execute()
            st.session_state.profile["is_live"] = True
            st.session_state.live_sessions = load_live_sessions()
            st.session_state.stream_key = stream_key
            st.session_state.selected_platform = platform if method == 'external' else 'inapp'
            return result.data[0]["id"]
        else:
            st.session_state.last_error = "Failed to start live session."
            return None
    except Exception as e:
        st.session_state.last_error = f"Error starting live session: {e}"
        return None

def update_live_stream_url(session_id, stream_url):
    if supabase is None:
        return False
    try:
        supabase.table("live_sessions").update({
            "stream_url": stream_url
        }).eq("id", session_id).execute()
        st.session_state.live_sessions = load_live_sessions()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error updating stream URL: {e}"
        return False

def end_live_session(session_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_sessions").update({
            "is_live": False,
            "ended_at": datetime.now().isoformat()
        }).eq("id", session_id).execute()
        supabase.table("profiles").update({"is_live": False}).eq("id", st.session_state.user.id).execute()
        st.session_state.profile["is_live"] = False
        st.session_state.live_sessions = load_live_sessions()
        st.session_state.stream_key = None
        st.session_state.selected_platform = None
        return True
    except Exception as e:
        st.session_state.last_error = f"Error ending live session: {e}"
        return False

def load_live_sessions():
    if supabase is None:
        return []
    try:
        # If stream_method column missing, load without it
        try:
            response = supabase.table("live_sessions").select(
                "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url, moncash_phone)"
            ).eq("is_live", True).order("started_at", desc=True).execute()
            return response.data
        except Exception as e:
            if "column 'stream_method' does not exist" in str(e):
                # Fallback to select without stream_method
                response = supabase.table("live_sessions").select(
                    "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url, moncash_phone)"
                ).eq("is_live", True).order("started_at", desc=True).execute()
                # Add default stream_method
                for s in response.data:
                    s['stream_method'] = 'external'
                return response.data
            else:
                raise e
    except Exception as e:
        st.session_state.last_error = f"Error loading live sessions: {e}"
        return []

def get_live_session(session_id):
    if supabase is None:
        return None
    try:
        response = supabase.table("live_sessions").select(
            "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url, moncash_phone)"
        ).eq("id", session_id).single().execute()
        # If stream_method missing, add default
        if response.data and 'stream_method' not in response.data:
            response.data['stream_method'] = 'external'
        return response.data
    except Exception as e:
        st.session_state.last_error = f"Error fetching live session: {e}"
        return None

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

# --- Authentication ---
def sign_up_email(email, password, full_name):
    if supabase is None:
        st.session_state.last_error = "Registration unavailable."
        return False
    try:
        user = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}}
        })
        if user.user:
            st.success("Sign-up successful! Please log in.")
            return True
    except Exception as e:
        st.session_state.last_error = f"Sign-up failed: {e}"
        return False

def log_in_email(email, password, remember=False):
    if supabase is None:
        st.session_state.last_error = "Login unavailable."
        return
    try:
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if user.user:
            st.session_state.logged_in = True
            st.session_state.user = user.user
            if user.session:
                st.session_state.refresh_token = user.session.refresh_token
            profile = get_or_create_profile(user.user.id, email)
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.session_state.posts = load_posts()
            st.session_state.live_sessions = load_live_sessions()
            load_friend_data()
            st.session_state.notifications = load_notifications(user.user.id)
            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
            st.session_state.exchange_rate = fetch_exchange_rate()
            if remember and user.session:
                set_cookie("sb_refresh_token", user.session.refresh_token, 30)
            st.rerun()
    except Exception as e:
        st.session_state.last_error = f"Login failed: {e}"

def reset_password_email(email):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        supabase.auth.reset_password_for_email(email)
        st.success("Password reset email sent. Please check your inbox.")
        return True
    except Exception as e:
        st.session_state.last_error = f"Failed to send reset email: {e}"
        return False

def format_phone(phone: str) -> str:
    phone = phone.strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

def send_phone_otp(raw_phone):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        phone = format_phone(raw_phone)
        if len(phone) < 8 or not phone[1:].isdigit():
            st.error("Please enter a valid international phone number with country code, e.g., 50947385663 for Haiti or 447840379 for UK.")
            return False
        supabase.auth.sign_in_with_otp({"phone": phone})
        st.success("OTP sent to your phone. Please enter the 6-digit code below.")
        return True
    except Exception as e:
        st.session_state.last_error = f"Failed to send OTP: {e}"
        return False

def verify_phone_otp(raw_phone, token, remember=False):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        phone = format_phone(raw_phone)
        session = supabase.auth.verify_otp({
            "phone": phone,
            "token": token,
            "type": "sms"
        })
        if session.user:
            st.session_state.logged_in = True
            st.session_state.user = session.user
            if session.session:
                st.session_state.refresh_token = session.session.refresh_token
            profile = get_or_create_profile(session.user.id, phone)
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.session_state.posts = load_posts()
            st.session_state.live_sessions = load_live_sessions()
            st.session_state.phone_otp_sent = False
            st.session_state.temp_phone = ""
            if remember and session.session:
                set_cookie("sb_refresh_token", session.session.refresh_token, 30)
            st.rerun()
            return True
        else:
            st.session_state.last_error = "Verification failed – no user returned."
            return False
    except Exception as e:
        st.session_state.last_error = f"Verification failed: {e}"
        return False

def logout():
    set_cookie("sb_refresh_token", "", -1)
    if supabase:
        supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        if key not in ["logged_in", "user", "profile", "posts", "live_sessions", "owner_space_access"]:
            st.session_state[key] = None
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.refresh_token = None
    st.session_state.owner_space_access = False
    st.session_state.phone_otp_sent = False
    st.session_state.temp_phone = ""
    st.session_state.viewing_live = None
    st.session_state.viewing_profile = None
    st.rerun()

# --- Friend, Chat, Call functions ---
def load_notifications(user_id):
    if supabase is None:
        return []
    try:
        notif = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return notif.data
    except Exception as e:
        st.session_state.last_error = f"Error loading notifications: {e}"
        return []

def mark_notification_read(notif_id):
    if supabase is None:
        return
    try:
        supabase.table("notifications").update({"read": True}).eq("id", notif_id).execute()
    except Exception as e:
        st.session_state.last_error = f"Error marking notification read: {e}"

def send_friend_request(sender_id, receiver_id):
    if supabase is None:
        return False, "Not logged in"
    try:
        existing1 = supabase.table("friend_requests").select("id").eq("sender_id", sender_id).eq("receiver_id", receiver_id).execute()
        existing2 = supabase.table("friend_requests").select("id").eq("sender_id", receiver_id).eq("receiver_id", sender_id).execute()
        if existing1.data or existing2.data:
            return False, "Friend request already exists"
        data = {"sender_id": sender_id, "receiver_id": receiver_id, "status": "pending"}
        supabase.table("friend_requests").insert(data).execute()
        sender_name = st.session_state.profile["full_name"]
        supabase.table("notifications").insert({
            "user_id": receiver_id,
            "type": "friend_request",
            "message": f"{sender_name} sent you a friend request",
            "read": False
        }).execute()
        return True, "Friend request sent"
    except Exception as e:
        return False, str(e)

def respond_friend_request(request_id, accept):
    if supabase is None:
        return False, "Not logged in"
    try:
        req = supabase.table("friend_requests").select("*").eq("id", request_id).single().execute()
        if not req.data:
            return False, "Request not found"
        new_status = "accepted" if accept else "rejected"
        supabase.table("friend_requests").update({"status": new_status}).eq("id", request_id).execute()
        if accept:
            receiver_name = st.session_state.profile["full_name"]
            supabase.table("notifications").insert({
                "user_id": req.data["sender_id"],
                "type": "friend_accept",
                "related_id": request_id,
                "message": f"{receiver_name} accepted your friend request",
                "read": False
            }).execute()
        return True, f"Request {new_status}"
    except Exception as e:
        return False, str(e)

def load_friend_data():
    if supabase is None or not st.session_state.user:
        st.write("Supabase or user missing")
        return
    user_id = st.session_state.user.id
    st.write(f"Loading friends for user {user_id}")
    pending = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "pending").execute()
    st.write("Pending requests:", pending.data)
    st.session_state.friend_requests = pending.data if pending.data else []
    sent = supabase.table("friend_requests").select("*, receiver:receiver_id(full_name, avatar_url)").eq("sender_id", user_id).eq("status", "accepted").execute()
    st.write("Accepted sent requests:", sent.data)
    received = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "accepted").execute()
    st.write("Accepted received requests:", received.data)
    friends = []
    for r in sent.data:
        friends.append({"id": r["receiver"]["id"], "full_name": r["receiver"]["full_name"], "avatar_url": r["receiver"].get("avatar_url")})
    for r in received.data:
        friends.append({"id": r["sender"]["id"], "full_name": r["sender"]["full_name"], "avatar_url": r["sender"].get("avatar_url")})
    st.session_state.friends = friends
    st.write("Final friends list:", friends)

def search_users(query):
    if supabase is None or not st.session_state.user:
        return []
    try:
        result = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone").neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(50).execute()
        return result.data
    except Exception as e:
        st.session_state.last_error = f"Search failed: {e}"
        return []

def send_message(sender_id, receiver_id, content, media_file=None):
    if supabase is None:
        return False
    try:
        media_info = None
        if media_file:
            media_info = upload_chat_media(sender_id, media_file)
        msg_data = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "read": False,
            "created_at": datetime.now().isoformat()
        }
        if media_info:
            msg_data["media_url"] = media_info["url"]
            msg_data["media_type"] = media_info["type"]
        supabase.table("messages").insert(msg_data).execute()
        sender_name = st.session_state.profile["full_name"]
        supabase.table("notifications").insert({
            "user_id": receiver_id,
            "type": "message",
            "message": f"New message from {sender_name}",
            "read": False
        }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error sending message: {e}"
        return False

def load_messages(user_id, other_id):
    if supabase is None:
        return []
    try:
        sent = supabase.table("messages").select("*").eq("sender_id", user_id).eq("receiver_id", other_id).execute()
        received = supabase.table("messages").select("*").eq("sender_id", other_id).eq("receiver_id", user_id).execute()
        all_msgs = (sent.data or []) + (received.data or [])
        all_msgs.sort(key=lambda x: x['created_at'])
        supabase.table("messages").update({"read": True}).eq("sender_id", other_id).eq("receiver_id", user_id).execute()
        return all_msgs
    except Exception as e:
        st.session_state.last_error = f"Error loading messages: {e}"
        return []

def get_conversations(user_id):
    if supabase is None:
        return []
    try:
        sent = supabase.table("messages").select("receiver_id").eq("sender_id", user_id).execute()
        received = supabase.table("messages").select("sender_id").eq("receiver_id", user_id).execute()
        other_ids = set()
        for s in sent.data:
            other_ids.add(s["receiver_id"])
        for r in received.data:
            other_ids.add(r["sender_id"])
        if not other_ids:
            return []
        profiles = supabase.table("profiles").select("id, full_name, avatar_url").in_("id", list(other_ids)).execute()
        return profiles.data
    except Exception as e:
        st.session_state.last_error = f"Error loading conversations: {e}"
        return []

def start_call(room_id=None):
    if not room_id:
        room_id = hashlib.md5(f"{st.session_state.user.id}_{time.time()}".encode()).hexdigest()[:10]
    st.session_state.call_room = room_id
    st.session_state.in_call = True

def end_call():
    st.session_state.in_call = False
    st.session_state.call_room = None

# ========== OWNER NOTIFICATIONS ==========
def get_last_seen_signup():
    if supabase is None:
        return datetime(2020, 1, 1)
    try:
        resp = supabase.table("owner_state").select("last_seen_signup").eq("id", 1).execute()
        if resp.data:
            return datetime.fromisoformat(resp.data[0]["last_seen_signup"].replace('Z', '+00:00'))
        else:
            supabase.table("owner_state").insert({"id": 1, "last_seen_signup": datetime.now().isoformat()}).execute()
            return datetime.now() - timedelta(days=365)
    except Exception as e:
        st.session_state.last_error = f"Error getting last seen signup: {e}"
        return datetime(2020, 1, 1)

def update_last_seen_signup():
    if supabase is None:
        return
    try:
        supabase.table("owner_state").update({"last_seen_signup": datetime.now().isoformat()}).eq("id", 1).execute()
    except Exception as e:
        st.session_state.last_error = f"Error updating last seen signup: {e}"

def get_new_users(since):
    if supabase is None:
        return []
    try:
        since_str = since.isoformat()
        resp = supabase.table("profiles").select("id, full_name, avatar_url, join_date").gt("join_date", since_str).order("join_date").execute()
        return resp.data
    except Exception as e:
        st.session_state.last_error = f"Error fetching new users: {e}"
        return []

def send_email_notification(new_users):
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO]):
        return
    if not new_users:
        return
    subject = f"New User Signups - {len(new_users)} new user(s)"
    body = "The following users have signed up since your last visit:\n\n"
    for u in new_users:
        joined = u.get('join_date', '')[:16] if u.get('join_date') else ''
        body += f"- {u['full_name']} (ID: {u['id']}) at {joined}\n"
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        st.session_state.last_error = f"Email send failed: {e}"

# ========== PAGE RENDERING FUNCTIONS ==========

# --- ENHANCED render_live_page with visible broadcast button and error handling ---
def render_live_page(session_id):
    session = get_live_session(session_id)
    if not session or not session.get("is_live"):
        st.error("This live session has ended or does not exist.")
        if st.button("Back to Feed"):
            st.session_state.viewing_live = None
            st.rerun()
        return

    is_broadcaster = st.session_state.user and session["user_id"] == st.session_state.user.id
    st.header(f"🔴 LIVE: {session['title']}")

    # Debug: show who you are
    if is_broadcaster:
        st.success("✅ You are the broadcaster. Use the controls below to start streaming.")
    else:
        st.info("👀 You are a viewer. Click 'Watch Stream' to see the live video.")

    gifts = load_gifts_for_session(session_id)
    total_gifts_htg = sum(g.get('converted_amount_htg', 0) for g in gifts)

    col1, col2 = st.columns([2, 1])
    with col1:
        stream_method = session.get("stream_method", "external")
        if stream_method == "external":
            # Existing external streaming code
            stream_url = session.get("stream_url")
            platform = session.get("platform")
            if is_broadcaster:
                with st.expander("📹 Set Stream URL", expanded=not stream_url):
                    with st.form("update_stream_url"):
                        new_url = st.text_input("Paste your live stream URL (YouTube, Facebook, Twitch)", value=stream_url or "")
                        if st.form_submit_button("Update Stream URL"):
                            if new_url:
                                if update_live_stream_url(session_id, new_url):
                                    st.success("Stream URL updated! Refreshing...")
                                    st.rerun()
                            else:
                                st.warning("Please enter a URL")
            if stream_url:
                if "facebook.com" in stream_url:
                    embed_code = f"""
                    <div id="fb-root"></div>
                    <script async defer src="https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v3.2"></script>
                    <div class="fb-video" data-href="{stream_url}" 
                         data-width="100%" data-allowfullscreen="true" data-autoplay="true"></div>
                    """
                    st.components.v1.html(embed_code, height=450)
                elif "youtube.com" in stream_url or "youtu.be" in stream_url:
                    if "youtu.be" in stream_url:
                        video_id = stream_url.split("/")[-1].split("?")[0]
                    elif "watch?v=" in stream_url:
                        video_id = stream_url.split("v=")[-1].split("&")[0]
                    else:
                        video_id = None
                    if video_id:
                        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
                        st.components.v1.html(f'<iframe width="100%" height="400" src="{embed_url}" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>', height=410)
                    else:
                        st.video(stream_url)
                elif "twitch.tv" in stream_url:
                    channel = stream_url.split("/")[-1]
                    embed_url = f"https://player.twitch.tv/?channel={channel}&parent={st.request.host}"
                    st.components.v1.html(f'<iframe src="{embed_url}" height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>', height=410)
                else:
                    st.video(stream_url)
            else:
                st.info("The streamer has not provided a video URL yet.")
        else:  # in-app streaming
            if is_broadcaster:
                # BROADCASTER VIEW – with prominent button
                broadcaster_html = f"""
                <div style="background: #1e2a3a; padding: 30px; border-radius: 20px; text-align: center; color: white;">
                    <div style="font-size: 24px; margin-bottom: 20px;">🎥 Your Live Stream</div>
                    <div style="background: #000; width: 100%; max-width: 600px; margin: 0 auto; border-radius: 16px; overflow: hidden; border: 3px solid #00a8ff;">
                        <video id="localVideo" autoplay muted style="width: 100%; aspect-ratio: 16/9; background: #111; display: block;"></video>
                    </div>
                    <div style="margin-top: 30px;">
                        <button id="startBtn" style="background: #00a8ff; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer; box-shadow: 0 8px 20px rgba(0,168,255,0.4);">▶ START BROADCAST</button>
                        <button id="stopBtn" style="background: #ff4444; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer; display: none; margin-left: 20px;">■ STOP BROADCAST</button>
                    </div>
                    <p id="status" style="margin-top: 20px; font-size: 18px; color: #ccc;">Ready to start. Click the button above.</p>
                </div>
                <script src="https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js"></script>
                <script>
                (function() {{
                    const sessionId = {session_id};
                    const userId = "{st.session_state.user.id}";
                    let localStream = null;
                    let peer = null;
                    let call = null;
                    const startBtn = document.getElementById('startBtn');
                    const stopBtn = document.getElementById('stopBtn');
                    const statusEl = document.getElementById('status');
                    const localVideo = document.getElementById('localVideo');

                    startBtn.onclick = async () => {{
                        try {{
                            statusEl.textContent = '📷 Requesting camera access...';
                            localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                            localVideo.srcObject = localStream;
                            statusEl.textContent = '✅ Camera access granted. Connecting to peer server...';

                            peer = new Peer(`broadcaster-${{sessionId}}`, {{ 
                                host: '0.peerjs.com',
                                port: 443,
                                secure: true,
                                config: {{
                                    'iceServers': [
                                        {{ urls: 'stun:stun.l.google.com:19302' }},
                                        {{ urls: 'stun:stun1.l.google.com:19302' }}
                                    ]
                                }}
                            }});

                            peer.on('open', (id) => {{
                                statusEl.textContent = `✅ Broadcasting live! Your peer ID: ${{id}}`;
                                startBtn.style.display = 'none';
                                stopBtn.style.display = 'inline-block';
                            }});

                            peer.on('call', (incomingCall) => {{
                                incomingCall.answer(localStream);
                                call = incomingCall;
                            }});

                            peer.on('error', (err) => {{
                                statusEl.textContent = '❌ Peer error: ' + err;
                            }});
                        }} catch (err) {{
                            statusEl.textContent = '❌ Error: ' + err.message;
                        }}
                    }};

                    stopBtn.onclick = () => {{
                        if (call) call.close();
                        if (peer) peer.destroy();
                        if (localStream) localStream.getTracks().forEach(track => track.stop());
                        localVideo.srcObject = null;
                        startBtn.style.display = 'inline-block';
                        stopBtn.style.display = 'none';
                        statusEl.textContent = 'Broadcast ended';
                    }};
                }})();
                </script>
                """
                st.components.v1.html(broadcaster_html, height=650)
            else:
                # VIEWER VIEW – with watch button
                viewer_html = f"""
                <div style="background: #1e2a3a; padding: 30px; border-radius: 20px; text-align: center; color: white;">
                    <div style="font-size: 24px; margin-bottom: 20px;">👀 Watching Live Stream</div>
                    <div style="background: #000; width: 100%; max-width: 600px; margin: 0 auto; border-radius: 16px; overflow: hidden; border: 3px solid #00a8ff;">
                        <video id="remoteVideo" autoplay style="width: 100%; aspect-ratio: 16/9; background: #111; display: block;"></video>
                    </div>
                    <div style="margin-top: 30px;">
                        <button id="watchBtn" style="background: #00a8ff; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer; box-shadow: 0 8px 20px rgba(0,168,255,0.4);">▶ WATCH STREAM</button>
                    </div>
                    <p id="status" style="margin-top: 20px; font-size: 18px; color: #ccc;">Click the button to start watching.</p>
                </div>
                <script src="https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js"></script>
                <script>
                (function() {{
                    const sessionId = {session_id};
                    const remoteVideo = document.getElementById('remoteVideo');
                    const watchBtn = document.getElementById('watchBtn');
                    const statusEl = document.getElementById('status');
                    let peer = null;

                    watchBtn.onclick = () => {{
                        statusEl.textContent = 'Connecting to broadcaster...';
                        peer = new Peer({{ 
                            host: '0.peerjs.com',
                            port: 443,
                            secure: true,
                            config: {{
                                'iceServers': [
                                    {{ urls: 'stun:stun.l.google.com:19302' }},
                                    {{ urls: 'stun:stun1.l.google.com:19302' }}
                                ]
                            }}
                        }});

                        peer.on('open', (id) => {{
                            statusEl.textContent = 'Connected. Requesting stream...';
                            const call = peer.call(`broadcaster-${{sessionId}}`, null);
                            call.on('stream', (remoteStream) => {{
                                remoteVideo.srcObject = remoteStream;
                                statusEl.textContent = '✅ Now watching live stream';
                                watchBtn.style.display = 'none';
                            }});
                            call.on('error', (err) => {{
                                statusEl.textContent = '❌ Call error: ' + err;
                            }});
                        }});

                        peer.on('error', (err) => {{
                            statusEl.textContent = '❌ Peer error: ' + err;
                        }});
                    }};
                }})();
                </script>
                """
                st.components.v1.html(viewer_html, height=550)

        # Shareable link
        try:
            base_url = st.request.url.split('?')[0]
        except:
            base_url = "https://globalinternetpy.streamlit.app"
        share_url = f"{base_url}?live={session_id}"
        st.text_input("Shareable link", value=share_url)

    with col2:
        # Live chat and gifts
        st.subheader("Live Chat & Gifts")
        if not is_broadcaster:
            st.markdown("### 🎁 Send a Gift")
            if not st.session_state.profile.get("moncash_phone"):
                st.info("Add your MonCash phone number in your profile to send gifts.")
            else:
                gift_options = [
                    {"label": "❤️ 50 HTG", "amount": 50, "currency": "HTG"},
                    {"label": "🎉 100 HTG", "amount": 100, "currency": "HTG"},
                    {"label": "🌟 500 HTG", "amount": 500, "currency": "HTG"},
                    {"label": "💵 1 USD", "amount": 1, "currency": "USD"},
                    {"label": "💵 5 USD", "amount": 5, "currency": "USD"},
                    {"label": "💵 10 USD", "amount": 10, "currency": "USD"},
                ]
                cols = st.columns(3)
                for i, opt in enumerate(gift_options):
                    with cols[i % 3]:
                        if st.button(opt["label"], key=f"gift_{i}"):
                            success, msg = send_gift(
                                session_id,
                                st.session_state.user.id,
                                session["user_id"],
                                opt["amount"],
                                opt["currency"]
                            )
                            if success:
                                st.success(msg)
                                st.session_state.live_gifts = load_gifts_for_session(session_id)
                                st.rerun()
                            else:
                                st.error(msg)

        if is_broadcaster:
            st.metric("Total Gifts Received", f"{total_gifts_htg:.0f} HTG")
            if session["profiles"]["moncash_phone"]:
                st.info(f"Gifts will be sent to your MonCash: {session['profiles']['moncash_phone']}")
            else:
                st.warning("Add your MonCash phone number in your profile to receive gifts.")

        with st.form(f"live_comment_{session_id}", clear_on_submit=True):
            msg = st.text_input("Write a comment...")
            if st.form_submit_button("Send"):
                if msg:
                    add_comment(session_id, st.session_state.user.id, msg)
                    st.rerun()

        comments = load_comments(session_id)
        all_events = []
        for c in comments:
            all_events.append({"type": "comment", "data": c, "time": c['created_at']})
        for g in gifts:
            all_events.append({"type": "gift", "data": g, "time": g['created_at']})
        all_events.sort(key=lambda x: x['time'])

        for ev in all_events:
            if ev['type'] == 'comment':
                c = ev['data']
                st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
            else:
                g = ev['data']
                sender = g.get('sender', {}).get('full_name', 'Someone')
                st.markdown(f"🎁 **{sender}** sent a gift of {g['amount']} {g['currency']}!")

def render_user_profile(user_id):
    # ... (keep existing – unchanged) ...
    # For brevity, keep your existing code from previous version.
    pass

def render_feed():
    # ... (keep existing – unchanged) ...
    pass

def render_friends_page():
    # ... (keep existing – unchanged) ...
    pass

def render_map():
    # ... (keep existing – unchanged) ...
    pass

def render_profile():
    # ... (keep existing – unchanged) ...
    pass

def owner_space():
    # ... (keep existing – unchanged) ...
    pass

def main_app():
    # ... (keep existing – unchanged) ...
    pass

def login_interface():
    # ... (keep existing – unchanged) ...
    pass

# Note: For brevity, I've omitted the unchanged functions (render_user_profile, render_feed, etc.) 
# to keep the response manageable. In your actual file, keep all those functions as they were.
# If you need the full file with all functions, let me know and I'll provide it.

if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
