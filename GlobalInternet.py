"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 45.0.0 (Complete with UNIBANK account display)
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
import urllib.parse
import json
import os
import random
import string
import traceback

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

# --- Session state ---
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
                load_friend_data()
                st.session_state.notifications = load_notifications(user.user.id)
                st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
        except Exception as e:
            st.session_state.last_error = str(e)

# --- UI styling (Haitian flag + fixed contrast) ---
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
    </style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========

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
                "is_live": False
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
        st.session_state.last_error = f"Avatar upload failed: {e}"
        return None

def upload_post_media(user_id, file):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
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
        st.session_state.last_error = f"Media upload failed: {e}"
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

# --- Post functions (with explicit foreign keys to avoid ambiguity) ---
@st.cache_data(ttl=60, show_spinner=False)
def load_posts_cached(user_id=None):
    """Load posts (cached for 60 seconds)."""
    if supabase is None:
        return []
    try:
        # Explicitly specify the foreign key to avoid ambiguity
        select_cols = "*, profiles!posts_user_id_fkey(full_name, avatar_url, is_live)"
        if user_id:
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

def create_post(user_id, content, media_files, is_public):
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

# --- Comment functions (with explicit foreign keys) ---
def add_comment(post_id, user_id, content, parent_id=None):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
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
        # Explicit foreign key for comments -> profiles
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

# --- Live session functions (with explicit foreign keys) ---
def create_live_session(title, platform):
    if supabase is None or st.session_state.user is None:
        st.session_state.last_error = "Cannot start live session."
        return None
    try:
        active = supabase.table("live_sessions").select("id").eq("user_id", st.session_state.user.id).eq("is_live", True).execute()
        if active.data:
            st.warning("You already have an active live session. End it first.")
            return None

        stream_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
        session_data = {
            "user_id": st.session_state.user.id,
            "title": title,
            "is_live": True,
            "started_at": datetime.now().isoformat(),
            "stream_url": None,
            "platform": platform,
            "stream_key": stream_key
        }
        result = supabase.table("live_sessions").insert(session_data).execute()
        if result.data:
            supabase.table("profiles").update({"is_live": True}).eq("id", st.session_state.user.id).execute()
            st.session_state.profile["is_live"] = True
            st.session_state.live_sessions = load_live_sessions()
            st.session_state.stream_key = stream_key
            st.session_state.selected_platform = platform
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
        response = supabase.table("live_sessions").select(
            "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url)"
        ).eq("is_live", True).order("started_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.session_state.last_error = f"Error loading live sessions: {e}"
        return []

def get_live_session(session_id):
    if supabase is None:
        return None
    try:
        response = supabase.table("live_sessions").select(
            "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url)"
        ).eq("id", session_id).single().execute()
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
            profile = get_or_create_profile(user.user.id, email)
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.session_state.posts = load_posts()
            st.session_state.live_sessions = load_live_sessions()
            load_friend_data()
            st.session_state.notifications = load_notifications(user.user.id)
            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
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
    st.session_state.owner_space_access = False
    st.session_state.phone_otp_sent = False
    st.session_state.temp_phone = ""
    st.session_state.viewing_live = None
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
        existing = supabase.table("friend_requests").select("id").or_(
            f"and(sender_id.eq.{sender_id},receiver_id.eq.{receiver_id})",
            f"and(sender_id.eq.{receiver_id},receiver_id.eq.{sender_id})"
        ).execute()
        if existing.data:
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
        return
    user_id = st.session_state.user.id
    pending = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "pending").execute()
    st.session_state.friend_requests = pending.data if pending.data else []
    sent = supabase.table("friend_requests").select("*, receiver:receiver_id(full_name, avatar_url)").eq("sender_id", user_id).eq("status", "accepted").execute()
    received = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "accepted").execute()
    friends = []
    for r in sent.data:
        friends.append({"id": r["receiver"]["id"], "full_name": r["receiver"]["full_name"], "avatar_url": r["receiver"].get("avatar_url")})
    for r in received.data:
        friends.append({"id": r["sender"]["id"], "full_name": r["sender"]["full_name"], "avatar_url": r["sender"].get("avatar_url")})
    st.session_state.friends = friends

def search_users(query):
    if supabase is None or not st.session_state.user:
        return []
    try:
        result = supabase.table("profiles").select("id, full_name, avatar_url").neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(50).execute()
        return result.data
    except Exception as e:
        st.session_state.last_error = f"Search failed: {e}"
        return []

