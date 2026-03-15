"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 9.1.0 (Private posts, dislike reaction)
"""
import streamlit as st
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

st.set_page_config(page_title="GLOBALINTERNET.PY", page_icon="🇭🇹", layout="wide")

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

# --- Schema detection: check if media_urls column exists in posts ---
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

# --- UI styling ---
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
    .camera-icon {
        font-size: 2rem;
        text-align: center;
        background: rgba(0,168,255,0.1);
        padding: 20px;
        border-radius: 50%;
        display: inline-block;
        cursor: pointer;
        transition: all 0.2s;
    }
    .camera-icon:hover {
        background: rgba(0,168,255,0.2);
        transform: scale(1.05);
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
    </style>
""", unsafe_allow_html=True)

# --- Helper functions for Supabase ---

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
                st.error("Failed to create profile.")
                return None
    except Exception as e:
        st.error(f"Error in get_or_create_profile: {e}")
        return None

def update_profile(profile_data):
    if supabase is None:
        return False
    try:
        supabase.table("profiles").update(profile_data).eq("id", profile_data["id"]).execute()
        return True
    except Exception as e:
        st.error(f"Error updating profile: {e}")
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
        st.error(f"Avatar upload failed: {e}")
        return None

def upload_post_media(user_id, file):
    if supabase is None or not MEDIA_URLS_EXISTS:
        return None
    try:
        content_type = file.type
        ext = file.name.split('.')[-1]
        file_name = f"post_{user_id}_{int(time.time())}_{hashlib.md5(file.name.encode()).hexdigest()[:8]}.{ext}"
        file_bytes = file.getvalue()
        supabase.storage.from_("post_media").upload(file_name, file_bytes, {"content-type": content_type})
        public_url = supabase.storage.from_("post_media").get_public_url(file_name)
        return {"url": public_url, "type": "video" if content_type.startswith("video") else "image"}
    except Exception as e:
        error_str = str(e)
        if "new row violates row-level security policy" in error_str:
            st.error("Storage permission error: Please ensure the 'post_media' bucket is public and RLS policies allow uploads.")
        elif "bucket not found" in error_str:
            st.error("The 'post_media' storage bucket does not exist. Please create it in the Supabase Storage dashboard.")
        else:
            st.error(f"Media upload failed: {error_str}")
        return None

def load_posts():
    """Load posts with visibility filtering."""
    if supabase is None:
        return []
    try:
        # Build query based on schema
        if MEDIA_URLS_EXISTS:
            query = supabase.table("posts").select(
                "*, profiles(full_name, avatar_url, is_live)"
            )
        else:
            query = supabase.table("posts").select(
                "id, user_id, content, is_public, likes_count, shares_count, original_post_id, created_at, profiles(full_name, avatar_url, is_live)"
            )

        # Apply visibility filter: public posts + private posts owned by current user
        if st.session_state.user:
            # Show all public posts + private posts from current user
            query = query.or_(
                f"is_public.eq.true,user_id.eq.{st.session_state.user.id}"
            )
        else:
            # Not logged in: only public posts
            query = query.eq("is_public", True)

        response = query.order("created_at", desc=True).execute()
        posts = response.data
        for post in posts:
            if "media_urls" not in post:
                post["media_urls"] = []
            # Fetch reactions
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
            else:
                post["user_reactions"] = []
        return posts
    except Exception as e:
        st.error(f"Error loading posts: {e}")
        return []

def create_post(user_id, content, media_files, is_public):
    if supabase is None:
        st.error("Supabase not configured.")
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
                    st.error("Could not create profile.")
                    return False
            else:
                st.error("User identifier not found.")
                return False

        media_urls = []
        if MEDIA_URLS_EXISTS and media_files:
            for f in media_files:
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
                else:
                    st.warning("One file failed to upload, skipped.")

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

        result = supabase.table("posts").insert(post).execute()
        if result.data:
            st.session_state.posts = load_posts()
            return True
        else:
            st.error("Post insertion failed.")
            return False
    except Exception as e:
        st.error(f"Error creating post: {e}")
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
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.error(f"Error toggling reaction: {e}")
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
        st.error(f"Error sharing post: {e}")
        return False

def add_comment(post_id, user_id, content):
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
        supabase.table("comments").insert(comment).execute()
        return True
    except Exception as e:
        st.error(f"Error adding comment: {e}")
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
        st.error(f"Error loading comments: {e}")
        return []

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
        st.error(f"Error toggling comment like: {e}")
        return False

