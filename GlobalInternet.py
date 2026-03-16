"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 31.0.0 (Handles missing reactions table gracefully)
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

# --- Schema detection ---
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

# --- Check if post_media bucket exists and is accessible ---
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
if MEDIA_URLS_EXISTS and not POST_MEDIA_BUCKET_OK:
    st.warning("⚠️ 'post_media' bucket is not accessible. Media uploads will fail. Please create the bucket and set it to public.")

# --- Check if reactions table exists ---
@st.cache_resource
def check_reactions_table():
    if supabase is None:
        return False
    try:
        supabase.table("reactions").select("id").limit(0).execute()
        return True
    except Exception as e:
        st.warning("⚠️ 'reactions' table is missing. Reactions will be disabled. Please run the SQL setup script.")
        return False

REACTIONS_TABLE_EXISTS = check_reactions_table()

# --- Secrets for owner only ---
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")
MONCASH_NUM = st.secrets.get("MONCASH_NUM", "(509)-47385663")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

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

# --- UI styling (unchanged) ---
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
    .debug-box {
        background-color: #e0f7fa;
        border-left: 6px solid #00bcd4;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
        font-family: monospace;
        white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper functions ---
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
    """Upload a file to post_media bucket with extensive error checking."""
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return None
    if not MEDIA_URLS_EXISTS:
        st.session_state.last_error = "media_urls column missing."
        return None
    if not POST_MEDIA_BUCKET_OK:
        st.session_state.last_error = "post_media bucket is not accessible."
        return None

    try:
        content_type = file.type
        ext = file.name.split('.')[-1]
        # Generate a unique filename
        timestamp = int(time.time())
        random_hash = hashlib.md5(file.name.encode()).hexdigest()[:8]
        file_name = f"post_{user_id}_{timestamp}_{random_hash}.{ext}"

        st.toast(f"Uploading {file.name} as {file_name}...", icon="📤")

        file_bytes = file.getvalue()
        # Upload
        supabase.storage.from_("post_media").upload(
            file_name, 
            file_bytes, 
            {"content-type": content_type}
        )
        # Get public URL
        public_url = supabase.storage.from_("post_media").get_public_url(file_name)

        # Verify that the URL is accessible (optional)
        try:
            r = requests.head(public_url, timeout=5)
            if r.status_code != 200:
                st.warning(f"Uploaded file URL {public_url} returned status {r.status_code}")
        except Exception as e:
            st.warning(f"Could not verify uploaded file: {e}")

        media_type = "video" if content_type.startswith("video") else "image"
        return {"url": public_url, "type": media_type}
    except Exception as e:
        error_str = str(e)
        st.session_state.last_error = f"Media upload failed: {error_str}"
        st.error(f"❌ Media upload error: {error_str}")
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

def load_posts():
    """Load posts with visibility filtering (public + user's private)."""
    if supabase is None:
        return []
    try:
        # Determine which columns to select based on schema
        if MEDIA_URLS_EXISTS:
            select_cols = "*, profiles(full_name, avatar_url, is_live)"
        else:
            select_cols = "id, user_id, content, is_public, likes_count, shares_count, original_post_id, created_at, profiles(full_name, avatar_url, is_live)"

        # If user is logged in, fetch public posts and user's private posts separately
        if st.session_state.user:
            # Public posts (is_public = true)
            public_resp = supabase.table("posts").select(select_cols).eq("is_public", True).execute()
            # Private posts owned by current user (is_public = false and user_id = current user)
            private_resp = supabase.table("posts").select(select_cols).eq("is_public", False).eq("user_id", st.session_state.user.id).execute()
            posts = public_resp.data + private_resp.data
            # Sort by created_at descending
            posts.sort(key=lambda x: x['created_at'], reverse=True)
        else:
            # Not logged in: only public posts
            resp = supabase.table("posts").select(select_cols).eq("is_public", True).order("created_at", desc=True).execute()
            posts = resp.data

        # For each post, try to add reactions (if table exists)
        for post in posts:
            if "media_urls" not in post:
                post["media_urls"] = []
            post["reactions"] = {}
            post["user_reactions"] = []
            if REACTIONS_TABLE_EXISTS:
                try:
                    reactions_resp = supabase.table("reactions").select("emoji").eq("post_id", post["id"]).execute()
                    counts = {}
                    if reactions_resp.data:
                        for r in reactions_resp.data:
                            emoji = r["emoji"]
                            counts[emoji] = counts.get(emoji, 0) + 1
                    post["reactions"] = counts
                    if st.session_state.user:
                        user_reactions_resp = supabase.table("reactions").select("emoji").eq("post_id", post["id"]).eq("user_id", st.session_state.user.id).execute()
                        post["user_reactions"] = [r["emoji"] for r in user_reactions_resp.data] if user_reactions_resp.data else []
                except Exception as e:
                    # If reactions table query fails, ignore (treat as no reactions)
                    pass
        return posts
    except Exception as e:
        st.session_state.last_error = f"Error loading posts: {e}"
        return []

def create_post(user_id, content, media_files, is_public):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        profile_check = supabase.table("profiles").select("id").eq("id", user_id).execute()
        if not profile_check.data:
            st.warning("Profile missing – attempting to recreate...")
            identifier = None
            if st.session_state.user and st.session_state.user.email:
                identifier = st.session_state.user.email
            elif st.session_state.user and st.session_state.user.phone:
                identifier = st.session_state.user.phone
            if identifier:
                profile = get_or_create_profile(user_id, identifier)
                if not profile:
                    st.session_state.last_error = "Could not create profile."
                    return False
            else:
                st.session_state.last_error = "User identifier not found."
                return False

        media_urls = []
        upload_errors = []
        if MEDIA_URLS_EXISTS and media_files:
            for f in media_files:
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
                else:
                    upload_errors.append(f.name)
                    # error already set in session_state.last_error

        post = {
            "user_id": user_id,
            "content": content,
            "is_public": is_public,
            "likes_count": 0,
            "shares_count": 0,
            "created_at": datetime.now().isoformat()
        }
        if MEDIA_URLS_EXISTS:
            post["media_urls"] = media_urls

        st.toast(f"Attempting to post: {content[:30]}...", icon="📤")
        # Show debug info
        with st.expander("Debug: Post data being sent"):
            st.json(post)

        result = supabase.table("posts").insert(post).execute()

        if result.data:
            st.session_state.posts = load_posts()
            if upload_errors:
                st.warning(f"✅ Post created, but the following files failed to upload: {', '.join(upload_errors)}. Check bucket permissions.")
            else:
                st.success("✅ Post published! Refreshing feed...")
            st.session_state.last_error = None  # clear any previous error
            # Show debug info
            with st.expander("Debug: Insert result"):
                st.json(result.data)
            return True
        else:
            st.session_state.last_error = "Post insertion failed – no data returned."
            return False
    except Exception as e:
        st.session_state.last_error = f"❌ Error creating post: {e}\n{traceback.format_exc()}"
        return False

def toggle_reaction(post_id, user_id, emoji):
    if supabase is None or not REACTIONS_TABLE_EXISTS:
        st.error("Reactions are disabled because the 'reactions' table is missing.")
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
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error toggling reaction: {e}"
        return False

def share_post(original_post_id, user_id, is_public=True):
    if supabase is None:
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
            "created_at": datetime.now().isoformat()
        }
        if MEDIA_URLS_EXISTS:
            post["media_urls"] = []
        supabase.table("posts").insert(post).execute()
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error sharing post: {e}"
        return False

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
        if parent_id is not None:
            comment["parent_id"] = parent_id
        supabase.table("comments").insert(comment).execute()
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
        comments = response.data
        tree = {}
        for c in comments:
            pid = c.get("parent_id")
            if pid not in tree:
                tree[pid] = []
            tree[pid].append(c)

        def flatten(parent_id):
            result = []
            for c in tree.get(parent_id, []):
                result.append(c)
                result.extend(flatten(c["id"]))
            return result

        return flatten(None)
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
            "*, profiles(full_name, avatar_url)"
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
            "*, profiles(full_name, avatar_url)"
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
        error_msg = str(e)
        if "Phone logins are disabled" in error_msg:
            st.error("Phone authentication is disabled in Supabase. Please enable it in Authentication → Providers.")
        else:
            st.session_state.last_error = f"Failed to send OTP: {error_msg}"
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
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.owner_space_access = False
    st.session_state.phone_otp_sent = False
    st.session_state.temp_phone = ""
    st.session_state.viewing_live = None
    st.rerun()

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
            elif "twitch.tv" in stream_url:
                channel = stream_url.split("/")[-1]
                embed_url = f"https://player.twitch.tv/?channel={channel}&parent={st.request.host}"
                st.components.v1.html(f'<iframe src="{embed_url}" height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>', height=410)
            else:
                st.video(stream_url)
        else:
            st.info("The streamer has not provided a video URL yet. Please wait.")
            st.markdown("""
            <div style="background: #000; border-radius: 10px; padding: 20px; text-align: center; color: white;">
                <h3>📡 Awaiting Stream URL</h3>
                <p>The streamer will provide a link shortly.</p>
                <div style="font-size: 4rem; margin: 20px;">⏳</div>
            </div>
            """, unsafe_allow_html=True)

        try:
            base_url = st.request.url.split('?')[0]
        except:
            base_url = "https://globalinternetpy.streamlit.app"
        share_url = f"{base_url}?live={session_id}"
        st.text_input("Shareable link", value=share_url, key=f"share_{session_id}")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📋 Copy Link", key=f"copy_{session_id}"):
                st.info("Link copied to clipboard!")
        with col_b:
            subject = f"Join me live on GLOBALINTERNET.PY: {session['title']}"
            body = f"Join the live session: {share_url}"
            mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            st.markdown(f'<a href="{mailto}" target="_blank"><button style="background: linear-gradient(105deg, #00a8ff 0%, #0080ff 100%); color: white; border: none; border-radius: 40px; padding: 10px 28px; font-weight: 600;">📧 Share via Email</button></a>', unsafe_allow_html=True)

    with col2:
        st.subheader("Live Chat")
        if st.button("🔄 Refresh Chat", key=f"refresh_{session_id}"):
            st.rerun()

        with st.form(f"new_comment_{session_id}", clear_on_submit=True):
            msg = st.text_input("Write a comment...")
            if st.form_submit_button("Send"):
                if msg:
                    if add_comment(session_id, st.session_state.user.id, msg):
                        st.rerun()

        comments = load_comments(session_id)
        for c in comments:
            indent = "comment-indent" if c.get("parent_id") else ""
            st.markdown(f"<div class='{indent}'>", unsafe_allow_html=True)
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
                st.markdown(f"<span class='comment-meta'>{c['created_at'][:16]}</span>", unsafe_allow_html=True)
            with cols[1]:
                if st.button(f"👍 {c.get('likes', 0)}", key=f"like_{c['id']}"):
                    like_comment(c['id'], increment=True)
                    st.rerun()
            with cols[2]:
                if st.session_state.user and c['user_id'] == st.session_state.user.id:
                    if st.button("🗑️", key=f"del_{c['id']}"):
                        delete_comment(c['id'])
                        st.rerun()
            if st.button(f"💬 Reply", key=f"reply_{c['id']}"):
                st.session_state[f"replying_to_{c['id']}"] = True
                st.rerun()
            if st.session_state.get(f"replying_to_{c['id']}", False):
                with st.form(f"reply_form_{c['id']}"):
                    reply = st.text_input("Your reply")
                    if st.form_submit_button("Post Reply"):
                        if reply:
                            add_comment(session_id, st.session_state.user.id, reply, parent_id=c['id'])
                            del st.session_state[f"replying_to_{c['id']}"]
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# --- Feed ---
def render_feed():
    st.header("🌐 Collaboration Feed")

    # Display any persistent error
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
            live_val = params["live"][0] if isinstance(params["live"], list) else params["live"]
            session_id = int(live_val)
            st.session_state.viewing_live = session_id
        except:
            pass

    if st.session_state.viewing_live:
        render_live_page(st.session_state.viewing_live)
        return

    # --- Enhanced post composer ---
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

        if MEDIA_URLS_EXISTS:
            media_files = st.file_uploader(
                "Add images or videos (optional)",
                type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"],
                accept_multiple_files=True,
                help="You can select multiple files. Max 200MB per file."
            )
        else:
            media_files = None
            st.info("📹 Media uploads are temporarily disabled (database setup required). You can still post text.")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            visibility = st.radio("Visibility", ["Public", "Private"], horizontal=True, index=0)
            is_public = (visibility == "Public")
        with col3:
            posted = st.form_submit_button("🚀 Post", use_container_width=True)

        if posted:
            if not content and not (MEDIA_URLS_EXISTS and media_files):
                st.warning("Please add a caption or media.")
            else:
                if create_post(st.session_state.user.id, content, media_files if MEDIA_URLS_EXISTS else [], is_public):
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
        post_id, post_preview = st.session_state.delete_confirm
        st.warning(f"Are you sure you want to delete this post?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete"):
                if delete_post(post_id):
                    st.success("Post deleted.")
                    st.session_state.posts = load_posts()
                st.session_state.delete_confirm = None
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.delete_confirm = None
                st.rerun()
        st.divider()

    # --- If no real posts, show demo post ---
    if not st.session_state.posts:
        demo_post = {
            "id": -1,
            "user_id": st.session_state.user.id if st.session_state.user else "demo",
            "content": "Welcome to GLOBALINTERNET.PY! This is a sample post to show how the feed works. You can react with emojis, comment, and share. Try it out!",
            "is_public": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profiles": {
                "full_name": st.session_state.profile["full_name"] if st.session_state.profile else "Demo User",
                "avatar_url": st.session_state.profile.get("avatar_url") if st.session_state.profile else None,
                "is_live": False
            },
            "media_urls": [
                {"type": "video", "url": "https://www.w3schools.com/html/mov_bbb.mp4"}
            ] if MEDIA_URLS_EXISTS else [],
            "reactions": {"👍": 3, "❤️": 2, "😂": 1},
            "user_reactions": ["👍"] if st.session_state.user else [],
            "shares_count": 1
        }

        with st.container():
            col_a, col_b, col_c, col_d = st.columns([1, 5, 2, 1])
            with col_a:
                avatar = demo_post.get("profiles", {}).get("avatar_url")
                if avatar:
                    st.image(avatar, width=40)
                else:
                    st.markdown("👤")
            with col_b:
                name = demo_post['profiles']['full_name']
                st.markdown(f"**{name}**")
            with col_c:
                st.caption(demo_post['created_at'])
            with col_d:
                pass

            if demo_post['content']:
                st.markdown(f"<div class='post-card'>{demo_post['content']}</div>", unsafe_allow_html=True)

            if demo_post["media_urls"]:
                for media in demo_post["media_urls"]:
                    if media["type"] == "image":
                        st.image(media["url"], use_column_width=True)
                    elif media["type"] == "video":
                        st.video(media["url"])

            emojis = ["👍", "👎", "❤️", "😂", "😮", "😢", "👏"]
            cols = st.columns(len(emojis) + 2)
            for i, emoji in enumerate(emojis):
                with cols[i]:
                    count = demo_post["reactions"].get(emoji, 0)
                    btn_label = f"{emoji} {count}" if count > 0 else emoji
                    if st.button(btn_label, key=f"demo_react_{i}"):
                        demo_post["reactions"][emoji] = demo_post["reactions"].get(emoji, 0) + 1
                        st.rerun()

            with cols[len(emojis)]:
                if st.button("💬 2", key="demo_comment"):
                    st.session_state["show_demo_comments"] = not st.session_state.get("show_demo_comments", False)
                    st.rerun()
            with cols[len(emojis)+1]:
                st.button("🔄 1", key="demo_share")

            if st.session_state.get("show_demo_comments", False):
                st.markdown("#### Comments")
                with st.form("demo_comment_form", clear_on_submit=True):
                    msg = st.text_input("Write a comment...")
                    if st.form_submit_button("Post Comment"):
                        if msg:
                            st.info("Demo comment posted! (not saved)")
                            st.session_state["demo_comment_posted"] = True
                            st.rerun()
                st.markdown("**User123**: Great app!")
                st.markdown("**Jane**: Love the video 😍")
                st.markdown("**Mike**: 🔥🔥🔥")

            st.divider()

        st.info("👆 This is a demo post to show you the interactive features. Create a real post to start building your feed!")

    else:
        # --- Display real posts ---
        for post in st.session_state.posts:
            with st.container():
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

                if post['content']:
                    st.markdown(f"<div class='post-card'>{post['content']}</div>", unsafe_allow_html=True)

                media_urls = post.get("media_urls", [])
                if media_urls:
                    for media in media_urls:
                        if media["type"] == "image":
                            st.image(media["url"], use_column_width=True)
                        elif media["type"] == "video":
                            st.video(media["url"])

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
                    if st.button(f"💬 {len(load_comments(post['id']))}", key=f"comment_btn_{post['id']}"):
                        st.session_state[f"show_comments_{post['id']}"] = not st.session_state.get(f"show_comments_{post['id']}", False)
                        st.rerun()
                with cols[len(emojis)+1]:
                    if st.button(f"🔄 {post['shares_count']}", key=f"share_{post['id']}"):
                        share_post(post['id'], st.session_state.user.id, is_public=True)
                        st.rerun()

                if st.session_state.get(f"show_comments_{post['id']}", False):
                    st.markdown("#### Comments")
                    with st.form(f"new_comment_post_{post['id']}", clear_on_submit=True):
                        msg = st.text_input("Write a comment...")
                        if st.form_submit_button("Post Comment"):
                            if msg:
                                if add_comment(post['id'], st.session_state.user.id, msg):
                                    st.rerun()

                    comments = load_comments(post['id'])
                    for c in comments:
                        indent = "comment-indent" if c.get("parent_id") else ""
                        st.markdown(f"<div class='{indent}'>", unsafe_allow_html=True)
                        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                        with col1:
                            st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
                            st.markdown(f"<span class='comment-meta'>{c['created_at'][:16]}</span>", unsafe_allow_html=True)
                        with col2:
                            if st.button(f"👍 {c.get('likes', 0)}", key=f"like_post_{c['id']}"):
                                like_comment(c['id'], increment=True)
                                st.rerun()
                        with col3:
                            if st.button(f"💬 Reply", key=f"reply_post_{c['id']}"):
                                st.session_state[f"replying_to_post_{c['id']}"] = True
                                st.rerun()
                        with col4:
                            if st.session_state.user and c['user_id'] == st.session_state.user.id:
                                if st.button("🗑️", key=f"del_post_{c['id']}"):
                                    delete_comment(c['id'])
                                    st.rerun()
                        if st.session_state.get(f"replying_to_post_{c['id']}", False):
                            with st.form(f"reply_form_post_{c['id']}"):
                                reply = st.text_input("Your reply")
                                if st.form_submit_button("Post Reply"):
                                    if reply:
                                        add_comment(post['id'], st.session_state.user.id, reply, parent_id=c['id'])
                                        del st.session_state[f"replying_to_post_{c['id']}"]
                                        st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                st.divider()

# --- Profile, Map, Owner Space (unchanged) ---
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
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        uploaded = st.file_uploader("📸 Change picture", type=["png","jpg","jpeg"], label_visibility="collapsed")
        if uploaded:
            url = upload_avatar(st.session_state.user.id, uploaded)
            if url:
                profile["avatar_url"] = url
                update_profile(profile)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        with st.form("edit_profile"):
            st.markdown("#### Account Information")
            full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
            bio = st.text_area("Bio", value=profile.get("bio", ""), height=100)
            location = st.text_input("Location", value=profile.get("location", ""))
            st.markdown("---")
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