def send_message(sender_id, receiver_id, content):
    if supabase is None:
        return False
    try:
        supabase.table("messages").insert({
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "read": False,
            "created_at": datetime.now().isoformat()
        }).execute()
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
        msgs = supabase.table("messages").select("*").or_(
            f"and(sender_id.eq.{user_id},receiver_id.eq.{other_id})",
            f"and(sender_id.eq.{other_id},receiver_id.eq.{user_id})"
        ).order("created_at").execute()
        supabase.table("messages").update({"read": True}).eq("sender_id", other_id).eq("receiver_id", user_id).execute()
        return msgs.data
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

# ========== PAGE RENDERING FUNCTIONS ==========

def render_live_page(session_id):
    session = get_live_session(session_id)
    if not session or not session.get("is_live"):
        st.error("This live session has ended or does not exist.")
        if st.button("Back to Feed"):
            st.session_state.viewing_live = None
            st.rerun()
        return

    st.header(f"🔴 LIVE: {session['title']}")
    col1, col2 = st.columns([2, 1])

    with col1:
        stream_url = session.get("stream_url")
        platform = session.get("platform")
        is_broadcaster = st.session_state.user and session["user_id"] == st.session_state.user.id

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
            else:
                st.video(stream_url)
        else:
            st.info("The streamer has not provided a video URL yet.")

        try:
            base_url = st.request.url.split('?')[0]
        except:
            base_url = "https://globalinternetpy.streamlit.app"
        share_url = f"{base_url}?live={session_id}"
        st.text_input("Shareable link", value=share_url)

    with col2:
        st.subheader("Live Chat")
        with st.form(f"live_comment_{session_id}", clear_on_submit=True):
            msg = st.text_input("Write a comment...")
            if st.form_submit_button("Send"):
                if msg:
                    add_comment(session_id, st.session_state.user.id, msg)
                    st.rerun()
        comments = load_comments(session_id)
        for c in comments:
            st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")

