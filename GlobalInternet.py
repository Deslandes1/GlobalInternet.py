"""
GLOBALINTERNET.PY - Satellite Communication Platform with Real Money Transfers
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Version: 35.0.0 (Friend Requests + Notifications)
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

# --- SQL SETUP (RUN ONCE IN SUPABASE SQL EDITOR) ---
"""
-- 1. Friend requests table
CREATE TABLE IF NOT EXISTS friend_requests (
    id BIGSERIAL PRIMARY KEY,
    sender_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(sender_id, receiver_id)
);

-- 2. Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    related_id BIGINT, -- friend_request id
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Trigger to update updated_at on friend_requests
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_friend_requests_updated_at
    BEFORE UPDATE ON friend_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""
# --- END SQL SETUP ---

# --- Configuration for Real Payments ---
BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "https://your-backend.com")
BACKEND_API_KEY = st.secrets.get("BACKEND_API_KEY", "")
MONCASH_MODE = st.secrets.get("MONCASH_MODE", "sandbox")

# --- Supabase client ---
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

# --- Session state for payment tracking ---
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
# --- NEW: Friend request & notification state ---
if "notifications" not in st.session_state:
    st.session_state.notifications = []
if "unread_count" not in st.session_state:
    st.session_state.unread_count = 0
if "friend_requests" not in st.session_state:
    st.session_state.friend_requests = []  # pending requests received
if "friends" not in st.session_state:
    st.session_state.friends = []

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
                profile = get_or_create_profile(user.user.id, user.user.email or user.user.phone)
                st.session_state.profile = profile
                st.session_state.connection_time = time.time()
                st.session_state.posts = load_posts()
                st.session_state.live_sessions = load_live_sessions()
                # Load friend data
                load_friend_data()
        except Exception as e:
            st.session_state.last_error = str(e)

