"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 37.0.0 (Always‑visible interactive comments)
"""
import streamlit as st

st.set_page_config(page_title="GLOBALINTERNET.PY", page_icon="🇭🇹", layout="wide")

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
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

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
    st.session_state.replying_to = {}    # dict comment_id -> bool

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
        except Exception as e:
            st.session_state.last_error = str(e)

# --- UI styling (Haitian flag + video size fix) ---
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
    /* Fix video size */
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
    /* Comment section styling */
    .comment-section {
        margin-top: 20px;
        background: rgba(255,255,255,0.5);
        padding: 15px;
        border-radius: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper functions (unchanged from previous version) ---
# (All helper functions from the previous version remain exactly the same.
#  For brevity, I'll include only the essential ones; but in the final code you should keep all.)

def get_or_create_profile(user_id, identifier):
    # ... (same as before)
    pass

def update_profile(profile_data):
    # ... (same)
    pass

def upload_avatar(user_id, image_file):
    # ... (same)
    pass

def upload_post_media(user_id, file):
    # ... (same)
    pass

def delete_post(post_id):
    # ... (same)
    pass

# --- Cached post loading ---
@st.cache_data(ttl=60, show_spinner=False)
def load_posts_cached(user_id=None):
    """Load posts (cached for 60 seconds)."""
    if supabase is None:
        return []
    try:
        select_cols = "*, profiles(full_name, avatar_url, is_live)"
        if user_id:
            # Get public posts + user's private posts
            public_resp = supabase.table("posts").select(select_cols).eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            private_resp = supabase.table("posts").select(select_cols).eq("is_public", False).eq("user_id", user_id).order("created_at", desc=True).execute()
            posts = public_resp.data + private_resp.data
            # Remove duplicates
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

        # Add reactions
        for post in posts:
            post["media_urls"] = post.get("media_urls", [])
            reactions_resp = supabase.table("reactions").select("emoji").eq("post_id", post["id"]).execute()
            counts = {}
            if reactions_resp.data:
                for r in reactions_resp.data:
                    emoji = r["emoji"]
                    counts[emoji] = counts.get(emoji, 0) + 1
            post["reactions"] = counts
            # Count comments
            comments_resp = supabase.table("comments").select("id", count="exact").eq("post_id", post["id"]).execute()
            post["comment_count"] = comments_resp.count if hasattr(comments_resp, 'count') else 0
        return posts
    except Exception as e:
        st.session_state.last_error = f"Error loading posts: {e}"
        return []

def load_posts():
    """Wrapper to load posts with current user."""
    user_id = st.session_state.user.id if st.session_state.user else None
    return load_posts_cached(user_id)

def create_post(user_id, content, media_files, is_public):
    # ... (same as before)
    pass

def toggle_reaction(post_id, user_id, emoji):
    # ... (same as before)
    pass

def share_post(original_post_id, user_id, is_public=True):
    # ... (same as before)
    pass

# --- Comment functions with full interactivity ---
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
        response = supabase.table("comments").select(
            "*, profiles(full_name, avatar_url)"
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

# --- Live session functions (unchanged) ---
def create_live_session(title, platform):
    # ... (same)
    pass

def update_live_stream_url(session_id, stream_url):
    # ... (same)
    pass

def end_live_session(session_id):
    # ... (same)
    pass

def load_live_sessions():
    # ... (same)
    pass

def get_live_session(session_id):
    # ... (same)
    pass

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

# --- Authentication (unchanged) ---
def sign_up_email(email, password, full_name):
    # ... (same)
    pass

def log_in_email(email, password, remember=False):
    # ... (same)
    pass

def reset_password_email(email):
    # ... (same)
    pass

def format_phone(phone: str) -> str:
    # ... (same)
    pass

def send_phone_otp(raw_phone):
    # ... (same)
    pass

def verify_phone_otp(raw_phone, token, remember=False):
    # ... (same)
    pass

def logout():
    # ... (same)
    pass

# --- Live page (simplified) ---
def render_live_page(session_id):
    # ... (same as before)
    pass

# --- Feed with always-visible comments ---
def render_feed():
    st.header("🌐 Collaboration Feed")

    if st.session_state.last_error:
        st.markdown(f"<div class='error-box'><b>❌ Error:</b>\n{st.session_state.last_error}</div>", unsafe_allow_html=True)
        if st.button("Clear error"):
            st.session_state.last_error = None
            st.rerun()

    # Check if viewing a live session
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

    # --- Post composer ---
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

    # --- Live sessions banner ---
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

    # --- Delete confirmation ---
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

    # --- Posts ---
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

                # --- Always-visible comment section ---
                st.markdown("<div class='comment-section'>", unsafe_allow_html=True)
                st.markdown("#### Comments")

                # New comment form
                with st.form(key=f"new_comment_{post['id']}", clear_on_submit=True):
                    msg = st.text_input("Write a comment...")
                    if st.form_submit_button("Post Comment"):
                        if msg:
                            add_comment(post['id'], st.session_state.user.id, msg)
                            st.rerun()

                # Load and display comments
                comments = load_comments(post['id'])
                # Build comment tree: top-level comments and their replies
                top_level = [c for c in comments if not c.get('parent_id')]
                replies = {}
                for c in comments:
                    if c.get('parent_id'):
                        replies.setdefault(c['parent_id'], []).append(c)

                for c in top_level:
                    # Top-level comment
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

                    # Reply form if active
                    if st.session_state.replying_to.get(c['id'], False):
                        with st.form(key=f"reply_form_{c['id']}"):
                            reply = st.text_input("Your reply")
                            if st.form_submit_button("Post Reply"):
                                if reply:
                                    add_comment(post['id'], st.session_state.user.id, reply, parent_id=c['id'])
                                    st.session_state.replying_to[c['id']] = False
                                    st.rerun()

                    # Show replies
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
                            # Optionally allow replying to replies (could add deeper nesting)
                            pass
                        with colr4:
                            if st.session_state.user and r['user_id'] == st.session_state.user.id:
                                if st.button("🗑️", key=f"del_comment_{r['id']}"):
                                    delete_comment(r['id'])
                                    st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)  # end comment-section
                st.divider()

# --- Profile, Map, Owner Space (unchanged) ---
def render_profile():
    # ... (same as before)
    pass

def render_map():
    # ... (same as before)
    pass

def owner_space():
    # ... (same as before)
    pass

def main_app():
    # ... (same as before)
    pass

def login_interface():
    # ... (same as before)
    pass

if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