def render_feed():
    st.header("🌐 Collaboration Feed")

    if st.session_state.last_error:
        st.markdown(f"<div class='error-box'><b>❌ Error:</b>\n{st.session_state.last_error}</div>", unsafe_allow_html=True)
        if st.button("Clear error"):
            st.session_state.last_error = None
            st.rerun()

    try:
        params = st.query_params
    except AttributeError:
        params = st.experimental_get_query_params()
    if "live" in params and params["live"]:
        try:
            session_id = int(params["live"][0] if isinstance(params["live"], list) else params["live"])
            st.session_state.viewing_live = session_id
        except:
            pass
    if st.session_state.viewing_live:
        render_live_page(st.session_state.viewing_live)
        return

    # Post composer
    st.markdown("### Create a post")
    with st.form("new_post", clear_on_submit=True):
        col_avatar, col_input = st.columns([1, 8])
        with col_avatar:
            if st.session_state.profile and st.session_state.profile.get("avatar_url"):
                st.image(st.session_state.profile["avatar_url"], width=50)
            else:
                st.markdown("👤", unsafe_allow_html=True)
        with col_input:
            content = st.text_area(
                "What's on your mind?",
                height=100,
                placeholder="Share your thoughts, ideas, or media...",
                label_visibility="collapsed"
            )
        media_files = st.file_uploader(
            "Add images or videos (optional)",
            type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"],
            accept_multiple_files=True
        )
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            visibility = st.radio("Visibility", ["Public", "Private"], horizontal=True, index=0)
            is_public = (visibility == "Public")
        with col3:
            posted = st.form_submit_button("🚀 Post", use_container_width=True)

        if posted:
            if not content and not media_files:
                st.warning("Please add a caption or media.")
            else:
                if create_post(st.session_state.user.id, content, media_files, is_public):
                    st.rerun()
    st.divider()

    # Live sessions banner
    active_lives = st.session_state.live_sessions
    if active_lives:
        st.markdown("### 🔴 Live Now")
        for live in active_lives:
            with st.container():
                col_a, col_b = st.columns([1,4])
                with col_a:
                    if live["profiles"]["avatar_url"]:
                        st.image(live["profiles"]["avatar_url"], width=40)
                    else:
                        st.markdown("👤")
                with col_b:
                    st.markdown(f"**{live['profiles']['full_name']}** is live: **{live['title']}**")
                    if st.button(f"Join Live", key=f"join_{live['id']}"):
                        st.session_state.viewing_live = live["id"]
                        st.rerun()
                st.divider()
    st.divider()

    # Delete confirmation
    if st.session_state.delete_confirm:
        post_id, _ = st.session_state.delete_confirm
        st.warning("Are you sure you want to delete this post?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete"):
                delete_post(post_id)
                st.cache_data.clear()
                st.session_state.posts = load_posts()
                st.session_state.delete_confirm = None
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.delete_confirm = None
                st.rerun()
        st.divider()

    # Posts
    if not st.session_state.posts:
        st.info("No posts yet. Be the first to create one!")
    else:
        for post in st.session_state.posts:
            with st.container():
                # Post header
                col_a, col_b, col_c, col_d = st.columns([1, 5, 2, 1])
                with col_a:
                    avatar = post.get("profiles", {}).get("avatar_url")
                    if avatar:
                        st.image(avatar, width=40)
                    else:
                        st.markdown("👤")
                with col_b:
                    name = post['profiles']['full_name']
                    if post.get("profiles", {}).get("is_live"):
                        st.markdown(f"**{name}** <span class='green-dot'></span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{name}**")
                    if not post.get("is_public", True):
                        st.markdown("<span class='private-badge'>Private</span>", unsafe_allow_html=True)
                with col_c:
                    st.caption(post['created_at'][:16])
                with col_d:
                    if st.session_state.user and post['user_id'] == st.session_state.user.id:
                        if st.button("🗑️", key=f"del_post_{post['id']}"):
                            st.session_state.delete_confirm = (post['id'], post['content'][:30])
                            st.rerun()

                # Post content
                if post['content']:
                    st.markdown(f"<div class='post-card'>{post['content']}</div>", unsafe_allow_html=True)

                # Media
                media_urls = post.get("media_urls", [])
                if media_urls:
                    for media in media_urls:
                        if media["type"] == "image":
                            st.image(media["url"], use_column_width=True)
                        elif media["type"] == "video":
                            st.video(media["url"])

                # Reactions row
                emojis = ["👍", "👎", "❤️", "😂", "😮", "😢", "👏"]
                cols = st.columns(len(emojis) + 2)
                for i, emoji in enumerate(emojis):
                    with cols[i]:
                        count = post.get("reactions", {}).get(emoji, 0)
                        btn_label = f"{emoji} {count}" if count > 0 else emoji
                        if st.button(btn_label, key=f"react_{post['id']}_{emoji}"):
                            toggle_reaction(post['id'], st.session_state.user.id, emoji)
                            st.rerun()

                with cols[len(emojis)]:
                    st.markdown(f"💬 {post.get('comment_count',0)} Comments")
                with cols[len(emojis)+1]:
                    if st.button(f"🔄 {post['shares_count']}", key=f"share_{post['id']}"):
                        share_post(post['id'], st.session_state.user.id, is_public=True)
                        st.rerun()

                # --- Comment section (always visible) ---
                st.markdown("<div class='comment-section'>", unsafe_allow_html=True)
                st.markdown("#### Comments")

                with st.form(key=f"new_comment_{post['id']}", clear_on_submit=True):
                    msg = st.text_input("Write a comment...")
                    if st.form_submit_button("Post Comment"):
                        if msg:
                            add_comment(post['id'], st.session_state.user.id, msg)
                            st.rerun()

                comments = load_comments(post['id'])
                top_level = [c for c in comments if not c.get('parent_id')]
                replies = {}
                for c in comments:
                    if c.get('parent_id'):
                        replies.setdefault(c['parent_id'], []).append(c)

                for c in top_level:
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                    with col1:
                        st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
                        st.markdown(f"<span class='comment-meta'>{c['created_at'][:16]}</span>", unsafe_allow_html=True)
                    with col2:
                        if st.button(f"👍 {c.get('likes',0)}", key=f"like_{c['id']}"):
                            like_comment(c['id'], increment=True)
                            st.rerun()
                    with col3:
                        if st.button("💬 Reply", key=f"reply_{c['id']}"):
                            st.session_state.replying_to[c['id']] = not st.session_state.replying_to.get(c['id'], False)
                            st.rerun()
                    with col4:
                        if st.session_state.user and c['user_id'] == st.session_state.user.id:
                            if st.button("🗑️", key=f"del_comment_{c['id']}"):
                                delete_comment(c['id'])
                                st.rerun()

                    if st.session_state.replying_to.get(c['id'], False):
                        with st.form(key=f"reply_form_{c['id']}"):
                            reply = st.text_input("Your reply")
                            if st.form_submit_button("Post Reply"):
                                if reply:
                                    add_comment(post['id'], st.session_state.user.id, reply, parent_id=c['id'])
                                    st.session_state.replying_to[c['id']] = False
                                    st.rerun()

                    for r in replies.get(c['id'], []):
                        st.markdown("<div class='comment-indent'>", unsafe_allow_html=True)
                        colr1, colr2, colr3, colr4 = st.columns([4, 1, 1, 1])
                        with colr1:
                            st.markdown(f"**{r['profiles']['full_name']}**: {r['content']}")
                            st.markdown(f"<span class='comment-meta'>{r['created_at'][:16]}</span>", unsafe_allow_html=True)
                        with colr2:
                            if st.button(f"👍 {r.get('likes',0)}", key=f"like_{r['id']}"):
                                like_comment(r['id'], increment=True)
                                st.rerun()
                        with colr3:
                            pass
                        with colr4:
                            if st.session_state.user and r['user_id'] == st.session_state.user.id:
                                if st.button("🗑️", key=f"del_comment_{r['id']}"):
                                    delete_comment(r['id'])
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)
                st.divider()