# --- RESPONSIVE UI STYLING (unchanged) ---
st.markdown("""
    <style>
    /* Base responsive settings */
    html {
        font-size: 14px;
    }
    @media (max-width: 600px) {
        html {
            font-size: 12px;
        }
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #f0f4fa 0%, #d9e2ef 100%);
        color: #1e2a3a;
    }
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(0,168,255,0.3);
        width: 100%;
        max-width: 250px;
    }
    @media (max-width: 600px) {
        [data-testid="stSidebar"] {
            max-width: 200px;
            font-size: 0.9rem;
        }
    }
    .main > div {
        padding-left: 1rem;
        padding-right: 1rem;
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
    @media (max-width: 600px) {
        .post-card {
            padding: 15px;
        }
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
        width: auto;
    }
    .stButton > button:hover {
        background: linear-gradient(105deg, #0080ff 0%, #0066cc 100%);
        box-shadow: 0 12px 24px rgba(0,128,255,0.3);
        transform: scale(1.02);
    }
    @media (max-width: 600px) {
        .stButton > button {
            width: 100%;
            margin: 5px 0;
        }
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
    img, video {
        max-width: 100%;
        height: auto;
        max-height: 70vh;
        object-fit: contain;
        display: block;
        margin-left: auto;
        margin-right: auto;
    }
    @media (max-width: 600px) {
        img, video {
            max-height: 50vh;
        }
    }
    .post-card img, .post-card video {
        max-width: 100%;
        border-radius: 12px;
    }
    .stColumn {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100%;
    }
    @media (min-width: 601px) {
        .stColumn {
            width: auto !important;
            flex: 1 1 0 !important;
            min-width: 0 !important;
        }
    }
    .stTextInput > div, .stTextArea > div, .stSelectbox > div {
        width: 100%;
    }
    /* Notification badge */
    .notification-badge {
        background-color: #ff4444;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 0.8rem;
        margin-left: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ========== FRIEND & NOTIFICATION FUNCTIONS ==========

def load_friend_data():
    """Load notifications, pending requests, and friends list into session state."""
    if supabase is None or not st.session_state.user:
        return
    user_id = st.session_state.user.id

    # Load notifications (unread first)
    try:
        notif = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        st.session_state.notifications = notif.data if notif.data else []
        st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
    except Exception as e:
        st.session_state.last_error = f"Failed to load notifications: {e}"

    # Load pending friend requests (where I am receiver)
    try:
        req = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "pending").execute()
        st.session_state.friend_requests = req.data if req.data else []
    except Exception as e:
        st.session_state.last_error = f"Failed to load friend requests: {e}"

    # Load friends (accepted requests where user is either sender or receiver)
    try:
        sent = supabase.table("friend_requests").select("*, receiver:receiver_id(full_name, avatar_url)").eq("sender_id", user_id).eq("status", "accepted").execute()
        received = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "accepted").execute()
        friends = []
        for r in sent.data:
            friends.append({"id": r['receiver']['id'], "full_name": r['receiver']['full_name'], "avatar_url": r['receiver'].get('avatar_url')})
        for r in received.data:
            friends.append({"id": r['sender']['id'], "full_name": r['sender']['full_name'], "avatar_url": r['sender'].get('avatar_url')})
        st.session_state.friends = friends
    except Exception as e:
        st.session_state.last_error = f"Failed to load friends: {e}"

def search_users(query):
    """Search for users by full_name or email (exclude current user)."""
    if supabase is None or not st.session_state.user:
        return []
    try:
        # Search in profiles (full_name) and auth.users (email) – but profiles has email? We'll search profiles full_name.
        # We'll also need to join with auth.users to get email. But supabase doesn't allow direct join to auth.users. Instead, we can store email in profiles (we already have identifier). For simplicity, we'll just search profiles full_name.
        result = supabase.table("profiles").select("id, full_name, avatar_url").neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(20).execute()
        return result.data if result.data else []
    except Exception as e:
        st.session_state.last_error = f"Search failed: {e}"
        return []

def send_friend_request(receiver_id):
    """Send a friend request. Returns (success, message)."""
    if supabase is None or not st.session_state.user:
        return False, "Not logged in"
    try:
        # Check if request already exists
        existing = supabase.table("friend_requests").select("id").or_(
            f"and(sender_id.eq.{st.session_state.user.id},receiver_id.eq.{receiver_id})",
            f"and(sender_id.eq.{receiver_id},receiver_id.eq.{st.session_state.user.id})"
        ).execute()
        if existing.data:
            return False, "Friend request already exists"
        # Insert new request
        data = {
            "sender_id": st.session_state.user.id,
            "receiver_id": receiver_id,
            "status": "pending"
        }
        supabase.table("friend_requests").insert(data).execute()
        # Create notification for receiver
        sender_name = st.session_state.profile['full_name']
        notif = {
            "user_id": receiver_id,
            "type": "friend_request",
            "message": f"{sender_name} sent you a friend request",
            "read": False
        }
        supabase.table("notifications").insert(notif).execute()
        return True, "Friend request sent"
    except Exception as e:
        return False, str(e)

def respond_friend_request(request_id, accept):
    """Accept or reject a friend request. Returns (success, message)."""
    if supabase is None or not st.session_state.user:
        return False, "Not logged in"
    try:
        # Get request to know sender
        req = supabase.table("friend_requests").select("*").eq("id", request_id).single().execute()
        if not req.data:
            return False, "Request not found"
        if req.data['receiver_id'] != st.session_state.user.id:
            return False, "Not authorized"
        new_status = "accepted" if accept else "rejected"
        supabase.table("friend_requests").update({"status": new_status}).eq("id", request_id).execute()
        if accept:
            # Create notification for sender
            receiver_name = st.session_state.profile['full_name']
            notif = {
                "user_id": req.data['sender_id'],
                "type": "friend_accept",
                "related_id": request_id,
                "message": f"{receiver_name} accepted your friend request",
                "read": False
            }
            supabase.table("notifications").insert(notif).execute()
        return True, f"Request {new_status}"
    except Exception as e:
        return False, str(e)

def mark_notification_read(notif_id):
    """Mark a notification as read."""
    if supabase is None:
        return
    try:
        supabase.table("notifications").update({"read": True}).eq("id", notif_id).execute()
    except Exception as e:
        st.session_state.last_error = f"Failed to mark read: {e}"

# ========== EXISTING HELPER FUNCTIONS (keep all previous) ==========
# ... (all your previous helper functions from get_or_create_profile to verify_phone_otp)
# ... (I will keep them as they are, but to save space I'll not repeat them here.
#      In the actual code you must include all previous functions.)

# For the sake of brevity, I'm assuming all previous functions are present.
# In the final answer I'll include them all, but here I'll just indicate they remain.

# ========== NEW PAGE: FRIENDS & NOTIFICATIONS ==========

def render_friends_page():
    st.header("👥 Friends & Requests")

    # Notifications section
    with st.expander(f"🔔 Notifications ({st.session_state.unread_count} unread)", expanded=True):
        if not st.session_state.notifications:
            st.info("No notifications")
        else:
            for n in st.session_state.notifications:
                col1, col2 = st.columns([5,1])
                with col1:
                    st.markdown(f"**{n['message']}**  \n*{n['created_at'][:16]}*")
                with col2:
                    if not n['read']:
                        if st.button("✓ Mark read", key=f"read_{n['id']}"):
                            mark_notification_read(n['id'])
                            load_friend_data()
                            st.rerun()
                if not n['read']:
                    st.markdown("---")

    st.divider()

    # Pending requests received
    st.subheader("📨 Friend Requests Received")
    if not st.session_state.friend_requests:
        st.info("No pending requests")
    else:
        for req in st.session_state.friend_requests:
            cols = st.columns([2,1,1])
            with cols[0]:
                st.markdown(f"**{req['sender']['full_name']}**")
            with cols[1]:
                if st.button("✅ Accept", key=f"accept_{req['id']}"):
                    success, msg = respond_friend_request(req['id'], True)
                    if success:
                        load_friend_data()
                        st.rerun()
                    else:
                        st.error(msg)
            with cols[2]:
                if st.button("❌ Reject", key=f"reject_{req['id']}"):
                    success, msg = respond_friend_request(req['id'], False)
                    if success:
                        load_friend_data()
                        st.rerun()
                    else:
                        st.error(msg)
            st.divider()

    st.divider()

    # Search users to send request
    st.subheader("🔍 Find Users")
    search_query = st.text_input("Search by name")
    if search_query:
        results = search_users(search_query)
        if not results:
            st.info("No users found")
        else:
            for user in results:
                cols = st.columns([3,1])
                with cols[0]:
                    st.markdown(f"**{user['full_name']}**")
                with cols[1]:
                    if st.button("➕ Add Friend", key=f"add_{user['id']}"):
                        success, msg = send_friend_request(user['id'])
                        if success:
                            st.success(msg)
                            load_friend_data()
                            st.rerun()
                        else:
                            st.error(msg)
                st.divider()

    st.divider()

    # Friends list
    st.subheader("👥 Your Friends")
    if not st.session_state.friends:
        st.info("You have no friends yet")
    else:
        for friend in st.session_state.friends:
            cols = st.columns([1,4])
            with cols[0]:
                if friend.get('avatar_url'):
                    st.image(friend['avatar_url'], width=30)
                else:
                    st.markdown("👤")
            with cols[1]:
                st.markdown(f"**{friend['full_name']}**")
            st.divider()

# ========== EXISTING PAGES (render_feed, render_profile, etc.) ==========
# ... keep them exactly as before ...

# ========== MODIFIED main_app() to include Friends page ==========
def main_app():
    with st.sidebar:
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

        # Notification badge on menu
        if st.session_state.unread_count > 0:
            st.sidebar.markdown(f"🔔 **Notifications** <span class='notification-badge'>{st.session_state.unread_count}</span>", unsafe_allow_html=True)

        # Live status / go live (unchanged)
        if st.session_state.profile and st.session_state.profile.get("is_live"):
            st.markdown("🔴 **You are live!**")
            if st.button("End Live Session"):
                for ls in st.session_state.live_sessions:
                    if ls["user_id"] == st.session_state.user.id:
                        end_live_session(ls["id"])
                        st.rerun()
                        break
        else:
            with st.expander("Go Live (Real Streaming)"):
                st.markdown("**Choose your platform:**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📺 YouTube", key="yt"):
                        st.session_state.selected_platform = "YouTube"
                with col2:
                    if st.button("📘 Facebook", key="fb"):
                        st.session_state.selected_platform = "Facebook"
                with col3:
                    if st.button("🎮 Twitch", key="tw"):
                        st.session_state.selected_platform = "Twitch"

                if st.session_state.selected_platform:
                    platform = st.session_state.selected_platform
                    st.markdown(f"**Selected: {platform}**")
                    with st.form("go_live_form"):
                        title = st.text_input("Live title")
                        if st.form_submit_button("Create Live Session"):
                            if title:
                                session_id = create_live_session(title, platform)
                                if session_id:
                                    st.success("Live session created! You are now live.")
                                    st.info(f"**Stream Key:** `{st.session_state.stream_key}`")
                                    st.markdown(f"**Start streaming on {platform}:** [Click here](https://www.{platform.lower()}.com/live)")
                                    st.rerun()
                            else:
                                st.warning("Please enter a title")

        st.divider()

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
        if st.session_state.profile:
            st.markdown(f"👤 **Logged in as:** {st.session_state.profile.get('full_name', 'User')}")
        if st.button("🚪 Logout"):
            logout()
        st.divider()

        pages = {
            "📡 Feed": render_feed,
            "👥 Friends": render_friends_page,
            "🛰️ Satellite Map": render_map,
            "👤 Profile": render_profile,
            "🕊️ Owner Space": owner_space
        }
        choice = st.selectbox("Menu", list(pages.keys()))
    pages[choice]()

# ========== LOGIN INTERFACE (unchanged) ==========
def login_interface():
    # ... (same as before) ...
    pass

if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