# --- Live session functions ---
def start_live_session(title):
    if supabase is None or st.session_state.user is None:
        st.error("Cannot start live session.")
        return None
    try:
        active = supabase.table("live_sessions").select("id").eq("user_id", st.session_state.user.id).eq("is_live", True).execute()
        if active.data:
            st.warning("You already have an active live session. End it first.")
            return None
        session_data = {
            "user_id": st.session_state.user.id,
            "title": title,
            "is_live": True,
            "started_at": datetime.now().isoformat(),
            "stream_url": None
        }
        result = supabase.table("live_sessions").insert(session_data).execute()
        if result.data:
            supabase.table("profiles").update({"is_live": True}).eq("id", st.session_state.user.id).execute()
            st.session_state.profile["is_live"] = True
            st.session_state.live_sessions = load_live_sessions()
            return result.data[0]["id"]
        else:
            st.error("Failed to start live session.")
            return None
    except Exception as e:
        st.error(f"Error starting live session: {e}")
        return None

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
        return True
    except Exception as e:
        st.error(f"Error ending live session: {e}")
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
        st.error(f"Error loading live sessions: {e}")
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
        st.error(f"Error fetching live session: {e}")
        return None

# --- Health monitoring ---
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

# --- Auth functions with password reset ---
def sign_up_email(email, password, full_name):
    if supabase is None:
        st.error("Registration unavailable.")
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
        st.error(f"Sign-up failed: {e}")
        return False

def log_in_email(email, password):
    if supabase is None:
        st.error("Login unavailable.")
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
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def reset_password_email(email):
    if supabase is None:
        st.error("Supabase not configured.")
        return False
    try:
        supabase.auth.reset_password_for_email(email)
        st.success("Password reset email sent. Please check your inbox.")
        return True
    except Exception as e:
        st.error(f"Failed to send reset email: {e}")
        return False

def format_phone(phone: str) -> str:
    phone = phone.strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone

def send_phone_otp(raw_phone):
    if supabase is None:
        st.error("Supabase not configured.")
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
            st.error(f"Failed to send OTP: {error_msg}")
        return False

def verify_phone_otp(raw_phone, token):
    if supabase is None:
        st.error("Supabase not configured.")
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
            st.rerun()
            return True
        else:
            st.error("Verification failed – no user returned.")
            return False
    except Exception as e:
        st.error(f"Verification failed: {e}")
        return False

def logout():
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

# --- Live page ---
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
        st.markdown("""
        <div style="background: #000; border-radius: 10px; padding: 20px; text-align: center; color: white;">
            <h3>📡 Live Stream (Simulated)</h3>
            <p>In a real implementation, this would be a video player.</p>
            <div style="font-size: 3rem;">📹</div>
        </div>
        """, unsafe_allow_html=True)

        share_url = f"{st.get_option('server.baseUrlPath') or st.request.url.split('?')[0]}?live={session_id}"
        st.text_input("Shareable link", value=share_url)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📋 Copy Link"):
                st.info("Link copied! (simulated)")
        with col_b:
            subject = f"Join me live on GLOBALINTERNET.PY: {session['title']}"
            body = f"Join the live session: {share_url}"
            mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
            st.markdown(f'<a href="{mailto}" target="_blank"><button style="background: linear-gradient(105deg, #00a8ff 0%, #0080ff 100%); color: white; border: none; border-radius: 40px; padding: 10px 28px; font-weight: 600;">📧 Share via Email</button></a>', unsafe_allow_html=True)

    with col2:
        st.subheader("Live Chat")
        comments = load_comments(session_id)
        for c in comments:
            cols = st.columns([4, 1])
            with cols[0]:
                st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
            with cols[1]:
                if st.button(f"👍 {c.get('likes', 0)}", key=f"like_comment_{c['id']}"):
                    like_comment(c['id'], increment=True)
                    st.rerun()
        with st.form("live_chat"):
            msg = st.text_input("Message")
            if st.form_submit_button("Send"):
                if msg:
                    if add_comment(session_id, st.session_state.user.id, msg):
                        st.rerun()

    if st.button("Back to Feed"):
        st.session_state.viewing_live = None
        st.rerun()