def render_friends_page():
    st.header("👥 Friends & Chat")

    st.markdown(f"<div class='friend-count'>You have {len(st.session_state.friends)} friends</div>", unsafe_allow_html=True)
    st.divider()

    # Notifications
    with st.expander(f"🔔 Notifications ({st.session_state.unread_count} unread)", expanded=True):
        if not st.session_state.notifications:
            st.info("No notifications")
        else:
            for n in st.session_state.notifications:
                cols = st.columns([5,1])
                with cols[0]:
                    st.markdown(f"**{n['message']}**  \n*{n['created_at'][:16]}*")
                with cols[1]:
                    if not n['read']:
                        if st.button("✓", key=f"read_{n['id']}"):
                            mark_notification_read(n['id'])
                            st.session_state.notifications = load_notifications(st.session_state.user.id)
                            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
                            st.rerun()
                st.divider()

    # Pending friend requests
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
                        st.session_state.notifications = load_notifications(st.session_state.user.id)
                        st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
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

    # Find users
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
                        success, msg = send_friend_request(st.session_state.user.id, user['id'])
                        if success:
                            st.success(msg)
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
            cols = st.columns([1,4,1,1])
            with cols[0]:
                if friend.get('avatar_url'):
                    st.image(friend['avatar_url'], width=30)
                else:
                    st.markdown("👤")
            with cols[1]:
                st.markdown(f"**{friend['full_name']}**")
            with cols[2]:
                if st.button("💬 Chat", key=f"chat_{friend['id']}"):
                    st.session_state.selected_chat = friend['id']
                    st.rerun()
            with cols[3]:
                if st.button("📞 Call", key=f"call_{friend['id']}"):
                    room = hashlib.md5(f"{st.session_state.user.id}_{friend['id']}_{time.time()}".encode()).hexdigest()[:10]
                    send_message(st.session_state.user.id, friend['id'], f"📞 Join my call: room={room}")
                    start_call(room)
                    st.rerun()
            st.divider()

    # Private Chat Section
    if st.session_state.selected_chat:
        st.subheader("💬 Private Chat")
        other_id = st.session_state.selected_chat
        other = supabase.table("profiles").select("full_name").eq("id", other_id).single().execute()
        other_name = other.data["full_name"] if other.data else "User"
        st.write(f"Chat with **{other_name}**")

        messages = load_messages(st.session_state.user.id, other_id)
        for msg in messages:
            if msg["sender_id"] == st.session_state.user.id:
                st.markdown(f"<div style='text-align:right; background:#e0f7fa; padding:5px; border-radius:10px; margin:5px;'><b>You:</b> {msg['content']}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; background:#f1f8e9; padding:5px; border-radius:10px; margin:5px;'><b>{other_name}:</b> {msg['content']}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)

        with st.form("send_message", clear_on_submit=True):
            msg_content = st.text_input("Type a message...")
            if st.form_submit_button("Send"):
                if msg_content:
                    send_message(st.session_state.user.id, other_id, msg_content)
                    st.rerun()
        if st.button("Close chat"):
            st.session_state.selected_chat = None
            st.rerun()
        st.divider()

    # Call section
    if st.session_state.in_call and st.session_state.call_room:
        st.subheader("📞 Active Call")
        st.markdown(f"Room ID: `{st.session_state.call_room}`")
        st.markdown("Share this room ID with the person you want to call.")
        jitsi_url = f"https://meet.jit.si/{st.session_state.call_room}#config.startWithAudioMuted=false&config.startWithVideoMuted=false"
        st.components.v1.html(f"""
            <iframe src="{jitsi_url}" width="100%" height="500" allow="camera; microphone; fullscreen"></iframe>
        """, height=520)
        if st.button("End Call"):
            end_call()
            st.rerun()
    else:
        if st.button("Start a new call"):
            start_call()
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
    st.header("👤 My Profile")
    if st.session_state.profile is None:
        return
    profile = st.session_state.profile

    col1, col2 = st.columns([1, 2])
    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=200, caption="Profile Picture")
        else:
            st.image("https://via.placeholder.com/200", width=200, caption="No picture")
        uploaded = st.file_uploader("📸 Change picture", type=["png","jpg","jpeg"], label_visibility="collapsed")
        if uploaded:
            url = upload_avatar(st.session_state.user.id, uploaded)
            if url:
                profile["avatar_url"] = url
                update_profile(profile)
                st.rerun()

    with col2:
        with st.form("edit_profile"):
            st.markdown("#### Account Information")
            full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
            bio = st.text_area("Bio", value=profile.get("bio", ""), height=100)
            location = st.text_input("Location", value=profile.get("location", ""))
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                profile.update({"full_name": full_name, "bio": bio, "location": location})
                if update_profile(profile):
                    st.success("Profile updated successfully!")
                    st.rerun()

    st.divider()
    cola, colb, colc, cold = st.columns(4)
    with cola:
        st.metric("Posts", len(st.session_state.posts))
    with colb:
        st.metric("Connections", profile.get("connections", 0))
    with colc:
        st.metric("Verified", "✅" if profile.get("verified", False) else "❌")
    with cold:
        st.metric("Member since", profile.get("join_date", "2024")[:10])