# --- Feed ---
def render_feed():
    st.header("🌐 Collaboration Feed")

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

    # New post form with visibility options
    with st.form("new_post", clear_on_submit=True):
        content = st.text_area("Caption", height=100, placeholder="Write a caption...")
        if MEDIA_URLS_EXISTS:
            media_files = st.file_uploader(
                "Add images or videos (optional)",
                type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"],
                accept_multiple_files=True
            )
        else:
            media_files = None
            st.info("📹 Media uploads are temporarily disabled (database setup required). You can still post text.")
        col1, col2 = st.columns([4,1])
        with col2:
            # Visibility: Public or Private
            visibility = st.radio("Visibility", ["Public", "Private"], horizontal=True, index=0)
            is_public = (visibility == "Public")
        if st.form_submit_button("🚀 Post"):
            if content or (MEDIA_URLS_EXISTS and media_files):
                if create_post(st.session_state.user.id, content, media_files if MEDIA_URLS_EXISTS else [], is_public):
                    st.success("Post published!")
                    st.rerun()
            else:
                st.warning("Please add a caption or media.")

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

    for post in st.session_state.posts:
        with st.container():
            col_a, col_b, col_c = st.columns([1,5,2])
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
                # Show private badge if post is not public
                if not post.get("is_public", True):
                    st.markdown("<span class='private-badge'>Private</span>", unsafe_allow_html=True)
            with col_c:
                st.caption(post['created_at'][:16])

            if post['content']:
                st.markdown(f"<div class='post-card'>{post['content']}</div>", unsafe_allow_html=True)

            media_urls = post.get("media_urls", [])
            if media_urls:
                for media in media_urls:
                    if media["type"] == "image":
                        st.image(media["url"], use_column_width=True)
                    elif media["type"] == "video":
                        st.video(media["url"])

            # Reactions (now including 👎)
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
                comments = load_comments(post['id'])
                for c in comments:
                    st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
                with st.form(key=f"add_comment_{post['id']}"):
                    new_comment = st.text_input("Write a comment...")
                    if st.form_submit_button("Post Comment"):
                        if new_comment:
                            add_comment(post['id'], st.session_state.user.id, new_comment)
                            st.rerun()
            st.divider()

# --- Profile ---
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

# --- Satellite Map ---
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

# --- Owner's Dashboard ---
def render_reclaim():
    st.header("🔐 Owner's Dashboard")
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

# --- Owner Space ---
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
    st.success("Welcome, Owner!")
    st.markdown("### 🔑 Your Private Credentials")
    st.markdown(f"- **CIN Number:** `{OWNER_CIN}`")
    st.markdown(f"- **MonCash Business:** `{MONCASH_NUM}`")
    st.markdown(f"- **OwnerSpace Password:** `{OWNSPACE_PASSWORD}`")
    if st.button("Logout from Owner Space"):
        st.session_state.owner_space_access = False
        st.rerun()

# --- Main app ---
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

        # Live controls
        if st.session_state.profile and st.session_state.profile.get("is_live"):
            st.markdown("🔴 **You are live!**")
            if st.button("End Live Session"):
                for ls in st.session_state.live_sessions:
                    if ls["user_id"] == st.session_state.user.id:
                        end_live_session(ls["id"])
                        st.rerun()
                        break
        else:
            with st.expander("Go Live"):
                with st.form("go_live"):
                    title = st.text_input("Live title")
                    if st.form_submit_button("Start Live"):
                        if title:
                            session_id = start_live_session(title)
                            if session_id:
                                st.success("Live started!")
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
            "🔐 Owner's Dashboard": render_reclaim,
            "🕊️ Owner Space": owner_space
        }
        choice = st.selectbox("Menu", list(pages.keys()))
    pages[choice]()

# --- Login interface ---
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
                    if st.form_submit_button("🚀 Login", use_container_width=True):
                        log_in_email(email, password)
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
            st.info("Phone users: You will receive a 6‑digit OTP each time you log in. No password needed.")
            if not st.session_state.phone_otp_sent:
                with st.form("phone_request"):
                    phone = st.text_input("Phone number (digits only, e.g., 50947385663)")
                    if st.form_submit_button("📲 Send OTP", use_container_width=True):
                        if phone:
                            if send_phone_otp(phone):
                                st.session_state.phone_otp_sent = True
                                st.session_state.temp_phone = phone
                                st.rerun()
                        else:
                            st.warning("Please enter a phone number")
            else:
                st.write(f"OTP sent to **+{st.session_state.temp_phone}**")
                with st.form("phone_verify"):
                    otp = st.text_input("Enter 6-digit OTP code")
                    if st.form_submit_button("✅ Verify & Login", use_container_width=True):
                        if otp:
                            verify_phone_otp(st.session_state.temp_phone, otp)
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