def owner_space():
    st.header("🕊️ Owner Space (Private)")
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

    st.subheader("🔐 Owner's Dashboard")
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
    st.divider()

    st.markdown("### 🔑 Your Private Credentials")
    st.markdown(f"- **CIN Number:** `{OWNER_CIN}`")
    st.markdown(f"- **MonCash Business:** `{MONCASH_NUM}`")
    st.markdown(f"- **UNIBANK US Money Account:** `{UNIBANK_ACCOUNT}`")
    st.markdown(f"- **OwnerSpace Password:** `{OWNSPACE_PASSWORD}`")

    if st.button("Logout from Owner Space"):
        st.session_state.owner_space_access = False
        st.rerun()

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

        if st.session_state.unread_count > 0:
            st.sidebar.markdown(f"🔔 **Notifications** <span class='notification-badge'>({st.session_state.unread_count})</span>", unsafe_allow_html=True)

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
            "👥 Friends & Chat": render_friends_page,
            "🛰️ Satellite Map": render_map,
            "👤 Profile": render_profile,
            "🕊️ Owner Space": owner_space
        }
        choice = st.selectbox("Menu", list(pages.keys()))
    pages[choice]()

def login_interface():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center;'><span class='haiti-symbol' style='font-size:6rem;'>🇭🇹</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #0a2a44;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name' style='font-size:1.8rem;'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators' style='font-size:1rem;'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes · Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        auth_method = st.radio("Choose method", ["Email", "Phone (OTP)"], horizontal=True)

        if auth_method == "Email":
            tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Sign Up", "🔐 Forgot Password"])
            with tab1:
                with st.form("login_email"):
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    remember = st.checkbox("Remember me (stay logged in)")
                    if st.form_submit_button("🚀 Login", use_container_width=True):
                        if email and password:
                            log_in_email(email, password, remember)
                        else:
                            st.warning("Please enter email and password")
            with tab2:
                with st.form("signup_email"):
                    full_name = st.text_input("Full Name")
                    email = st.text_input("Email")
                    password = st.text_input("Password", type="password")
                    if st.form_submit_button("📝 Sign Up", use_container_width=True):
                        if full_name and email and password:
                            sign_up_email(email, password, full_name)
                        else:
                            st.warning("Please fill all fields")
            with tab3:
                with st.form("reset_email"):
                    reset_email = st.text_input("Enter your email address")
                    if st.form_submit_button("Send Reset Link", use_container_width=True):
                        if reset_email:
                            reset_password_email(reset_email)
                        else:
                            st.warning("Please enter your email")
        else:
            st.info("Phone users: You will receive a 6‑digit OTP each time you log in.")
            if not st.session_state.phone_otp_sent:
                with st.form("phone_request"):
                    phone = st.text_input("Phone number (digits only, e.g., 50947385663)")
                    remember = st.checkbox("Remember me (stay logged in)")
                    if st.form_submit_button("📲 Send OTP", use_container_width=True):
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
                    otp = st.text_input("Enter 6-digit OTP code")
                    if st.form_submit_button("✅ Verify & Login", use_container_width=True):
                        if otp:
                            remember = st.session_state.get("phone_remember", False)
                            verify_phone_otp(st.session_state.temp_phone, otp, remember)
                        else:
                            st.warning("Please enter the OTP")
                if st.button("← Back / Resend OTP"):
                    st.session_state.phone_otp_sent = False
                    st.session_state.temp_phone = ""
                    st.rerun()

if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
