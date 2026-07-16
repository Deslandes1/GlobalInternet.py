# ====== FULL app.py (Lakay se Lakay - no post_type column) ======
# Lakay se Lakay - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes (Python Developer, Haiti)
# Version: 78.26.0 (Resilient column handling for profile visibility & contacts)
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
import asyncio
import tempfile
import edge_tts
from PIL import Image

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Lakay se Lakay", page_icon="🏠", layout="wide")

# ====== KEEP‑ALIVE PING ======
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
        st.warning("⚠️ Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in your Streamlit secrets.")
        return None
    if not url.startswith("https://"):
        st.error("❌ SUPABASE_URL must start with 'https://'. Please correct your secrets.")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        error_msg = str(e)
        if "Name or service not known" in error_msg or "Failed to resolve" in error_msg:
            st.error("❌ Cannot resolve Supabase domain. Please check your SUPABASE_URL (must be a valid internet address).")
        else:
            st.error(f"❌ Failed to connect to Supabase: {error_msg}")
        return None

supabase = init_supabase()

# ====== ENSURE STORAGE BUCKETS EXIST ======
def ensure_bucket_exists(bucket_name, public=True):
    if supabase is None:
        return False
    supabase_key = st.secrets.get("SUPABASE_KEY")
    supabase_url = st.secrets.get("SUPABASE_URL")
    if not supabase_key or not supabase_url:
        return False
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    check_url = f"{supabase_url}/storage/v1/bucket/{bucket_name}"
    try:
        check_resp = requests.get(check_url, headers=headers)
        return check_resp.status_code == 200
    except Exception:
        return False

# --- Secrets (NO DEFAULTS – all come from st.secrets) ---
OWNER_CIN = st.secrets.get("OWNER_CIN")
MONCASH_NUM = st.secrets.get("MONCASH_NUM")
UNIBANK_ACCOUNT = st.secrets.get("UNIBANK_ACCOUNT")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password")  # <-- Your password

BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "https://your-backend.com")
BACKEND_API_KEY = st.secrets.get("BACKEND_API_KEY", "")
EXCHANGE_RATE_API = st.secrets.get("EXCHANGE_RATE_API", "https://api.exchangerate-api.com/v4/latest/USD")

SMTP_SERVER = st.secrets.get("SMTP_SERVER")
SMTP_PORT = st.secrets.get("SMTP_PORT")
SMTP_USERNAME = st.secrets.get("SMTP_USERNAME")
SMTP_PASSWORD = st.secrets.get("SMTP_PASSWORD")
EMAIL_FROM = st.secrets.get("EMAIL_FROM")
EMAIL_TO = st.secrets.get("EMAIL_TO")

JITSI_DOMAIN = st.secrets.get("JITSI_DOMAIN", "meet.jit.si")

# ====== GLOBAL SHIELD API KEY – NO FALLBACK! ======
GLOBAL_SHIELD_API_KEY = st.secrets.get("GLOBAL_SHIELD_API_KEY")
GLOBAL_SHIELD_ACTIVE = bool(GLOBAL_SHIELD_API_KEY)

# ====== GROQ API KEY ======
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

# Optional: check for missing critical secrets
_missing = []
if not OWNER_CIN:
    _missing.append("OWNER_CIN")
if not MONCASH_NUM:
    _missing.append("MONCASH_NUM")
if not UNIBANK_ACCOUNT:
    _missing.append("UNIBANK_ACCOUNT")
if not OWNSPACE_PASSWORD:
    _missing.append("OwnSpace_Password")
if not GLOBAL_SHIELD_API_KEY:
    _missing.append("GLOBAL_SHIELD_API_KEY")
if not GROQ_API_KEY:
    _missing.append("GROQ_API_KEY")
if _missing:
    st.warning(f"⚠️ Missing secrets: {', '.join(_missing)}. Some features may not work. Define them in Streamlit Cloud.")

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
if "live_gifts" not in st.session_state:
    st.session_state.live_gifts = []
if "exchange_rate" not in st.session_state:
    st.session_state.exchange_rate = 100
if "background_url" not in st.session_state:
    st.session_state.background_url = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "editing_post" not in st.session_state:
    st.session_state.editing_post = None
if "call_background_url" not in st.session_state:
    st.session_state.call_background_url = None
if "call_reload" not in st.session_state:
    st.session_state.call_reload = 0
if "live_room_name" not in st.session_state:
    st.session_state.live_room_name = None
if "love_story_url" not in st.session_state:
    st.session_state.love_story_url = None
if "show_love_story" not in st.session_state:
    st.session_state.show_love_story = False
# ---- Groq search states ----
if "groq_search_results" not in st.session_state:
    st.session_state.groq_search_results = []
if "groq_selected_item" not in st.session_state:
    st.session_state.groq_selected_item = None
if "groq_search_query" not in st.session_state:
    st.session_state.groq_search_query = ""
# ---- Album states ----
if "viewing_album" not in st.session_state:
    st.session_state.viewing_album = None
if "creating_album" not in st.session_state:
    st.session_state.creating_album = False
# ---- Call state for "ringing" simulation ----
if "call_initiated_time" not in st.session_state:
    st.session_state.call_initiated_time = None
if "call_target_user" not in st.session_state:
    st.session_state.call_target_user = None
if "call_ringing" not in st.session_state:
    st.session_state.call_ringing = False
# ---- Navigation page ----
if "current_page" not in st.session_state:
    st.session_state.current_page = "feed"

# ---- NAVIGATION FROM QUERY PARAMS ----
if "page" in st.query_params:
    page_param = st.query_params["page"]
    valid_pages = ["feed", "friends_chat", "satellite_map", "worldcup", "profile", "video_call", "owner_space"]
    if page_param in valid_pages:
        st.session_state.current_page = page_param
    del st.query_params["page"]

# ====== LANGUAGE DICTIONARY ======
LANG = {
    "en": {
        "login_title": "Login",
        "signup_title": "Sign Up",
        "forgot_password": "Forgot Password",
        "email": "Email",
        "password": "Password",
        "full_name": "Full Name",
        "remember_me": "Remember me",
        "login_button": "🚀 Login",
        "signup_button": "📝 Sign Up",
        "send_reset_link": "Send Reset Link",
        "feed": "📡 Feed",
        "friends_chat": "👥 Friends & Chat",
        "satellite_map": "🛰️ Satellite Map",
        "worldcup": "⚽ Live World Cup",
        "profile": "👤 Profile",
        "owner_space": "🕊️ Owner Space",
        "logout": "🚪 Logout",
        "system_health": "🛡️ System Health",
        "signal": "📡 Signal",
        "latency": "⏱️ Latency",
        "quality": "📊 Quality",
        "uptime": "⏰ Uptime",
        "encrypted": "🔒 Status: ENCRYPTED",
        "compensation": "💰 Compensation",
        "logged_in_as": "👤 Logged in as",
        "go_live": "Go Live (Real Streaming)",
        "external_platform": "External platform (YouTube/Facebook/Twitch)",
        "in_app_camera": "In-app camera",
        "select_platform": "Select platform",
        "live_title": "Live title",
        "create_live_session": "Create Live Session",
        "you_are_live": "🔴 You are live!",
        "end_live_session": "End Live Session",
        "set_stream_url": "📹 Set Stream URL",
        "paste_url": "Paste your live stream URL",
        "update_url": "Update Stream URL",
        "shareable_link": "Shareable link",
        "live_chat_gifts": "Live Chat & Gifts",
        "send_gift": "🎁 Send a Gift",
        "add_moncash": "Add your MonCash phone number in your profile to send gifts.",
        "add_natcash": "Add your NATCASH phone number to receive gifts.",
        "total_gifts": "Total Gifts Received",
        "gifts_sent_to": "Gifts will be sent to your MonCash",
        "gifts_sent_to_natcash": "NATCASH",
        "write_comment": "Write a comment...",
        "send": "Send",
        "back_to_feed": "Back to Feed",
        "create_post": "Create a post",
        "caption_placeholder": "Write something... or paste a video link (YouTube, Vimeo, etc.)",
        "add_media": "Add images or videos (PNG, JPG, JPEG, GIF, MP4, MOV, AVI)",
        "visibility": "Visibility",
        "public": "Public",
        "private": "Private",
        "post": "🚀 Post",
        "delete_post": "🗑️ Delete",
        "comments": "Comments",
        "reply": "💬 Reply",
        "post_reply": "Post Reply",
        "your_reply": "Your reply",
        "clear_error": "Clear error",
        "join_live": "Join Live",
        "watch_stream": "▶ WATCH STREAM",
        "start_broadcast": "▶ START BROADCAST",
        "stop_broadcast": "■ STOP BROADCAST",
        "you_are_broadcaster": "✅ You are the broadcaster. Use the controls below to start streaming.",
        "you_are_viewer": "👀 You are a viewer. Click 'Watch Stream' to see the live video.",
        "choose_background": "🎨 Background Filters",
        "bg_option": "BG",
        "upload_background": "Or upload your own image",
        "background_set": "Background set!",
        "ready_to_start": "Ready to start. Click the button above.",
        "camera_access": "📷 Requesting camera access...",
        "camera_granted": "✅ Camera access granted. Connecting to peer server...",
        "broadcasting": "✅ Broadcasting live! Your peer ID",
        "peer_error": "❌ Peer error",
        "error": "❌ Error",
        "broadcast_ended": "Broadcast ended",
        "initializing": "Initializing...",
        "connected_requesting": "Connected. Requesting stream from broadcaster...",
        "calling": "Calling",
        "received_stream": "Received remote stream",
        "now_watching": "✅ Now watching live stream",
        "call_error": "❌ Call error",
        "call_ended": "Call ended",
        "disconnected": "Disconnected. Please refresh.",
        "send_message": "Send",
        "close_chat": "Close chat",
        "active_call": "📞 Active Call",
        "room_id": "Room ID",
        "share_room": "Share this room ID with the person you want to call.",
        "start_call": "Start a new call",
        "end_call": "End Call",
        "find_users": "🔍 Find Users",
        "search_by_name": "Search by name",
        "add_friend": "➕ Add Friend",
        "view_profile": "👤 View Profile",
        "friend_requests": "📨 Friend Requests Received",
        "accept": "✅ Accept",
        "reject": "❌ Reject",
        "your_friends": "👥 Your Friends",
        "no_friends": "You have no friends yet",
        "chat": "💬 Chat",
        "call": "📞 Call",
        "profile_btn": "👤 Profile",
        "edit_profile": "Edit Profile",
        "save_changes": "💾 Save Changes",
        "change_picture": "📸 Change picture",
        "bio": "Bio",
        "location": "Location",
        "moncash_phone": "MonCash Phone Number (for receiving gifts)",
        "natcash_phone": "NATCASH Phone Number (for receiving gifts)",
        "posts_count": "Posts",
        "connections": "Connections",
        "verified": "Verified",
        "member_since": "Member since",
        "dashboard": "💰 Dashboard",
        "new_users": "📈 New Users",
        "post_moderation": "🛡️ User Post Moderation",
        "client_payments": "📥 Client Payments",
        "gift_management": "🎁 Gift Management",
        "owner_dashboard": "🔐 Owner's Dashboard",
        "balance": "MonCash Business Balance",
        "transfer_funds": "💰 Transfer Funds to Your Account",
        "amount_transfer": "Amount to transfer ($)",
        "transfer": "🚀 Transfer to My MonCash",
        "no_gifts": "No gifts yet.",
        "payout_summary": "Payout Summary",
        "total_gifts_htg": "Total Gifts (HTG)",
        "mark_paid": "Mark All as Paid (Simulated)",
        "contact_support": "📬 Contact for Support / Large Payments",
        "logout_owner": "Logout from Owner Space",
        "setup_instructions": "ℹ️ Setup Instructions (if uploads fail)",
        "storage_error": "Storage permission error: Please set up RLS policies for the 'avatars' bucket.",
        "listen_explanation": "🔊 Listen to App Explanation",
        "voice_lang": "🌐 Voice Language",
        "app_explanation": "This application was built by Gesner Deslandes, Engineer-in-Chief at GlobalInternet.py. Phone: (509) 4738-5663. Email: deslandes78@gmail.com. Get in touch with Gesner if you want to build any website or software. This application is a Haitian social media platform that lets you connect with friends, share posts, go live, send gifts, and chat in real time. It uses Supabase for data, supports live streaming with background filters, and includes a satellite map for fun. It is designed to be a modern, secure, and fun space for Haitian users to interact online. All features are built with Python and Streamlit. Plus, when there's a World Cup game, you can watch it live right here on the platform!",
        "network_error": "⚠️ Cannot connect to the authentication server. Please check your internet connection and try again. If the problem persists, contact support.",
        "debug_hint": "If you are an administrator, enable 'Show debug info' below to see the raw error.",
        "show_debug": "Show debug info",
        "home_title": "🏠 Lakay se Lakay",
        "home_haiti": "HAITI",
        "home_subtitle": "Your Haitian social media platform",
        "call_permission_hint": "📌 Ensure both participants grant camera and microphone access when prompted by the browser. If you don't see each other, refresh the page and try again.",
        "join_instructions": "📌 After joining the room, click the **'Join'** button in the video window and allow camera/microphone access. If you still don't see the other person, ask them to check their camera settings.",
        "reload_call": "🔄 Reload Call",
        "request_to_join": "📨 Request to Join",
        "request_pending": "⏳ Request pending... waiting for broadcaster approval.",
        "broadcaster_controls": "🎛️ Broadcaster Controls",
        "join_live": "🔴 Join Live",
        "user_management": "👥 User Management",
        "ban_user": "🚫 Ban User",
        "unban_user": "✅ Unban User",
        "ban_reason": "Ban Reason",
        "banned": "Banned",
        "active": "Active",
        "my_wall": "📝 My Wall",
        "my_live_sessions": "📺 My Live Sessions",
        "live_status_live": "🔴 LIVE",
        "live_status_ended": "Ended",
        "video_call": "📞 Video Call (Jitsi Demo)",
        "demo_note": "ℹ️ This is a demo using Jitsi Meet – free and open-source. You can start a call and share the room link with anyone.",
        "copy_link": "📋 Copy Room Link",
        "room_link_copied": "✅ Room link copied to clipboard!",
        "start_video_call": "Start a Video Call",
        "your_personal_room": "Your Personal Room",
        "join_room": "Join Room",
        # === Groq search keys ===
        "search_groq": "🔍 Search Books & Videos",
        "groq_search_placeholder": "What are you looking for? (books, tutorials, etc.)",
        "groq_results": "Results",
        "groq_open": "📖 Open",
        "groq_close": "✖ Close",
        "no_groq_results": "No recommendations found.",
        "groq_api_key_missing": "⚠️ Groq API key not set. Add GROQ_API_KEY to your secrets.",
        "youtube_not_supported": "⚠️ YouTube links are not supported in this search. Please search for books or other videos.",
        # === Album keys ===
        "albums": "📸 Photo Albums",
        "create_album": "Create New Album",
        "album_title": "Album Title",
        "album_description": "Description",
        "album_visibility": "Visibility",
        "album_public": "Public",
        "album_private": "Private",
        "upload_photos": "Upload Photos",
        "no_albums": "No albums yet.",
        "view_album": "View Album",
        "delete_album": "Delete Album",
        "album_created": "Album created successfully!",
        "photos_uploaded": "Photos uploaded successfully!",
        "album_deleted": "Album deleted.",
        "cover_photo": "Cover Photo",
        "owner_albums": "All Albums (Owner View)",
        "paste_video_link_hint": "💡 For YouTube, Vimeo, or other video links, simply paste the URL in the caption above. The file uploader is for uploading video/image files from your device.",
        "open_in_new_tab": "Open in new tab",
        "profile_visibility": "Profile Visibility",
        "whatsapp_phone": "WhatsApp Phone (with country code, e.g., 50947385663)",
        "call_unavailable": "User is not available or offline. Please try again later.",
        "calling": "📞 Calling... Ringing...",
        "ringing": "🔔 Ringing... waiting for user to pick up.",
        "email_user": "📧 Email",
        "whatsapp": "💬 WhatsApp",
        "call_now": "📞 Call Now",
        "private_profile": "🔒 This profile is private. Send a friend request to see their posts and albums."
    },
    "fr": {
        # ... (similar translations, but for brevity we can copy from previous version)
    },
    "es": {},
    "ht": {}
}

def t(key):
    return LANG.get(st.session_state.language, LANG["en"]).get(key, key)

# ====== COOKIE HELPERS ======
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

def refresh_supabase_session():
    if supabase is None or not st.session_state.refresh_token:
        return False
    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        if new_session and new_session.user:
            st.session_state.user = new_session.user
            st.session_state.refresh_token = new_session.session.refresh_token
            profile = get_or_create_profile(new_session.user.id, new_session.user.email or new_session.user.phone, new_session.user.email)
            if profile and profile.get("is_banned"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.profile = None
                st.session_state.refresh_token = None
                st.error("🚫 Your account has been banned. Contact support if you believe this is an error.")
                st.rerun()
                return False
            st.session_state.profile = profile
            return True
        else:
            return False
    except Exception as e:
        st.session_state.last_error = f"Token refresh failed: {e}"
        return False

# --- Restore session ---
if not st.session_state.logged_in and supabase:
    inject_cookie_reader()
    refresh_token = get_cookie("sb_refresh_token")
    if refresh_token:
        try:
            user = supabase.auth.get_user(refresh_token)
            if user.user:
                profile = get_or_create_profile(user.user.id, user.user.email or user.user.phone, user.user.email)
                if profile and profile.get("is_banned"):
                    st.error("🚫 Your account has been banned. Contact support if you believe this is an error.")
                    st.stop()
                st.session_state.logged_in = True
                st.session_state.user = user.user
                st.session_state.refresh_token = refresh_token
                st.session_state.profile = profile
                st.session_state.connection_time = time.time()
                st.cache_data.clear()
                st.session_state.posts = load_posts()
                st.session_state.live_sessions = load_live_sessions()
                load_friend_data()
                st.session_state.notifications = load_notifications(user.user.id)
                st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
                st.info("🔁 Session restored – you are still logged in.")
            else:
                set_cookie("sb_refresh_token", "", -1)
                st.warning("Session expired. Please log in again.")
        except Exception:
            set_cookie("sb_refresh_token", "", -1)
            st.warning("Could not restore session. Please log in again.")
            st.session_state.last_error = str(e)

if st.session_state.logged_in and supabase and st.session_state.refresh_token:
    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        if new_session and new_session.user:
            st.session_state.user = new_session.user
            st.session_state.refresh_token = new_session.session.refresh_token
            profile = get_or_create_profile(new_session.user.id, new_session.user.email or new_session.user.phone, new_session.user.email)
            if profile and profile.get("is_banned"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.profile = None
                st.session_state.refresh_token = None
                st.error("🚫 Your account has been banned. Contact support if you believe this is an error.")
                st.stop()
            st.session_state.profile = profile
    except Exception:
        pass

# ====== STARFIELD ======
st.components.v1.html("""
<canvas id="starfield" style="position:fixed; top:0; left:0; width:100%; height:100%; z-index:-2; pointer-events:none;"></canvas>
<script>
(function() {
    const canvas = document.getElementById('starfield');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;
    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        initStars();
    });

    const stars = [];
    const NUM_STARS = 300;

    function initStars() {
        stars.length = 0;
        for (let i = 0; i < NUM_STARS; i++) {
            stars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 2.0 + 0.5,
                twinkleSpeed: 0.02 + Math.random() * 0.04,
                phase: Math.random() * Math.PI * 2
            });
        }
    }
    initStars();

    function drawStars(time) {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        for (const star of stars) {
            const brightness = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(time * star.twinkleSpeed + star.phase));
            ctx.globalAlpha = brightness;
            ctx.beginPath();
            ctx.arc(star.x, star.y, star.radius, 0, 2 * Math.PI);
            ctx.fill();
        }
        ctx.globalAlpha = 1.0;
        requestAnimationFrame(drawStars);
    }
    requestAnimationFrame(drawStars);
})();
</script>
""", height=0)

# ====== UI STYLING ======
st.markdown("""
    <style>
    .stApp { background-color: #D6EAF8; }
    .stApp [data-testid="stAppViewContainer"] { background-color: transparent; color: #1e2a3a; }
    [data-testid="stSidebar"] { background: rgba(214, 234, 248, 0.9); backdrop-filter: blur(8px); border-right: 1px solid rgba(0,168,255,0.3); }
    .lakay-flag-text { background: linear-gradient(135deg, #00209F 0%, #00209F 50%, #D21034 50%, #D21034 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; display: inline-block; }
    .rope-text { display: inline-block; animation: sway 3s ease-in-out infinite; position: relative; }
    .rope-text .stars { position: absolute; top: -20px; left: -20px; right: -20px; bottom: -20px; pointer-events: none; z-index: 1; }
    .rope-text .stars span { position: absolute; font-size: 1.2rem; color: gold; text-shadow: 0 0 10px #ffd700, 0 0 20px #ff8c00; animation: twinkle 2s ease-in-out infinite alternate; }
    .rope-text .stars span:nth-child(1) { top: -10px; left: -15px; animation-delay: 0s; }
    .rope-text .stars span:nth-child(2) { top: -5px; right: -20px; animation-delay: 0.7s; }
    .rope-text .stars span:nth-child(3) { bottom: -10px; left: 10px; animation-delay: 1.4s; }
    .rope-text .stars span:nth-child(4) { bottom: -5px; right: 5px; animation-delay: 0.3s; }
    .rope-text .stars span:nth-child(5) { top: 50%; left: -30px; animation-delay: 1.1s; }
    .rope-text .stars span:nth-child(6) { top: 30%; right: -30px; animation-delay: 0.9s; }
    @keyframes sway { 0% { transform: rotate(-2deg) scale(1); } 50% { transform: rotate(2deg) scale(1.02); } 100% { transform: rotate(-2deg) scale(1); } }
    @keyframes twinkle { 0% { opacity: 0.3; transform: scale(0.8); } 100% { opacity: 1; transform: scale(1.2); } }
    .haiti-symbol { font-size: 4rem; text-align: center; background: linear-gradient(135deg, #00209F 0%, #00209F 50%, #D21034 50%, #D21034 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; display: inline-block; width: 100%; }
    .owner-name { text-align: center; font-size: 1.5rem; font-weight: 600; color: #0a2a44; margin-top: -10px; }
    .collaborators { text-align: center; font-size: 0.9rem; color: #2c3e50; background: rgba(255,255,255,0.5); padding: 8px 16px; border-radius: 40px; margin: 10px 0; border: 1px solid rgba(0,68,204,0.2); }
    .stMetric { background: rgba(255,255,255,0.6); backdrop-filter: blur(5px); padding: 20px; border-radius: 20px; border: 1px solid rgba(0,168,255,0.3); box-shadow: 0 8px 20px rgba(0,20,50,0.1); }
    .post-card { background: rgba(255,255,255,0.7); backdrop-filter: blur(8px); padding: 20px 25px; border-radius: 20px; border: 1px solid rgba(0,168,255,0.2); margin: 15px 0; color: #1e2a3a; transition: transform 0.2s; }
    .post-card:hover { transform: translateY(-2px); box-shadow: 0 12px 25px rgba(0,0,0,0.1); }
    .health-text { font-family: 'Courier New', monospace; color: #0a2a44; background: rgba(255,255,255,0.6); backdrop-filter: blur(5px); padding: 15px; border-radius: 16px; border-left: 4px solid #00a8ff; }
    .stButton > button { background: linear-gradient(105deg, #00a8ff 0%, #0080ff 100%); color: white; border: none; border-radius: 40px; padding: 8px 20px; font-weight: 600; box-shadow: 0 8px 16px rgba(0,128,255,0.2); transition: all 0.2s; font-size: 0.9rem; }
    .stButton > button:hover { background: linear-gradient(105deg, #0080ff 0%, #0066cc 100%); box-shadow: 0 12px 24px rgba(0,128,255,0.3); transform: scale(1.02); }
    .live-badge { background-color: #ff4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; display: inline-block; margin-left: 8px; }
    .green-dot { height: 12px; width: 12px; background-color: #00ff88; border-radius: 50%; display: inline-block; margin-right: 5px; animation: pulse 2s infinite; }
    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.1); } 100% { opacity: 1; transform: scale(1); } }
    .private-badge { background-color: #ffaa00; color: #1e2a3a; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; display: inline-block; margin-left: 8px; }
    .comment-indent { margin-left: 2rem; border-left: 2px solid #ddd; padding-left: 1rem; margin-bottom: 10px; }
    .comment-meta { font-size: 0.8rem; color: #666; }
    .delete-confirm { background-color: #ffdddd; border-left: 3px solid red; padding: 10px; margin: 10px 0; }
    .error-box { background-color: #ffdddd; border-left: 6px solid #ff4444; padding: 15px; margin: 10px 0; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }
    video { max-width: 100%; max-height: 60vh; width: auto; height: auto; object-fit: contain; border-radius: 12px; }
    img { max-width: 100%; max-height: 60vh; width: auto; height: auto; object-fit: contain; border-radius: 12px; }
    .comment-section { margin-top: 20px; background: rgba(255,255,255,0.5); padding: 15px; border-radius: 16px; }
    .friend-count { font-size: 1.2rem; font-weight: bold; color: #0a2a44; }
    .online-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #00ff88; border: 2px solid white; margin-left: 2px; vertical-align: middle; animation: pulse 2s infinite; }
    .offline-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #888; border: 2px solid white; margin-left: 2px; vertical-align: middle; }
    .profile-avatar { width: 150px; height: 150px; object-fit: cover; border-radius: 10px; border: 2px solid #00209F; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    @media (max-width: 768px) { ... }
    .stTextInput > div > div > input { color: #1e2a3a !important; background-color: rgba(255,255,255,0.9) !important; border: 1px solid rgba(0,168,255,0.3) !important; border-radius: 40px !important; padding: 10px 20px !important; }
    .stTextArea > div > textarea { color: #1e2a3a !important; background-color: rgba(255,255,255,0.9) !important; border: 1px solid rgba(0,168,255,0.3) !important; border-radius: 20px !important; }
    .stRadio > div { color: #1e2a3a !important; }
    .stRadio label { color: #1e2a3a !important; }
    .stTabs [data-baseweb="tab-list"] button { color: #1e2a3a !important; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { color: #0080ff !important; font-weight: bold; }
    h1, h2, h3 { color: #0a2a44 !important; }
    .stAlert { background-color: rgba(255,255,255,0.7) !important; color: #1e2a3a !important; }
    a { color: #0080ff !important; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .home-title { text-align: center; padding: 1.5rem; background: rgba(255,255,255,0.6); border-radius: 20px; margin-bottom: 1.5rem; backdrop-filter: blur(4px); box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    .home-title h1 { margin: 0; font-size: 2.8rem; color: #0a2a44; font-weight: 700; letter-spacing: 1px; }
    .home-title p { margin: 0.3rem 0 0; opacity: 0.85; color: #1e2a3a; font-size: 1.1rem; }
    .dove-symbol { font-size: 4rem; color: #ffffff; text-shadow: 0 0 20px rgba(0,0,0,0.1); display: block; margin: 0 auto; }
    @keyframes scrollLeft {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .marquee {
        white-space: nowrap;
        overflow: hidden;
        display: block;
        animation: scrollLeft 12s linear infinite;
        font-size: 2.5rem;
        font-weight: bold;
        padding: 0.2rem 0;
    }
    .marquee span {
        display: inline-block;
        padding-right: 2rem;
    }
    .discover-card {
        background: rgba(255,255,255,0.8);
        backdrop-filter: blur(4px);
        border-radius: 16px;
        padding: 15px;
        border: 1px solid rgba(0,168,255,0.2);
        margin: 10px 0;
        transition: 0.2s;
    }
    .discover-card:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    }
    .album-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        gap: 15px;
        margin: 10px 0;
    }
    .album-card {
        background: rgba(255,255,255,0.8);
        border-radius: 12px;
        padding: 10px;
        border: 1px solid rgba(0,168,255,0.2);
        text-align: center;
        transition: 0.2s;
        cursor: pointer;
    }
    .album-card:hover {
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        transform: translateY(-3px);
    }
    .album-card img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
    }
    .album-card .album-title {
        font-weight: 600;
        margin: 8px 0 4px;
    }
    .album-card .album-meta {
        font-size: 0.8rem;
        color: #666;
    }
    .photo-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 10px;
        margin: 10px 0;
    }
    .photo-grid img {
        width: 100%;
        height: 150px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #ddd;
        transition: 0.2s;
    }
    .photo-grid img:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
""", unsafe_allow_html=True)

# ====== HELPER FUNCTIONS ======
def make_clickable(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)

def get_youtube_id(url):
    patterns = [r'(?:youtube\.com\/watch\?v=)([\w-]+)', r'(?:youtu\.be\/)([\w-]+)', r'(?:youtube\.com\/embed\/)([\w-]+)', r'(?:youtube\.com\/v\/)([\w-]+)', r'(?:youtube\.com\/shorts\/)([\w-]+)']
    for p in patterns:
        m = re.search(p, url)
        if m: return m.group(1)
    return None

def get_vimeo_id(url):
    m = re.search(r'(?:vimeo\.com\/)(\d+)', url)
    return m.group(1) if m else None

def get_dailymotion_id(url):
    m = re.search(r'(?:dailymotion\.com\/video\/)([a-zA-Z0-9]+)', url)
    return m.group(1) if m else None

def get_facebook_video_url(url):
    if 'facebook.com' in url and ('/video' in url or '/watch' in url or 'videos' in url):
        return url
    return None

def get_tiktok_id(url):
    m = re.search(r'(?:tiktok\.com\/@[\w.-]+\/video\/)(\d+)', url)
    if m: return m.group(1)
    m = re.search(r'(?:vm\.tiktok\.com\/)([\w]+)', url)
    if m: return m.group(1)
    return None

def get_twitch_url(url):
    if 'twitch.tv' in url: return url
    return None

def get_instagram_url(url):
    if 'instagram.com' in url and ('/p/' in url or '/reel/' in url):
        return url
    return None

def get_streamable_id(url):
    m = re.search(r'(?:streamable\.com\/)([a-zA-Z0-9]+)', url)
    return m.group(1) if m else None

def is_direct_video_url(url):
    video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.mpg', '.mpeg', '.m4v']
    return any(url.lower().endswith(ext) for ext in video_extensions)

def embed_video_from_url(url):
    youtube_id = get_youtube_id(url)
    if youtube_id:
        st.components.v1.html(f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{youtube_id}" frameborder="0" allow="encrypted-media" allowfullscreen></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=430)
        return True
    vimeo_id = get_vimeo_id(url)
    if vimeo_id:
        st.components.v1.html(f'<iframe src="https://player.vimeo.com/video/{vimeo_id}" width="100%" height="400" frameborder="0" allow="fullscreen" allowfullscreen></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=430)
        return True
    dailymotion_id = get_dailymotion_id(url)
    if dailymotion_id:
        st.components.v1.html(f'<iframe frameborder="0" width="100%" height="400" src="https://www.dailymotion.com/embed/video/{dailymotion_id}" allowfullscreen allow=""></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=430)
        return True
    fb_url = get_facebook_video_url(url)
    if fb_url:
        st.components.v1.html(f'<div id="fb-root"></div><script async defer src="https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v3.2"></script><div class="fb-video" data-href="{fb_url}" data-width="100%" data-allowfullscreen="true"></div><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=470)
        return True
    tiktok_id = get_tiktok_id(url)
    if tiktok_id:
        if tiktok_id.isdigit():
            st.components.v1.html(f'<blockquote class="tiktok-embed" cite="https://www.tiktok.com/@username/video/{tiktok_id}" data-video-id="{tiktok_id}" style="max-width: 605px;min-width: 325px;" ><section> <a target="_blank" title="TikTok" href="https://www.tiktok.com/@username/video/{tiktok_id}">View on TikTok</a> </section> </blockquote> <script async src="https://www.tiktok.com/embed.js"></script><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=650)
        else:
            st.components.v1.html(f'<iframe width="100%" height="600" src="{url}" frameborder="0" allowfullscreen></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=650)
        return True
    twitch_url = get_twitch_url(url)
    if twitch_url:
        try: parent = st.request.host if hasattr(st, 'request') else 'localhost'
        except: parent = 'localhost'
        if '/videos/' in twitch_url or '/clip/' in twitch_url:
            video_id = twitch_url.split('/')[-1].split('?')[0]
            embed_url = f"https://player.twitch.tv/?video={video_id}&parent={parent}"
        else:
            channel = twitch_url.split('/')[-1].split('?')[0]
            embed_url = f"https://player.twitch.tv/?channel={channel}&parent={parent}"
        st.components.v1.html(f'<iframe src="{embed_url}" height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=430)
        return True
    insta_url = get_instagram_url(url)
    if insta_url:
        st.components.v1.html(f'<iframe width="100%" height="600" src="{url}embed" frameborder="0" allowfullscreen></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=630)
        return True
    streamable_id = get_streamable_id(url)
    if streamable_id:
        st.components.v1.html(f'<iframe width="100%" height="400" src="https://streamable.com/e/{streamable_id}" frameborder="0" allowfullscreen></iframe><p style="font-size:0.8rem; color:green;">🎥 Click play to watch</p>', height=430)
        return True
    if is_direct_video_url(url):
        st.video(url, autoplay=False)
        st.markdown(f"<p style='font-size:0.8rem; color:green;'>🎥 Click play to watch</p>", unsafe_allow_html=True)
        return True
    return False

# ---- Profile & Auth ----
def get_or_create_profile(user_id, identifier, email=None):
    if supabase is None:
        return None
    try:
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        else:
            default_name = identifier.split('@')[0] if '@' in identifier else f"User {identifier[-4:]}"
            new_profile = {
                "id": user_id,
                "full_name": default_name,
                "avatar_url": None,
                "bio": "",
                "location": "",
                "is_live": False,
                "moncash_phone": None,
                "natcash_phone": None,
                "email": email if email else "",
                "profile_visibility": "public",  # default public
                "whatsapp_phone": None,
                "join_date": datetime.now().isoformat(),
                "is_banned": False,
                "ban_reason": None,
                "last_active": datetime.now().isoformat()
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

# ---- Ban/Unban ----
def ban_user(user_id, reason=""):
    if supabase is None:
        return False, "Supabase not configured."
    try:
        supabase.table("profiles").update({"is_banned": True, "ban_reason": reason}).eq("id", user_id).execute()
        try:
            supabase.table("notifications").insert({
                "user_id": user_id,
                "type": "ban",
                "message": f"🚫 Your account has been banned. Reason: {reason if reason else 'Violation of platform rules.'}",
                "read": False
            }).execute()
        except Exception:
            pass
        return True, "User banned successfully."
    except Exception as e:
        return False, str(e)

def unban_user(user_id):
    if supabase is None:
        return False, "Supabase not configured."
    try:
        supabase.table("profiles").update({"is_banned": False, "ban_reason": None}).eq("id", user_id).execute()
        try:
            supabase.table("notifications").insert({
                "user_id": user_id,
                "type": "unban",
                "message": "✅ Your account was restored. You can now log in again.",
                "read": False
            }).execute()
        except Exception:
            pass
        return True, "User unbanned successfully."
    except Exception as e:
        return False, str(e)

# ====== RESILIENT QUERY HELPERS ======
def safe_select_profiles(fields=None, **filters):
    """
    Try to select profiles with optional extra fields (profile_visibility, email, whatsapp_phone).
    If those columns don't exist, fall back to basic fields.
    """
    if supabase is None:
        return []
    if fields is None:
        fields = ["id", "full_name", "avatar_url", "is_banned", "ban_reason", "join_date", "last_active"]
    try:
        query = supabase.table("profiles").select(",".join(fields))
        for col, val in filters.items():
            query = query.eq(col, val)
        resp = query.execute()
        return resp.data if resp.data else []
    except Exception as e:
        # If column error (42703), try without extra fields
        if "42703" in str(e):
            base_fields = ["id", "full_name", "avatar_url", "is_banned", "ban_reason", "join_date", "last_active"]
            # Also include moncash and natcash if they exist, but we'll just use basic
            query = supabase.table("profiles").select(",".join(base_fields))
            for col, val in filters.items():
                query = query.eq(col, val)
            resp = query.execute()
            return resp.data if resp.data else []
        else:
            raise

def get_all_users():
    """Get all users, safely handling missing columns."""
    if supabase is None:
        return []
    try:
        # Try with extra fields first
        fields = ["id", "full_name", "avatar_url", "is_banned", "ban_reason", "join_date", "last_active", "profile_visibility", "email", "whatsapp_phone"]
        return safe_select_profiles(fields=fields)
    except Exception:
        # Fallback to basic fields
        return safe_select_profiles()

def search_users(query):
    if supabase is None or not st.session_state.user:
        return []
    try:
        fields = ["id", "full_name", "avatar_url", "last_active", "profile_visibility", "email", "whatsapp_phone"]
        query_builder = supabase.table("profiles").select(",".join(fields)).neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(50)
        resp = query_builder.execute()
        return resp.data if resp.data else []
    except Exception as e:
        if "42703" in str(e):
            # Fallback: without extra fields
            fields = ["id", "full_name", "avatar_url", "last_active"]
            query_builder = supabase.table("profiles").select(",".join(fields)).neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(50)
            resp = query_builder.execute()
            return resp.data if resp.data else []
        else:
            st.session_state.last_error = f"Search failed: {e}"
            return []

# ---- Uploads with compression ----
def compress_image(file_bytes, max_size_kb=200, quality=70, max_width=1024):
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed = output.getvalue()
        while len(compressed) > max_size_kb * 1024 and quality > 20:
            quality -= 10
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed = output.getvalue()
        return compressed, 'image/jpeg'
    except Exception:
        return file_bytes, 'image/jpeg'

def upload_avatar(user_id, image_file):
    if supabase is None:
        return upload_avatar_base64(image_file)
    if not ensure_bucket_exists("avatars"):
        return upload_avatar_base64(image_file)
    try:
        original_bytes = image_file.getvalue()
        compressed_bytes, content_type = compress_image(original_bytes, max_size_kb=150)
        ext = 'jpg'
        file_name = f"{user_id}_{int(time.time())}.{ext}"
        supabase.storage.from_("avatars").upload(file_name, compressed_bytes, {"content-type": content_type})
        return supabase.storage.from_("avatars").get_public_url(file_name)
    except Exception:
        return upload_avatar_base64(image_file)

def upload_avatar_base64(image_file):
    try:
        file_bytes = image_file.getvalue()
        b64 = base64.b64encode(file_bytes).decode('utf-8')
        content_type = image_file.type
        if content_type.startswith('image'):
            return f"data:{content_type};base64,{b64}"
        return None
    except Exception:
        return None

def upload_post_media(user_id, file):
    if supabase is None:
        return upload_media_base64(file)
    if not ensure_bucket_exists("post_media"):
        return upload_media_base64(file)
    try:
        content_type = file.type
        if content_type.startswith('image'):
            original_bytes = file.getvalue()
            compressed_bytes, content_type = compress_image(original_bytes, max_size_kb=300)
            ext = 'jpg'
        else:
            compressed_bytes = file.getvalue()
            ext = file.name.split('.')[-1]
        timestamp = int(time.time())
        random_hash = hashlib.md5(file.name.encode()).hexdigest()[:8]
        file_name = f"post_{user_id}_{timestamp}_{random_hash}.{ext}"
        supabase.storage.from_("post_media").upload(
            file_name,
            compressed_bytes,
            {"content-type": content_type}
        )
        public_url = supabase.storage.from_("post_media").get_public_url(file_name)
        media_type = "video" if content_type.startswith("video") else "image"
        return {"url": public_url, "type": media_type}
    except Exception:
        return upload_media_base64(file)

def upload_media_base64(file):
    try:
        file_bytes = file.getvalue()
        b64 = base64.b64encode(file_bytes).decode('utf-8')
        content_type = file.type
        data_url = f"data:{content_type};base64,{b64}"
        media_type = "video" if content_type.startswith("video") else "image"
        return {"url": data_url, "type": media_type}
    except Exception:
        return None

def upload_chat_media(user_id, file):
    if supabase is None:
        return upload_media_base64(file)
    if not ensure_bucket_exists("chat_media"):
        return upload_media_base64(file)
    try:
        content_type = file.type
        if content_type.startswith('image'):
            original_bytes = file.getvalue()
            compressed_bytes, content_type = compress_image(original_bytes, max_size_kb=200)
            ext = 'jpg'
        else:
            compressed_bytes = file.getvalue()
            ext = file.name.split('.')[-1]
        timestamp = int(time.time())
        random_hash = hashlib.md5(file.name.encode()).hexdigest()[:8]
        file_name = f"chat_{user_id}_{timestamp}_{random_hash}.{ext}"
        supabase.storage.from_("chat_media").upload(
            file_name,
            compressed_bytes,
            {"content-type": content_type}
        )
        public_url = supabase.storage.from_("chat_media").get_public_url(file_name)
        media_type = "video" if content_type.startswith("video") else "image"
        return {"url": public_url, "type": media_type}
    except Exception:
        return upload_media_base64(file)

# ---- POST CRUD ----
def delete_post(post_id):
    if supabase is None:
        return False
    try:
        supabase.table("posts").delete().eq("id", post_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error deleting post: {e}"
        return False

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

def toggle_post_visibility(post_id, make_public):
    if supabase is None:
        return False, "Supabase not configured."
    try:
        supabase.table("posts").update({"is_public": make_public}).eq("id", post_id).execute()
        return True, f"Post visibility updated to {'Public' if make_public else 'Private'}."
    except Exception as e:
        return False, str(e)

# ---- Online status helpers ----
def update_last_active(user_id):
    if supabase is None:
        return
    try:
        supabase.table("profiles").update({"last_active": datetime.now().isoformat()}).eq("id", user_id).execute()
    except Exception:
        pass

def is_user_online(last_active_str, threshold_minutes=5):
    if not last_active_str:
        return False
    try:
        last_active = datetime.fromisoformat(last_active_str.replace('Z', '+00:00'))
        now = datetime.now(last_active.tzinfo)
        return (now - last_active).total_seconds() < threshold_minutes * 60
    except Exception:
        return False

def display_avatar_and_followers(avatar_url, user_id, size=50, profile=None):
    online = False
    if profile is not None:
        online = is_user_online(profile.get('last_active'))
    elif st.session_state.user and user_id == st.session_state.user.id:
        online = is_user_online(st.session_state.profile.get('last_active')) if st.session_state.profile else False
    dot_class = "online-indicator" if online else "offline-indicator"
    dot_html = f'<span class="{dot_class}"></span>'
    if avatar_url:
        st.markdown(f'<img src="{avatar_url}" class="profile-avatar" style="width:{size}px; height:{size}px;" />', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="profile-avatar" style="width:{size}px; height:{size}px; background:#ccc; display:flex; align-items:center; justify-content:center; font-size:{size*0.6}px;">👤</div>', unsafe_allow_html=True)
    st.markdown(dot_html, unsafe_allow_html=True)
    if user_id == st.session_state.user.id:
        st.caption("1miFollowers")
    else:
        st.caption("1kFollowers")

def get_user_post_count(user_id, public_only=False):
    if supabase is None:
        return 0
    try:
        query = supabase.table("posts").select("id", count="exact").eq("user_id", user_id)
        if public_only:
            query = query.eq("is_public", True)
        resp = query.execute()
        return resp.count if hasattr(resp, 'count') else len(resp.data or [])
    except Exception:
        return 0

@st.cache_data(ttl=60, show_spinner=False)
def load_posts_cached(user_id=None, author_id=None, include_private=False):
    if supabase is None:
        return []
    try:
        if author_id is not None:
            query = supabase.table("posts").select("*").eq("user_id", author_id)
            if not include_private:
                query = query.eq("is_public", True)
            posts = query.order("created_at", desc=True).execute().data or []
        elif user_id is not None:
            public_resp = supabase.table("posts").select("*").eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            private_resp = supabase.table("posts").select("*").eq("is_public", False).eq("user_id", user_id).order("created_at", desc=True).execute()
            posts = (public_resp.data or []) + (private_resp.data or [])
            seen = set()
            unique = []
            for p in posts:
                if p["id"] not in seen:
                    seen.add(p["id"])
                    unique.append(p)
            posts = unique
            posts.sort(key=lambda x: x['created_at'], reverse=True)
        else:
            resp = supabase.table("posts").select("*").eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            posts = resp.data or []

        user_ids = {p["user_id"] for p in posts}
        profiles = {}
        if user_ids:
            profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, is_live, last_active").in_("id", list(user_ids)).execute()
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p

        for post in posts:
            p = profiles.get(post["user_id"], {})
            post["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "is_live": p.get("is_live", False),
                "last_active": p.get("last_active"),
            }
            post["media_urls"] = post.get("media_urls", [])
            reactions_resp = supabase.table("reactions").select("emoji").eq("post_id", post["id"]).execute()
            counts = {}
            for r in reactions_resp.data or []:
                emoji = r["emoji"]
                counts[emoji] = counts.get(emoji, 0) + 1
            post["reactions"] = counts
            comments_resp = supabase.table("comments").select("id", count="exact").eq("post_id", post["id"]).execute()
            post["comment_count"] = comments_resp.count if hasattr(comments_resp, 'count') else 0

        return posts
    except Exception as e:
        st.session_state.last_error = f"Error loading posts: {e}"
        return []

# ---- NEW: Shuffle feed like a cord ----
def shuffle_feed_posts(posts):
    """Interleave posts from different users so that each user's content gets visibility."""
    if not posts:
        return []
    from collections import defaultdict
    groups = defaultdict(list)
    for p in posts:
        groups[p['user_id']].append(p)
    # Sort each user's posts by created_at (most recent first)
    for uid in groups:
        groups[uid].sort(key=lambda x: x['created_at'], reverse=True)
    result = []
    # While there are any posts left
    while any(groups.values()):
        # Get active user IDs (those with remaining posts)
        active_users = [uid for uid, lst in groups.items() if lst]
        # Shuffle the order of users each round
        random.shuffle(active_users)
        # Take one post from each user in the shuffled order
        for uid in active_users:
            if groups[uid]:
                result.append(groups[uid].pop(0))
    return result

def load_posts():
    user_id = st.session_state.user.id if st.session_state.user else None
    posts = load_posts_cached(user_id=user_id)
    if posts:
        posts = shuffle_feed_posts(posts)
    return posts

def load_user_posts(user_id, include_private=False):
    return load_posts_cached(author_id=user_id, include_private=include_private)

# --- FIXED: Removed post_type column ---
def create_post(user_id, content, media_files=None, is_public=True, existing_media_urls=None):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        media_urls = []
        if media_files:
            progress_bar = st.progress(0, text="Uploading media...")
            for i, f in enumerate(media_files):
                progress_bar.progress((i + 1) / len(media_files), text=f"Uploading {i+1}/{len(media_files)}...")
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
            progress_bar.empty()
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
            st.success(t("post"))
            return True
        else:
            st.session_state.last_error = "Post insertion failed."
            return False
    except Exception as e:
        st.session_state.last_error = f"Error creating post: {e}"
        return False

def update_post(post_id, user_id, content, media_files=None, existing_media_urls=None):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        media_urls = existing_media_urls or []
        if media_files:
            progress_bar = st.progress(0, text="Uploading media...")
            for i, f in enumerate(media_files):
                progress_bar.progress((i + 1) / len(media_files), text=f"Uploading {i+1}/{len(media_files)}...")
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
            progress_bar.empty()
        post_data = {"content": content, "media_urls": media_urls, "updated_at": datetime.now().isoformat()}
        supabase.table("posts").update(post_data).eq("id", post_id).eq("user_id", user_id).execute()
        st.cache_data.clear()
        st.session_state.posts = load_posts()
        st.success("Post updated!")
        return True
    except Exception as e:
        st.session_state.last_error = f"Error updating post: {e}"
        return False

def toggle_reaction(post_id, user_id, emoji):
    if supabase is None:
        return False
    try:
        check = supabase.table("reactions").select("id").eq("post_id", post_id).eq("user_id", user_id).eq("emoji", emoji).execute()
        if check.data:
            supabase.table("reactions").delete().eq("post_id", post_id).eq("user_id", user_id).eq("emoji", emoji).execute()
        else:
            supabase.table("reactions").insert({"post_id": post_id, "user_id": user_id, "emoji": emoji}).execute()
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
            "content": "(Shared post)",
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

# ---- Comments ----
def load_comments(post_id):
    if supabase is None:
        return []
    try:
        resp = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at").execute()
        comments = resp.data or []
        user_ids = {c["user_id"] for c in comments}
        profiles = {}
        if user_ids:
            profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, last_active").in_("id", list(user_ids)).execute()
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p
        for c in comments:
            p = profiles.get(c["user_id"], {})
            c["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "last_active": p.get("last_active"),
            }
        return comments
    except Exception as e:
        st.session_state.last_error = f"Error loading comments: {e}"
        return []

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

# ---- Live Sessions ----
def load_live_sessions():
    if supabase is None:
        return []
    try:
        response = supabase.table("live_sessions").select("*").eq("is_live", True).order("started_at", desc=True).execute()
        sessions = response.data or []
        user_ids = {s["user_id"] for s in sessions}
        profiles = {}
        if user_ids:
            try:
                profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone, natcash_phone, last_active").in_("id", list(user_ids)).execute()
                use_natcash = True
            except Exception:
                profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone, last_active").in_("id", list(user_ids)).execute()
                use_natcash = False
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p
                if not use_natcash:
                    profiles[p["id"]]["natcash_phone"] = None
        for s in sessions:
            p = profiles.get(s["user_id"], {})
            s["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "moncash_phone": p.get("moncash_phone"),
                "natcash_phone": p.get("natcash_phone") if "natcash_phone" in p else None,
                "last_active": p.get("last_active"),
            }
            if "stream_method" not in s:
                s["stream_method"] = "external"
        return sessions
    except Exception:
        return []

def get_user_live_sessions(user_id):
    if supabase is None:
        return []
    try:
        response = supabase.table("live_sessions").select("*").eq("user_id", user_id).order("started_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        st.session_state.last_error = f"Error loading user live sessions: {e}"
        return []

def create_live_session(title, platform, method='external'):
    if supabase is None or st.session_state.user is None:
        st.session_state.last_error = "Cannot start live session."
        return None
    try:
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
            # Create a post on feed about the live session (no post_type)
            create_post(st.session_state.user.id, f"🔴 I'm live: {title}", is_public=True)
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
        supabase.table("live_sessions").update({"stream_url": stream_url}).eq("id", session_id).execute()
        st.session_state.live_sessions = load_live_sessions()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error updating stream URL: {e}"
        return False

def end_live_session(session_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_sessions").update({"is_live": False, "ended_at": datetime.now().isoformat()}).eq("id", session_id).execute()
        supabase.table("profiles").update({"is_live": False}).eq("id", st.session_state.user.id).execute()
        st.session_state.profile["is_live"] = False
        st.session_state.live_sessions = load_live_sessions()
        st.session_state.stream_key = None
        st.session_state.selected_platform = None
        return True
    except Exception as e:
        st.session_state.last_error = f"Error ending live session: {e}"
        return False

def get_live_session(session_id):
    if supabase is None:
        return None
    try:
        response = supabase.table("live_sessions").select("*").eq("id", session_id).single().execute()
        session = response.data
        if not session:
            return None
        try:
            profile_resp = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone, natcash_phone, last_active").eq("id", session["user_id"]).single().execute()
            profile = profile_resp.data or {}
        except Exception:
            profile_resp = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone, last_active").eq("id", session["user_id"]).single().execute()
            profile = profile_resp.data or {}
            profile["natcash_phone"] = None
        session["profiles"] = {
            "full_name": profile.get("full_name", "Unknown"),
            "avatar_url": profile.get("avatar_url"),
            "moncash_phone": profile.get("moncash_phone"),
            "natcash_phone": profile.get("natcash_phone") if "natcash_phone" in profile else None,
            "last_active": profile.get("last_active"),
        }
        if "stream_method" not in session:
            session["stream_method"] = "external"
        return session
    except Exception as e:
        st.session_state.last_error = f"Error fetching live session: {e}"
        return None

def send_gift(session_id, sender_id, recipient_id, amount, currency):
    if supabase is None:
        return False, "Supabase not configured"
    try:
        rate = st.session_state.exchange_rate
        amount_htg = amount * rate if currency == "USD" else amount
        sender_name = st.session_state.profile["full_name"]
        gift_data = {
            "session_id": session_id,
            "sender_id": sender_id,
            "sender_name": sender_name,
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
        supabase.table("live_gifts").update({"status": "completed"}).eq("id", gift_id).execute()
        try:
            supabase.table("notifications").insert({
                "user_id": recipient_id,
                "type": "gift",
                "message": f"🎁 You received a gift of {amount} {currency} from {sender_name}!",
                "read": False
            }).execute()
        except Exception:
            pass
        return True, "Gift sent successfully!"
    except Exception as e:
        st.session_state.last_error = f"Error sending gift: {e}"
        return False, str(e)

def load_gifts_for_session(session_id):
    if supabase is None:
        return []
    try:
        resp = supabase.table("live_gifts").select("*").eq("session_id", session_id).eq("status", "completed").order("created_at").execute()
        gifts = resp.data or []
        for g in gifts:
            g['sender'] = {'full_name': g.get('sender_name', 'Someone'), 'avatar_url': None}
        return gifts
    except Exception as e:
        st.session_state.last_error = f"Error loading gifts: {e}"
        return []

# ---- Friends / Chat / Notifications ----
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
        try:
            supabase.table("notifications").insert({
                "user_id": receiver_id,
                "type": "friend_request",
                "message": f"{sender_name} sent you a friend request",
                "read": False
            }).execute()
        except Exception:
            pass
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
            try:
                supabase.table("notifications").insert({
                    "user_id": req.data["sender_id"],
                    "type": "friend_accept",
                    "related_id": request_id,
                    "message": f"{receiver_name} accepted your friend request",
                    "read": False
                }).execute()
            except Exception:
                pass
            # Force reload of friend data to update the list
            load_friend_data()
        return True, f"Request {new_status}"
    except Exception as e:
        return False, str(e)

# ====== FIXED load_friend_data with retry and error handling ======
def load_friend_data():
    """Load friend requests and friends with retry and error handling."""
    if supabase is None or not st.session_state.user:
        return

    user_id = st.session_state.user.id
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            # Fetch pending friend requests (received)
            pending_resp = supabase.table("friend_requests") \
                .select("id, sender_id, receiver_id, status, created_at") \
                .eq("receiver_id", user_id) \
                .eq("status", "pending") \
                .execute()
            pending_raw = pending_resp.data or []

            # Fetch accepted friend requests (sent by user)
            sent_resp = supabase.table("friend_requests") \
                .select("id, sender_id, receiver_id, status, created_at") \
                .eq("sender_id", user_id) \
                .eq("status", "accepted") \
                .execute()
            # Fetch accepted friend requests (received by user)
            received_resp = supabase.table("friend_requests") \
                .select("id, sender_id, receiver_id, status, created_at") \
                .eq("receiver_id", user_id) \
                .eq("status", "accepted") \
                .execute()

            accepted_raw = (sent_resp.data or []) + (received_resp.data or [])

            # Collect all user IDs to fetch profiles
            user_ids = set()
            for req in pending_raw:
                user_ids.add(req["sender_id"])
            for req in accepted_raw:
                user_ids.add(req["sender_id"])
                user_ids.add(req["receiver_id"])
            user_ids.discard(user_id)

            # Fetch profiles for those users safely (with fallback for missing columns)
            profiles = {}
            if user_ids:
                try:
                    # Try to get extra fields
                    fields = ["id", "full_name", "avatar_url", "last_active", "profile_visibility", "email", "whatsapp_phone"]
                    profiles_resp = supabase.table("profiles") \
                        .select(",".join(fields)) \
                        .in_("id", list(user_ids)) \
                        .execute()
                    for p in profiles_resp.data or []:
                        profiles[p["id"]] = p
                except Exception as e:
                    if "42703" in str(e):
                        # Fallback: without extra fields
                        fields = ["id", "full_name", "avatar_url", "last_active"]
                        profiles_resp = supabase.table("profiles") \
                            .select(",".join(fields)) \
                            .in_("id", list(user_ids)) \
                            .execute()
                        for p in profiles_resp.data or []:
                            # add default values for missing fields
                            p["profile_visibility"] = "public"
                            p["email"] = None
                            p["whatsapp_phone"] = None
                            profiles[p["id"]] = p
                    else:
                        raise

            # Build pending requests list
            pending_requests = []
            for req in pending_raw:
                sender_id = req["sender_id"]
                sender = profiles.get(sender_id, {})
                pending_requests.append({
                    "id": req["id"],
                    "sender": {
                        "id": sender_id,
                        "full_name": sender.get("full_name", "Unknown"),
                        "avatar_url": sender.get("avatar_url"),
                        "last_active": sender.get("last_active"),
                        "profile_visibility": sender.get("profile_visibility", "public"),
                    },
                    "receiver_id": req["receiver_id"],
                    "status": req["status"],
                })
            st.session_state.friend_requests = pending_requests

            # Build friends list
            friends = []
            seen = set()
            for req in accepted_raw:
                other_id = req["receiver_id"] if req["sender_id"] == user_id else req["sender_id"]
                if other_id in seen:
                    continue
                seen.add(other_id)
                other = profiles.get(other_id, {})
                friends.append({
                    "id": other_id,
                    "full_name": other.get("full_name", "Unknown"),
                    "avatar_url": other.get("avatar_url"),
                    "last_active": other.get("last_active"),
                    "profile_visibility": other.get("profile_visibility", "public"),
                    "email": other.get("email"),
                    "whatsapp_phone": other.get("whatsapp_phone"),
                })
            st.session_state.friends = friends

            return

        except Exception as e:
            st.session_state.last_error = f"Error loading friend data (attempt {attempt+1}/{max_retries}): {e}"
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                st.session_state.friend_requests = []
                st.session_state.friends = []
                st.session_state.last_error = f"Failed to load friend data after {max_retries} attempts: {e}"
                st.warning("Could not load friends data. Please refresh the page.")

# ---- Search users ----
def search_users(query):
    if supabase is None or not st.session_state.user:
        return []
    try:
        fields = ["id", "full_name", "avatar_url", "last_active", "profile_visibility", "email", "whatsapp_phone"]
        query_builder = supabase.table("profiles").select(",".join(fields)).neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(50)
        resp = query_builder.execute()
        results = resp.data if resp.data else []
        # Ensure default values for missing fields
        for r in results:
            r.setdefault("profile_visibility", "public")
            r.setdefault("email", None)
            r.setdefault("whatsapp_phone", None)
        return results
    except Exception as e:
        if "42703" in str(e):
            # Fallback: without extra fields
            fields = ["id", "full_name", "avatar_url", "last_active"]
            query_builder = supabase.table("profiles").select(",".join(fields)).neq("id", st.session_state.user.id).ilike("full_name", f"%{query}%").limit(50)
            resp = query_builder.execute()
            results = resp.data if resp.data else []
            for r in results:
                r["profile_visibility"] = "public"
                r["email"] = None
                r["whatsapp_phone"] = None
            return results
        else:
            st.session_state.last_error = f"Search failed: {e}"
            return []

def get_all_users():
    """Get all users, safely handling missing columns."""
    if supabase is None:
        return []
    try:
        fields = ["id", "full_name", "avatar_url", "is_banned", "ban_reason", "join_date", "last_active", "profile_visibility", "email", "whatsapp_phone"]
        resp = supabase.table("profiles").select(",".join(fields)).order("full_name").execute()
        results = resp.data if resp.data else []
        for r in results:
            r.setdefault("profile_visibility", "public")
            r.setdefault("email", None)
            r.setdefault("whatsapp_phone", None)
        return results
    except Exception as e:
        if "42703" in str(e):
            fields = ["id", "full_name", "avatar_url", "is_banned", "ban_reason", "join_date", "last_active"]
            resp = supabase.table("profiles").select(",".join(fields)).order("full_name").execute()
            results = resp.data if resp.data else []
            for r in results:
                r["profile_visibility"] = "public"
                r["email"] = None
                r["whatsapp_phone"] = None
            return results
        else:
            st.session_state.last_error = f"Error loading users: {e}"
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
        try:
            supabase.table("notifications").insert({
                "user_id": receiver_id,
                "type": "message",
                "message": f"New message from {sender_name}",
                "read": False
            }).execute()
        except Exception:
            pass
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

def start_call(room_id=None):
    if not room_id:
        room_id = hashlib.md5(f"{st.session_state.user.id}_{time.time()}".encode()).hexdigest()[:10]
    st.session_state.call_room = room_id
    st.session_state.in_call = True
    # Log the call in video_calls table for Owner monitoring
    if supabase:
        try:
            supabase.table("video_calls").insert({
                "user_id": st.session_state.user.id,
                "room": room_id,
                "started_at": datetime.now().isoformat(),
                "is_active": True
            }).execute()
        except Exception:
            pass

def end_call():
    if st.session_state.in_call and st.session_state.call_room:
        # Update video_calls record
        if supabase:
            try:
                supabase.table("video_calls").update({"ended_at": datetime.now().isoformat(), "is_active": False}).eq("room", st.session_state.call_room).eq("is_active", True).execute()
            except Exception:
                pass
    st.session_state.in_call = False
    st.session_state.call_room = None
    st.session_state.call_ringing = False
    st.session_state.call_initiated_time = None

# ---- NEW: Initiate a call with ring simulation ----
def initiate_call(target_user_id):
    """Initiate a call to another user, create room, send notification, and start ringing."""
    if st.session_state.call_ringing:
        st.warning("You already have an ongoing call or ringing.")
        return
    room = hashlib.md5(f"{st.session_state.user.id}_{target_user_id}_{time.time()}".encode()).hexdigest()[:10]
    # Send a notification to the target user
    try:
        supabase.table("notifications").insert({
            "user_id": target_user_id,
            "type": "call_request",
            "message": f"📞 {st.session_state.profile['full_name']} is calling you. Room: {room}",
            "read": False,
            "created_at": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"Failed to send call notification: {e}")
        return
    # Start the call for the current user (they will join the room)
    start_call(room)
    st.session_state.call_target_user = target_user_id
    st.session_state.call_ringing = True
    st.session_state.call_initiated_time = time.time()
    st.rerun()

def check_call_status():
    """Check if the call has been ringing for more than 30 seconds and simulate 'unavailable'."""
    if st.session_state.call_ringing and st.session_state.call_initiated_time:
        elapsed = time.time() - st.session_state.call_initiated_time
        if elapsed > 30:  # 30 seconds = 5 rings (approx 6 sec per ring)
            # Mark as unavailable
            st.session_state.call_ringing = False
            st.session_state.call_initiated_time = None
            # End the call room
            end_call()
            st.warning(t("call_unavailable"))
            st.rerun()

# ---- Owner Space helpers ----
def ensure_owner_state_table():
    if supabase is None:
        return False
    try:
        supabase.table("owner_state").select("id").limit(1).execute()
        return True
    except Exception:
        return False

def get_last_seen_signup():
    if supabase is None:
        return datetime(2020, 1, 1)
    try:
        if not ensure_owner_state_table():
            return datetime.now() - timedelta(days=365)
        resp = supabase.table("owner_state").select("last_seen_signup").eq("id", 1).execute()
        if resp.data:
            return datetime.fromisoformat(resp.data[0]["last_seen_signup"].replace('Z', '+00:00'))
        else:
            try:
                supabase.table("owner_state").insert({"id": 1, "last_seen_signup": datetime.now().isoformat()}).execute()
            except:
                pass
            return datetime.now() - timedelta(days=365)
    except Exception:
        return datetime(2020, 1, 1)

def update_last_seen_signup():
    if supabase is None:
        return
    try:
        if not ensure_owner_state_table():
            return
        supabase.table("owner_state").update({"last_seen_signup": datetime.now().isoformat()}).eq("id", 1).execute()
    except Exception:
        pass

def get_new_users(since):
    if supabase is None:
        return []
    try:
        since_str = since.isoformat()
        resp = supabase.table("profiles").select("id, full_name, avatar_url, join_date, last_active").gt("join_date", since_str).order("join_date").execute()
        return resp.data
    except Exception:
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
    except Exception:
        pass

# ---- Photo Album functions ----
def create_album(user_id, title, description, visibility='public'):
    if supabase is None:
        return None
    try:
        album_data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "visibility": visibility,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        result = supabase.table("photo_albums").insert(album_data).execute()
        if result.data:
            # Create a post about the album (no post_type)
            album_id = result.data[0]["id"]
            content = f"📸 New album: {title}"
            if visibility == 'public':
                create_post(user_id, content, is_public=True)
            else:
                create_post(user_id, content, is_public=False)
            return result.data[0]
        return None
    except Exception as e:
        st.session_state.last_error = f"Error creating album: {e}"
        return None

def upload_album_photos(album_id, files):
    if supabase is None:
        return False
    try:
        for file in files:
            # Upload to album_photos bucket (we'll create a dedicated bucket)
            content_type = file.type
            if content_type.startswith('image'):
                original_bytes = file.getvalue()
                compressed_bytes, content_type = compress_image(original_bytes, max_size_kb=500)
                ext = 'jpg'
            else:
                compressed_bytes = file.getvalue()
                ext = file.name.split('.')[-1]
            timestamp = int(time.time())
            random_hash = hashlib.md5(file.name.encode()).hexdigest()[:8]
            file_name = f"album_{album_id}_{timestamp}_{random_hash}.{ext}"
            # Ensure bucket exists (we'll assume 'album_photos' bucket is created)
            if not ensure_bucket_exists("album_photos"):
                # fallback: store in post_media bucket
                bucket = "post_media"
            else:
                bucket = "album_photos"
            supabase.storage.from_(bucket).upload(
                file_name,
                compressed_bytes,
                {"content-type": content_type}
            )
            public_url = supabase.storage.from_(bucket).get_public_url(file_name)
            # Insert record
            supabase.table("album_photos").insert({
                "album_id": album_id,
                "photo_url": public_url,
                "uploaded_at": datetime.now().isoformat()
            }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error uploading photos: {e}"
        return False

def get_user_albums(user_id, include_private=False):
    if supabase is None:
        return []
    try:
        query = supabase.table("photo_albums").select("*").eq("user_id", user_id)
        if not include_private:
            query = query.eq("visibility", "public")
        albums = query.order("created_at", desc=True).execute().data or []
        # For each album, get cover photo (first photo)
        for album in albums:
            photos = supabase.table("album_photos").select("photo_url").eq("album_id", album["id"]).limit(1).execute().data or []
            album["cover_photo"] = photos[0]["photo_url"] if photos else None
        return albums
    except Exception as e:
        st.session_state.last_error = f"Error loading albums: {e}"
        return []

def get_album_photos(album_id):
    if supabase is None:
        return []
    try:
        photos = supabase.table("album_photos").select("photo_url").eq("album_id", album_id).order("uploaded_at").execute().data or []
        return photos
    except Exception as e:
        st.session_state.last_error = f"Error loading album photos: {e}"
        return []

def delete_album(album_id):
    if supabase is None:
        return False
    try:
        # Delete photos first
        photos = supabase.table("album_photos").select("id").eq("album_id", album_id).execute().data or []
        for p in photos:
            supabase.table("album_photos").delete().eq("id", p["id"]).execute()
        # Delete album
        supabase.table("photo_albums").delete().eq("id", album_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error deleting album: {e}"
        return False

def toggle_album_visibility(album_id, visibility):
    if supabase is None:
        return False
    try:
        supabase.table("photo_albums").update({"visibility": visibility, "updated_at": datetime.now().isoformat()}).eq("id", album_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error toggling album visibility: {e}"
        return False

def get_all_albums(include_private=True):
    """For OwnerSpace: get all albums (public and private)."""
    if supabase is None:
        return []
    try:
        albums = supabase.table("photo_albums").select("*").order("created_at", desc=True).execute().data or []
        # Get user info
        user_ids = set(a["user_id"] for a in albums)
        profiles = {}
        if user_ids:
            profiles_resp = supabase.table("profiles").select("id, full_name").in_("id", list(user_ids)).execute().data or []
            for p in profiles_resp:
                profiles[p["id"]] = p["full_name"]
        for album in albums:
            album["owner_name"] = profiles.get(album["user_id"], "Unknown")
            photos = supabase.table("album_photos").select("photo_url").eq("album_id", album["id"]).limit(1).execute().data or []
            album["cover_photo"] = photos[0]["photo_url"] if photos else None
        return albums
    except Exception as e:
        st.session_state.last_error = f"Error loading all albums: {e}"
        return []

# ---- Video call monitoring (Owner) ----
def get_active_video_calls():
    if supabase is None:
        return []
    try:
        calls = supabase.table("video_calls").select("*, profiles!video_calls_user_id_fkey(full_name)").eq("is_active", True).order("started_at", desc=True).execute().data or []
        return calls
    except Exception as e:
        st.session_state.last_error = f"Error fetching video calls: {e}"
        return []

# ---- Network and auth ----
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
        st.error("Registration unavailable (Supabase not configured).")
        return False
    try:
        user = supabase.auth.sign_up({"email": email, "password": password, "options": {"data": {"full_name": full_name}}})
        if user.user:
            if user.user.identities and len(user.user.identities) > 0:
                st.success("Sign-up successful! Please check your email to confirm your account before logging in. (Check spam folder if not received.)")
            else:
                st.success("Sign-up successful! You can now log in.")
            return True
        else:
            st.error("Sign-up failed: No user returned.")
            return False
    except Exception as e:
        error_str = str(e)
        if "User already registered" in error_str:
            st.error("This email is already registered. Please log in instead.")
        elif "Email rate limit exceeded" in error_str:
            st.error("Too many sign-up attempts from this email. Please wait a few minutes and try again, or use a different email.")
        elif "Password should be at least 6 characters" in error_str.lower():
            st.error("Password must be at least 6 characters long.")
        elif "Invalid email" in error_str.lower():
            st.error("Please enter a valid email address.")
        else:
            st.error(f"Sign-up failed: {error_str}")
        return False

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
        error_str = str(e)
        if "Unsupported phone provider" in error_str:
            st.error("Phone authentication is not enabled in your Supabase project. Please use email sign-up instead, or contact the administrator to enable phone auth.")
        else:
            st.error(f"Failed to send OTP: {error_str}")
        return False

def verify_phone_otp(raw_phone, token, remember=False):
    if supabase is None:
        st.error("Supabase not configured.")
        return False
    try:
        phone = format_phone(raw_phone)
        session = supabase.auth.verify_otp({"phone": phone, "token": token, "type": "sms"})
        if session.user:
            profile = get_or_create_profile(session.user.id, phone, session.user.email)
            if profile and profile.get("is_banned"):
                st.error("🚫 Your account has been banned. Contact support if you believe this is an error.")
                return False
            st.session_state.logged_in = True
            st.session_state.user = session.user
            if session.session:
                st.session_state.refresh_token = session.session.refresh_token
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.cache_data.clear()
            st.session_state.posts = load_posts()
            st.session_state.live_sessions = load_live_sessions()
            st.session_state.phone_otp_sent = False
            st.session_state.temp_phone = ""
            if remember and session.session:
                set_cookie("sb_refresh_token", session.session.refresh_token, 30)
            st.rerun()
            return True
        else:
            st.error("Verification failed – no user returned.")
            return False
    except Exception as e:
        st.error(f"Verification failed: {e}")
        return False

def logout():
    set_cookie("sb_refresh_token", "", -1)
    if supabase:
        supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.refresh_token = None
    st.session_state.owner_space_access = False
    st.session_state.phone_otp_sent = False
    st.session_state.temp_phone = ""
    st.session_state.viewing_live = None
    st.session_state.viewing_profile = None
    st.session_state.selected_chat = None
    st.session_state.call_room = None
    st.session_state.in_call = False
    st.session_state.call_ringing = False
    st.session_state.call_initiated_time = None
    st.session_state.delete_confirm = None
    st.session_state.last_error = None
    st.session_state.replying_to = {}
    st.session_state.notifications = []
    st.session_state.unread_count = 0
    st.session_state.friend_requests = []
    st.session_state.friends = []
    st.session_state.live_gifts = []
    st.session_state.background_url = None
    st.session_state.editing_post = None
    st.session_state.love_story_url = None
    st.session_state.show_love_story = False
    st.rerun()

# ====== AUDIO FUNCTION ======
def generate_audio(text, voice):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            output_path = tmp.name
        comm = edge_tts.Communicate(text, voice)
        asyncio.run(comm.save(output_path))
        return output_path
    except Exception as e:
        st.error(f"Audio generation error: {e}")
        return None

def play_audio(audio_path):
    if audio_path and os.path.exists(audio_path):
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
            b64 = base64.b64encode(audio_bytes).decode()
            st.markdown(f'<audio controls src="data:audio/mp3;base64,{b64}" autoplay style="width:100%;"></audio>', unsafe_allow_html=True)
        os.unlink(audio_path)

# ====== LOGIN FUNCTION ======
def log_in_email(email, password, remember=False, show_debug=False):
    if supabase is None:
        st.error("❌ Authentication service is not configured. Please contact the administrator.")
        return
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if user.user:
            profile = get_or_create_profile(user.user.id, email, user.user.email)
            if profile and profile.get("is_banned"):
                st.error("🚫 Your account has been banned. Contact support if you believe this is an error.")
                return
            st.session_state.logged_in = True
            st.session_state.user = user.user
            if user.session:
                st.session_state.refresh_token = user.session.refresh_token
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.cache_data.clear()
            st.session_state.posts = load_posts()
            st.session_state.live_sessions = load_live_sessions()
            load_friend_data()
            st.session_state.notifications = load_notifications(user.user.id)
            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
            st.session_state.exchange_rate = fetch_exchange_rate()
            if remember and user.session:
                set_cookie("sb_refresh_token", user.session.refresh_token, 30)
                st.success("✅ Session saved – you’ll stay logged in for 30 days.")
            st.rerun()
    except Exception as e:
        error_str = str(e)
        if show_debug:
            st.error(f"❌ Full error:\n{error_str}")
        elif "Name or service not known" in error_str or "Failed to resolve" in error_str:
            st.error(t("network_error"))
            st.caption(t("debug_hint"))
        elif "Invalid login credentials" in error_str:
            st.error("❌ Invalid email or password.")
        elif "Email not confirmed" in error_str:
            st.error("❌ Please confirm your email address before logging in.")
        else:
            st.error(f"❌ Login failed: {error_str}")

def render_top_icons():
    if not st.session_state.logged_in:
        return
    user_id = st.session_state.user.id
    unread_msgs = 0
    try:
        resp = supabase.table("messages").select("id", count="exact").eq("receiver_id", user_id).eq("read", False).execute()
        unread_msgs = resp.count if hasattr(resp, 'count') else 0
    except Exception:
        pass
    unread_notifs = st.session_state.unread_count
    col1, col2 = st.columns([1, 1])
    with col1:
        label = f"💬 {unread_msgs}" if unread_msgs > 0 else "💬"
        if st.button(label, key="top_msg_icon", use_container_width=True):
            st.session_state.current_page = "friends_chat"
            st.rerun()
    with col2:
        label = f"🔔 {unread_notifs}" if unread_notifs > 0 else "🔔"
        if st.button(label, key="top_notif_icon", use_container_width=True):
            st.session_state.current_page = "friends_chat"
            st.rerun()
    st.divider()

# ====== LOGIN INTERFACE ======
def login_interface():
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <span class="dove-symbol">🕊️</span>
        <h2 style="color: #0a2a44; margin-top: -5px;">
            <span class="lakay-flag-text">Bienvenu sou Lakay se Lakay</span>
            <span class="rope-text">
                <span class="stars"><span>✦</span><span>✦</span><span>✦</span><span>✦</span><span>✦</span><span>✦</span></span>
            </span>
        </h2>
        <p style="color: #1e2a3a; opacity: 0.8;">Nou kontan wè w isit la. Se yon platfòm sosyal ki fèt pou tout Ayisyen yo – kote ou ka pataje lide ou, foto ou, videyo ou, e konekte ak zanmi ou yo nan yon espas ki sekirize e ki amizan. N ap viv ansanm, n ap grandi ansanm. Pataje kè ou, pataje lavi ou!</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    show_debug = st.checkbox(t("show_debug"), value=False)
    tab1, tab2, tab3 = st.tabs([t("login_title"), t("signup_title"), t("forgot_password")])
    with tab1:
        with st.form("login_email"):
            email = st.text_input(t("email"))
            password = st.text_input(t("password"), type="password")
            remember = st.checkbox(t("remember_me"))
            if st.form_submit_button(t("login_button"), use_container_width=True):
                if email and password:
                    log_in_email(email, password, remember, show_debug)
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

# ========== SOCIAL MEDIA RENDER FUNCTIONS ==========
def display_media_item(media):
    try:
        url = media["url"]
        if media["type"] == "image":
            st.image(url, use_column_width=True)
        elif media["type"] == "video":
            st.video(url, autoplay=False)
        else:
            st.markdown(f"[Media file]({url})")
    except Exception as e:
        st.error(f"Error displaying media: {e}")
        st.markdown(f"[Click to open media]({media['url']})")

# ====== GROQ SEARCH FUNCTION ======
def groq_search(query):
    """Use Groq API to recommend books/videos (not YouTube) based on the query."""
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("Groq API key not set. Add GROQ_API_KEY to your secrets.")
        return []

    # Detect YouTube links
    if "youtube.com" in query.lower() or "youtu.be" in query.lower():
        st.warning(t("youtube_not_supported"))
        return []

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    system_prompt = (
        "You are a helpful assistant that recommends books or videos (but not YouTube) based on a user's query. "
        "Return a JSON array of objects with 'title', 'description', and a 'url' field if available (you can suggest a link to a free source like Project Gutenberg, OpenLibrary, or a search link). "
        "If you cannot provide a link, set 'url' to null. The JSON should be the only thing in your response. "
        "Use the user's language (English, French, or Spanish) for the response."
    )
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            try:
                results = json.loads(content)
                if isinstance(results, list):
                    return results
                else:
                    st.error("Unexpected response format. Please try again.")
                    return []
            except json.JSONDecodeError:
                st.error("Failed to parse the response. Please rephrase your query.")
                return []
        else:
            if resp.status_code == 400 and "model_decommissioned" in resp.text:
                st.error("The selected Groq model is no longer available. Please contact the app administrator.")
            else:
                st.error(f"Groq API error: {resp.status_code} - {resp.text}")
            return []
    except Exception as e:
        st.error(f"Error connecting to Groq: {e}")
        return []

# ====== RENDER DISCOVER NEW PEOPLE SECTION ======
def render_discover_section():
    """Display the 'Discover New People' grid."""
    if supabase is None:
        st.info("Unable to load users – database not connected.")
        return
    try:
        current_user_id = st.session_state.user.id
        # Get all users except current
        all_users = get_all_users()
        if not all_users:
            st.info("No other users found.")
            return

        # Get current friends IDs
        friends_ids = {f["id"] for f in st.session_state.friends}
        # Get pending friend requests (both sent and received)
        req_resp = supabase.table("friend_requests").select("*").eq("status", "pending").execute()
        pending_requests = req_resp.data or []
        sent_dict = {}
        received_dict = {}
        for req in pending_requests:
            if req["sender_id"] == current_user_id:
                sent_dict[req["receiver_id"]] = req["id"]
            if req["receiver_id"] == current_user_id:
                received_dict[req["sender_id"]] = req["id"]

        # Build a list of users to display (not friends, not self)
        non_friends = []
        for u in all_users:
            uid = u["id"]
            if uid == current_user_id:
                continue
            if uid in friends_ids:
                continue
            # Determine status
            if uid in sent_dict:
                status = "sent"
                request_id = sent_dict[uid]
            elif uid in received_dict:
                status = "received"
                request_id = received_dict[uid]
            else:
                status = "none"
                request_id = None
            # Ensure default visibility
            u.setdefault("profile_visibility", "public")
            non_friends.append({**u, "status": status, "request_id": request_id})

        if not non_friends:
            st.info("🎉 You are already friends with everyone on the platform!")
            return

        # Display in a grid-like layout using columns
        cols = st.columns(3)
        for idx, user in enumerate(non_friends):
            with cols[idx % 3]:
                with st.container():
                    st.markdown('<div class="discover-card">', unsafe_allow_html=True)
                    # Avatar and name
                    col_av, col_name = st.columns([1, 3])
                    with col_av:
                        display_avatar_and_followers(user.get("avatar_url"), user["id"], size=70, profile=user)
                    with col_name:
                        # Make name clickable to view profile
                        if st.button(user['full_name'], key=f"discover_name_{user['id']}"):
                            st.session_state.viewing_profile = user['id']
                            st.rerun()
                        if user.get("is_banned"):
                            st.caption("🚫 Banned")
                        else:
                            st.caption("📌 " + user.get("location", ""))

                    # Action buttons
                    if user.get("is_banned"):
                        st.info("User banned")
                    elif user["status"] == "none":
                        if st.button("➕ Friend request", key=f"fr_send_{user['id']}"):
                            success, msg = send_friend_request(current_user_id, user["id"])
                            if success:
                                st.success("Friend request sent!")
                                load_friend_data()
                                st.rerun()
                            else:
                                st.error(msg)
                    elif user["status"] == "sent":
                        st.button("⏳ Friend request pending", key=f"fr_pending_{user['id']}", disabled=True)
                    elif user["status"] == "received":
                        col_acc, col_rej = st.columns(2)
                        with col_acc:
                            if st.button("✅ Accept", key=f"fr_accept_{user['id']}"):
                                success, msg = respond_friend_request(user["request_id"], True)
                                if success:
                                    load_friend_data()
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with col_rej:
                            if st.button("❌ Reject", key=f"fr_reject_{user['id']}"):
                                success, msg = respond_friend_request(user["request_id"], False)
                                if success:
                                    load_friend_data()
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        st.button("👥 Friends", key=f"fr_friend_{user['id']}", disabled=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        # Refresh button
        if st.button("🔄 Refresh friends list"):
            load_friend_data()
            st.rerun()
    except Exception as e:
        st.error(f"Could not load users: {e}")

# ====== FEED ======
def render_feed():
    # ====== LOVE STORY – OPEN IN NEW TAB ======
    if st.session_state.get("show_love_story", False) and st.session_state.get("love_story_url"):
        st.title("💕 Love Story")
        st.info(
            "This content is hosted on an external site. "
            "Click the button below to watch in a new tab."
        )
        try:
            st.link_button("▶ Watch Now", st.session_state.love_story_url)
        except AttributeError:
            st.markdown(
                f'<a href="{st.session_state.love_story_url}" target="_blank" '
                f'style="display:inline-block; background:#0080ff; color:white; '
                f'padding:10px 20px; border-radius:5px; text-decoration:none; '
                f'font-weight:bold;">▶ Watch Now</a>',
                unsafe_allow_html=True
            )
        if st.button("✖ Close and return to Feed"):
            st.session_state.show_love_story = False
            st.session_state.love_story_url = None
            st.rerun()
        return
    # -------------------------------------------------

    if st.session_state.viewing_profile:
        render_user_profile(st.session_state.viewing_profile)
        return

    st.header(t("feed"))
    if st.session_state.last_error:
        st.markdown(f"<div class='error-box'><b>❌ Error:</b>\n{st.session_state.last_error}</div>", unsafe_allow_html=True)
        if st.button(t("clear_error")):
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

    # ---- Create a post ----
    st.markdown(f"### {t('create_post')}")
    st.info(t("paste_video_link_hint"))  # <-- NEW HINT
    with st.form("new_post", clear_on_submit=True):
        col_avatar, col_input = st.columns([1, 8])
        with col_avatar:
            display_avatar_and_followers(st.session_state.profile.get("avatar_url"), st.session_state.user.id, size=50, profile=st.session_state.profile)
        with col_input:
            content = st.text_area(t("caption_placeholder"), height=150, placeholder=t("caption_placeholder"), label_visibility="collapsed")
        media_files = st.file_uploader(t("add_media"), type=["png","jpg","jpeg","gif","mp4","mov","avi"], accept_multiple_files=True)
        st.caption("⚠️ File size limit: 200MB (Streamlit Cloud). For videos larger than 200MB, use a link (YouTube, etc.).")
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            visibility = st.radio(t("visibility"), [t("public"), t("private")], horizontal=True, index=0)
            is_public = (visibility == t("public"))
        with col3:
            if st.form_submit_button(t("post"), use_container_width=True):
                if not content and not media_files:
                    st.warning("Please add a caption or media.")
                else:
                    if create_post(st.session_state.user.id, content, media_files, is_public):
                        st.rerun()

    st.divider()

    # ====== GROQ SEARCH ======
    st.markdown(f"### {t('search_groq')}")
    groq_key = st.secrets.get("GROQ_API_KEY")
    if not groq_key:
        st.warning(t("groq_api_key_missing"))
    else:
        col_search, col_btn = st.columns([4, 1])
        with col_search:
            search_query = st.text_input("", placeholder=t("groq_search_placeholder"),
                                         key="groq_search_input", label_visibility="collapsed")
        with col_btn:
            if st.button("🔍", key="groq_search_btn", use_container_width=True):
                if search_query:
                    if "youtube.com" in search_query.lower() or "youtu.be" in search_query.lower():
                        st.warning(t("youtube_not_supported"))
                    else:
                        with st.spinner("Searching with Groq..."):
                            results = groq_search(search_query)
                            st.session_state.groq_search_results = results
                            st.session_state.groq_selected_item = None
                            st.session_state.groq_search_query = search_query
                            st.rerun()
                else:
                    st.warning("Please enter a search term.")

        if st.session_state.groq_search_results:
            st.markdown(f"#### {t('groq_results')} for '{st.session_state.groq_search_query}'")
            cols = st.columns(3)
            for idx, item in enumerate(st.session_state.groq_search_results):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"**{item.get('title', 'Untitled')}**")
                        st.caption(item.get('description', '')[:120] + "...")
                        url = item.get('url')
                        if url:
                            if st.button(t("groq_open"), key=f"groq_open_{idx}"):
                                st.session_state.groq_selected_item = url
                                st.rerun()
                        else:
                            st.button("📚 No link", disabled=True, key=f"groq_nolink_{idx}")
            if st.session_state.groq_selected_item:
                st.divider()
                st.markdown(f"### 🔗 Open Resource")
                st.markdown(f"[{st.session_state.groq_selected_item}]({st.session_state.groq_selected_item})")
                st.markdown(f'<a href="{st.session_state.groq_selected_item}" target="_blank">Open in new tab</a>', unsafe_allow_html=True)
                if st.button(t("groq_close")):
                    st.session_state.groq_selected_item = None
                    st.rerun()
        elif st.session_state.groq_search_query and not st.session_state.groq_search_results:
            st.info(t("no_groq_results"))

    # ---- Live Now ----
    active_lives = st.session_state.live_sessions
    if active_lives:
        st.markdown("### 🔴 Live Now")
        for live in active_lives:
            with st.container():
                col_a, col_b = st.columns([1,4])
                with col_a:
                    display_avatar_and_followers(live["profiles"]["avatar_url"], live["user_id"], size=40, profile=live["profiles"])
                with col_b:
                    st.markdown(f"**{live['profiles']['full_name']}** is live: **{live['title']}**")
                    if st.button(t("join_live"), key=f"join_{live['id']}"):
                        st.session_state.viewing_live = live["id"]
                        st.rerun()
                st.divider()

    # ====== DISCOVER NEW PEOPLE – placed prominently ======
    st.markdown("---")
    st.subheader("👥 Discover New People")
    load_friend_data()
    render_discover_section()
    st.divider()

    # ---- Feed posts ----
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

    if not st.session_state.posts:
        st.info("No posts yet. Be the first to create one!")
    else:
        for post in st.session_state.posts:
            with st.container():
                col_a, col_b, col_c, col_d, col_e = st.columns([1,4,2,1,1])
                with col_a:
                    display_avatar_and_followers(post["profiles"].get("avatar_url"), post["user_id"], size=40, profile=post["profiles"])
                with col_b:
                    name = post['profiles']['full_name']
                    if post['user_id'] != st.session_state.user.id:
                        if st.button(name, key=f"view_profile_{post['id']}"):
                            st.session_state.viewing_profile = post['user_id']
                            st.rerun()
                    else:
                        st.markdown(f"**{name}**")
                    if post.get("profiles", {}).get("is_live"):
                        st.markdown(f"<span class='green-dot'></span>", unsafe_allow_html=True)
                    if not post.get("is_public", True):
                        st.markdown("<span class='private-badge'>Private</span>", unsafe_allow_html=True)
                    # Check if it's a live post (by content, not by column)
                    if post['content'].startswith("🔴 I'm live:"):
                        # Check if live session is still active
                        live_session = None
                        if supabase:
                            try:
                                live_resp = supabase.table("live_sessions").select("*").eq("user_id", post["user_id"]).eq("is_live", True).execute()
                                if live_resp.data:
                                    live_session = live_resp.data[0]
                            except:
                                pass
                        if live_session:
                            st.markdown(f"<span class='live-badge'>🔴 LIVE NOW</span>", unsafe_allow_html=True)
                            if st.button("🎥 Join Live", key=f"join_live_post_{post['id']}"):
                                st.session_state.viewing_live = live_session["id"]
                                st.rerun()
                with col_c:
                    st.caption(post['created_at'][:16])
                with col_d:
                    if st.session_state.user and post['user_id'] == st.session_state.user.id:
                        if st.button("✏️", key=f"edit_{post['id']}"):
                            st.session_state.editing_post = post['id']
                            st.rerun()
                with col_e:
                    if st.session_state.user and post['user_id'] == st.session_state.user.id:
                        if st.button("🗑️", key=f"del_post_{post['id']}"):
                            st.session_state.delete_confirm = (post['id'], post['content'][:30])
                            st.rerun()

                # EDIT FORM (shown only when editing this post)
                if st.session_state.editing_post == post['id']:
                    with st.form(key=f"edit_form_{post['id']}"):
                        new_content = st.text_area("Edit caption", value=post.get('content', ''), height=100)
                        new_media = st.file_uploader("Add additional media", type=["png","jpg","jpeg","gif","mp4","mov","avi"], accept_multiple_files=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save"):
                                existing = post.get('media_urls', [])
                                if update_post(post['id'], st.session_state.user.id, new_content, new_media, existing):
                                    st.session_state.editing_post = None
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancel"):
                                st.session_state.editing_post = None
                                st.rerun()
                    st.divider()

                # Normal post: display media files first
                media_urls = post.get("media_urls", [])
                if media_urls:
                    for media in media_urls:
                        display_media_item(media)

                # Then display post content and embed any video links (YouTube etc.)
                if post['content']:
                    clickable_content = make_clickable(post['content'])
                    st.markdown(f"<div class='post-card'>{clickable_content}</div>", unsafe_allow_html=True)
                    # Find URLs in content and embed them
                    urls = re.findall(r'(https?://[^\s]+)', post['content'])
                    for url in urls:
                        # Try to embed (YouTube, Vimeo, etc.)
                        try:
                            embed_video_from_url(url)
                        except Exception as e:
                            # If embedding fails, just show the link as plain text
                            st.markdown(f"[Link]({url})")

                emojis = ["👍","👎","❤️","😂","😮","😢","👏"]
                reaction_counts = post.get("reactions", {})
                summary = " ".join([f"{emoji} {count}" for emoji, count in list(reaction_counts.items())[:3]])
                col_react, col_comments, col_shares = st.columns([2,1,1])
                with col_react:
                    if st.button("👍 React", key=f"react_btn_{post['id']}"):
                        st.session_state[f"show_reactions_{post['id']}"] = not st.session_state.get(f"show_reactions_{post['id']}", False)
                        st.rerun()
                    if st.session_state.get(f"show_reactions_{post['id']}", False):
                        st.markdown("**Choose reaction**")
                        for i in range(0, len(emojis), 3):
                            cols = st.columns(3)
                            for j, emoji in enumerate(emojis[i:i+3]):
                                with cols[j]:
                                    if st.button(emoji, key=f"react_{post['id']}_{emoji}"):
                                        toggle_reaction(post['id'], st.session_state.user.id, emoji)
                                        st.session_state[f"show_reactions_{post['id']}"] = False
                                        st.rerun()
                    if summary:
                        st.markdown(f"<small>{summary}</small>", unsafe_allow_html=True)
                with col_comments:
                    st.markdown(f"💬 {post.get('comment_count',0)}")
                with col_shares:
                    if st.button(f"🔄 {post['shares_count']}", key=f"share_{post['id']}"):
                        share_post(post['id'], st.session_state.user.id, is_public=True)
                        st.rerun()

                st.markdown("<div class='comment-section'>", unsafe_allow_html=True)
                st.markdown(f"#### {t('comments')}")
                with st.form(key=f"new_comment_{post['id']}", clear_on_submit=True):
                    msg = st.text_input(t("write_comment"), label_visibility="collapsed", placeholder=t("write_comment"))
                    if st.form_submit_button(t("post")):
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
                    col_avatar_comment, col1, col2, col3, col4 = st.columns([1,4,1,1,1])
                    with col_avatar_comment:
                        display_avatar_and_followers(c['profiles'].get('avatar_url'), c['user_id'], size=30, profile=c['profiles'])
                    with col1:
                        clickable_comment = make_clickable(c['content'])
                        st.markdown(f"**{c['profiles']['full_name']}**: {clickable_comment}")
                        st.markdown(f"<span class='comment-meta'>{c['created_at'][:16]}</span>", unsafe_allow_html=True)
                    with col2:
                        if st.button(f"👍 {c.get('likes',0)}", key=f"like_{c['id']}"):
                            like_comment(c['id'], increment=True)
                            st.rerun()
                    with col3:
                        if st.button(t("reply"), key=f"reply_{c['id']}"):
                            st.session_state.replying_to[c['id']] = not st.session_state.replying_to.get(c['id'], False)
                            st.rerun()
                    with col4:
                        if st.session_state.user and c['user_id'] == st.session_state.user.id:
                            if st.button("🗑️", key=f"del_comment_{c['id']}"):
                                delete_comment(c['id'])
                                st.rerun()

                    if st.session_state.replying_to.get(c['id'], False):
                        with st.form(key=f"reply_form_{c['id']}"):
                            reply = st.text_input(t("your_reply"), label_visibility="collapsed", placeholder=t("your_reply"))
                            if st.form_submit_button(t("post_reply")):
                                if reply:
                                    add_comment(post['id'], st.session_state.user.id, reply, parent_id=c['id'])
                                    st.session_state.replying_to[c['id']] = False
                                    st.rerun()

                    for r in replies.get(c['id'], []):
                        st.markdown("<div class='comment-indent'>", unsafe_allow_html=True)
                        colr_avatar, colr1, colr2, colr3, colr4 = st.columns([1,4,1,1,1])
                        with colr_avatar:
                            display_avatar_and_followers(r['profiles'].get('avatar_url'), r['user_id'], size=30, profile=r['profiles'])
                        with colr1:
                            clickable_reply = make_clickable(r['content'])
                            st.markdown(f"**{r['profiles']['full_name']}**: {clickable_reply}")
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

# ====== render_user_profile ======
def render_user_profile(user_id, show_back_button=True):
    if supabase is None:
        st.error("Database not connected.")
        if st.button(t("back_to_feed")):
            st.session_state.viewing_profile = None
            st.rerun()
        return
    render_top_icons()
    try:
        profile_resp = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if not profile_resp.data:
            st.error("User not found.")
            if st.button(t("back_to_feed")):
                st.session_state.viewing_profile = None
                st.rerun()
            return
        profile = profile_resp.data[0]
    except Exception as e:
        error_str = str(e)
        if "JWT expired" in error_str:
            if refresh_supabase_session():
                try:
                    profile_resp = supabase.table("profiles").select("*").eq("id", user_id).execute()
                    if profile_resp.data:
                        profile = profile_resp.data[0]
                    else:
                        st.error("User not found.")
                        if st.button(t("back_to_feed")):
                            st.session_state.viewing_profile = None
                            st.rerun()
                        return
                except Exception as retry_e:
                    st.error(f"Error loading profile after refresh: {retry_e}")
                    if st.button(t("back_to_feed")):
                        st.session_state.viewing_profile = None
                        st.rerun()
                    return
            else:
                st.error("Session expired. Please log in again.")
                logout()
                st.rerun()
                return
        else:
            st.error(f"Error loading profile: {error_str}")
            if st.button(t("back_to_feed")):
                st.session_state.viewing_profile = None
                st.rerun()
            return
    st.header(f"👤 {profile['full_name']}'s Profile")
    col1, col2 = st.columns([1,2])
    with col1:
        display_avatar_and_followers(profile.get("avatar_url"), user_id, size=150, profile=profile)
        st.markdown(f"**{t('bio')}:** {profile.get('bio', 'No bio')}")
        st.markdown(f"**{t('location')}:** {profile.get('location', 'Unknown')}")
        st.markdown(f"**{t('moncash_phone')}:** {profile.get('moncash_phone', 'Not set')}")
        st.markdown(f"**{t('natcash_phone')}:** {profile.get('natcash_phone', 'Not set')}")
        st.markdown(f"**{t('member_since')}:** {profile.get('join_date', '')[:10]}")
        st.markdown(f"**{t('profile_visibility')}:** {profile.get('profile_visibility', 'public').capitalize()}")

        # --- Interaction Buttons ---
        is_own_profile = (user_id == st.session_state.user.id)
        if not is_own_profile:
            # Call button
            if st.button(t("call_now"), key=f"call_{user_id}"):
                initiate_call(user_id)
                st.rerun()
            # Chat button
            if st.button(t("chat"), key=f"chat_{user_id}"):
                st.session_state.selected_chat = user_id
                st.session_state.viewing_profile = None
                st.rerun()
            # Email button (if email exists)
            if profile.get("email"):
                st.markdown(f'<a href="mailto:{profile["email"]}" target="_blank" style="display:inline-block; margin-top:5px; background:#0080ff; color:white; padding:6px 12px; border-radius:20px; text-decoration:none; font-weight:bold;">📧 {t("email_user")}</a>', unsafe_allow_html=True)
            # WhatsApp button (if whatsapp_phone exists)
            if profile.get("whatsapp_phone"):
                wa_number = profile["whatsapp_phone"].replace("+", "").strip()
                st.markdown(f'<a href="https://wa.me/{wa_number}" target="_blank" style="display:inline-block; margin-top:5px; background:#25D366; color:white; padding:6px 12px; border-radius:20px; text-decoration:none; font-weight:bold;">💬 {t("whatsapp")}</a>', unsafe_allow_html=True)
        if show_back_button:
            if st.button(t("back_to_feed")):
                st.session_state.viewing_profile = None
                st.rerun()

    with col2:
        # Check visibility and friendship
        is_friend = any(f['id'] == user_id for f in st.session_state.friends)
        can_view_content = is_own_profile or is_friend or profile.get('profile_visibility', 'public') == 'public'

        tab1, tab2 = st.tabs(["📝 Posts", "📸 Albums"])
        with tab1:
            st.subheader(t("feed"))
            if can_view_content:
                posts = load_user_posts(user_id, include_private=is_own_profile)
                post_count = len(posts)
                if not posts:
                    st.info("No posts to show." if not is_own_profile else "You haven't posted anything yet.")
                else:
                    for post in posts:
                        with st.container():
                            st.markdown(f"**{post['profiles']['full_name']}**")
                            st.caption(post['created_at'][:16])
                            if post['content']:
                                clickable_content = make_clickable(post['content'])
                                st.markdown(f"<div class='post-card'>{clickable_content}</div>", unsafe_allow_html=True)
                            for media in post.get("media_urls", []):
                                display_media_item(media)
                            st.divider()
                st.metric(t("posts_count"), post_count)
            else:
                st.info(t("private_profile"))
        with tab2:
            st.subheader(t("albums"))
            if can_view_content:
                albums = get_user_albums(user_id, include_private=is_own_profile)
                if not albums:
                    st.info(t("no_albums"))
                else:
                    cols = st.columns(3)
                    for idx, album in enumerate(albums):
                        with cols[idx % 3]:
                            with st.container():
                                st.markdown(f'<div class="album-card">', unsafe_allow_html=True)
                                if album.get("cover_photo"):
                                    st.image(album["cover_photo"], width=200)
                                else:
                                    st.image("https://via.placeholder.com/200x150?text=No+Photo", width=200)
                                st.markdown(f"<div class='album-title'>{album['title']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='album-meta'>{album['description'][:50]}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='album-meta'>Visibility: {'Public' if album['visibility']=='public' else 'Private'}</div>", unsafe_allow_html=True)
                                if st.button(t("view_album"), key=f"view_album_{album['id']}"):
                                    st.session_state.viewing_album = album['id']
                                    st.rerun()
                                if is_own_profile:
                                    if st.button(t("delete_album"), key=f"del_album_{album['id']}"):
                                        if delete_album(album['id']):
                                            st.success(t("album_deleted"))
                                            st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info(t("private_profile"))

    # If viewing an album
    if st.session_state.viewing_album:
        album_id = st.session_state.viewing_album
        album_data = supabase.table("photo_albums").select("*").eq("id", album_id).execute().data
        if album_data:
            album = album_data[0]
            photos = get_album_photos(album_id)
            st.subheader(f"📸 {album['title']}")
            st.caption(album['description'])
            st.caption(f"Visibility: {album['visibility']}")
            if photos:
                st.markdown('<div class="photo-grid">', unsafe_allow_html=True)
                for photo in photos:
                    st.image(photo["photo_url"], use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No photos in this album.")
            if st.button("← Back to Profile"):
                st.session_state.viewing_album = None
                st.rerun()
        else:
            st.error("Album not found.")
            st.session_state.viewing_album = None
    st.divider()
    cola, colb = st.columns(2)
    with cola:
        st.metric(t("posts_count"), post_count if 'post_count' in locals() else 0)
    with colb:
        st.metric("Followers", "1KFollowers")
    st.divider()

    # --- Handle call ringing state ---
    if st.session_state.call_ringing and st.session_state.call_target_user == user_id:
        st.info(t("ringing"))
        # Auto-check after 30 seconds (handled by check_call_status)
        check_call_status()

# ====== render_friends_page ======
def render_friends_page():
    try:
        if st.session_state.viewing_profile:
            render_user_profile(st.session_state.viewing_profile, show_back_button=False)
            if st.button("← Back to Friends"):
                st.session_state.viewing_profile = None
                st.rerun()
            return

        st.header(t("friends_chat"))
        with st.expander(t("setup_instructions")):
            st.markdown("**If you get 'new row violates row-level security policy' for notifications:**")
            st.markdown("1. Go to your Supabase Dashboard → SQL Editor.")
            st.markdown("2. Run the following SQL:")
            st.code("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;\nCREATE POLICY \"Allow authenticated inserts\" ON notifications FOR INSERT TO authenticated WITH CHECK (true);", language="sql")
            st.markdown("3. Then refresh the app.")
            st.markdown("---")
            st.markdown("**If you get 'new row violates row-level security policy' when uploading files:**")
            st.markdown("1. Go to your Supabase Dashboard → Storage.")
            st.markdown("2. For each bucket (`avatars`, `post_media`, `chat_media`), click on the bucket → 'Policies'.")
            st.markdown("3. Add a new policy:")
            st.markdown("   - Policy name: `Allow authenticated uploads`")
            st.markdown("   - Allowed operations: `INSERT`")
            st.markdown("   - Target roles: `authenticated`")
            st.markdown("   - USING expression: `(auth.role() = 'authenticated')`")
            st.markdown("4. Also add a policy for SELECT (reading) if needed:")
            st.markdown("   - Policy name: `Allow public read`")
            st.markdown("   - Allowed operations: `SELECT`")
            st.markdown("   - USING expression: `true`")

        st.markdown(f"<div class='friend-count'>{t('your_friends')}: {len(st.session_state.friends)}</div>", unsafe_allow_html=True)
        st.divider()

        with st.expander(f"🔔 {t('friend_requests')} ({st.session_state.unread_count})", expanded=True):
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

        st.subheader(t("friend_requests"))
        if not st.session_state.friend_requests:
            st.info("No pending friend requests")
        else:
            for req in st.session_state.friend_requests:
                cols = st.columns([2,1,1])
                with cols[0]:
                    display_avatar_and_followers(req['sender'].get('avatar_url'), req['sender']['id'], size=60, profile=req['sender'])
                    st.markdown(f"**{req['sender']['full_name']}**")
                with cols[1]:
                    if st.button(t("accept"), key=f"accept_{req['id']}"):
                        success, msg = respond_friend_request(req['id'], True)
                        if success:
                            load_friend_data()
                            st.session_state.notifications = load_notifications(st.session_state.user.id)
                            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
                            st.rerun()
                        else:
                            st.error(msg)
                with cols[2]:
                    if st.button(t("reject"), key=f"reject_{req['id']}"):
                        success, msg = respond_friend_request(req['id'], False)
                        if success:
                            load_friend_data()
                            st.rerun()
                        else:
                            st.error(msg)
                st.divider()

        st.subheader(t("find_users"))
        search_query = st.text_input(t("search_by_name"))
        if search_query:
            results = search_users(search_query)
            if not results:
                st.info("No users found")
            else:
                for user in results:
                    cols = st.columns([3,1,1])
                    with cols[0]:
                        display_avatar_and_followers(user.get('avatar_url'), user['id'], size=60, profile=user)
                        st.markdown(f"**{user['full_name']}**")
                    with cols[1]:
                        if st.button(t("add_friend"), key=f"add_{user['id']}"):
                            success, msg = send_friend_request(st.session_state.user.id, user['id'])
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
                    with cols[2]:
                        if st.button(t("view_profile"), key=f"view_{user['id']}"):
                            st.session_state.viewing_profile = user['id']
                            st.rerun()
                    st.divider()

        st.divider()
        st.subheader(t("your_friends"))
        if not st.session_state.friends:
            st.info(t("no_friends"))
        else:
            for friend in st.session_state.friends:
                cols = st.columns([1,4,1,1,1,1])
                with cols[0]:
                    display_avatar_and_followers(friend.get('avatar_url'), friend['id'], size=60, profile=friend)
                with cols[1]:
                    # Make name clickable to view profile
                    if st.button(friend['full_name'], key=f"friend_name_{friend['id']}"):
                        st.session_state.viewing_profile = friend['id']
                        st.rerun()
                with cols[2]:
                    if st.button(t("chat"), key=f"chat_{friend['id']}"):
                        st.session_state.selected_chat = friend['id']
                        st.rerun()
                with cols[3]:
                    if st.button(t("call"), key=f"call_{friend['id']}"):
                        initiate_call(friend['id'])
                        st.rerun()
                with cols[4]:
                    if st.button("📧", key=f"email_{friend['id']}"):
                        if friend.get('email'):
                            st.markdown(f'<a href="mailto:{friend["email"]}" target="_blank">Email</a>', unsafe_allow_html=True)
                        else:
                            st.warning("No email provided.")
                with cols[5]:
                    if st.button("💬", key=f"whatsapp_{friend['id']}"):
                        if friend.get('whatsapp_phone'):
                            wa = friend["whatsapp_phone"].replace("+", "").strip()
                            st.markdown(f'<a href="https://wa.me/{wa}" target="_blank">WhatsApp</a>', unsafe_allow_html=True)
                        else:
                            st.warning("No WhatsApp number.")
                st.divider()

        # Private chat
        if st.session_state.selected_chat:
            st.markdown("---")
            st.subheader("💬 Private Chat")
            other_id = st.session_state.selected_chat
            try:
                other_resp = supabase.table("profiles").select("full_name, avatar_url, moncash_phone, natcash_phone, last_active, email, whatsapp_phone").eq("id", other_id).execute()
                other_data = other_resp.data[0] if other_resp.data else None
            except Exception as e:
                st.warning(f"Could not load other user's profile: {e}")
                other_data = None

            if other_data:
                other_name = other_data.get("full_name", "User")
                other_avatar = other_data.get("avatar_url")
                other_profile = {"last_active": other_data.get("last_active")}
            else:
                other_name = "User"
                other_avatar = None
                other_profile = {}

            col1, col2 = st.columns([1,5])
            with col1:
                display_avatar_and_followers(other_avatar, other_id, size=60, profile=other_profile)
            with col2:
                st.markdown(f"**Chat with {other_name}**")
                if st.button("✖ Close Chat", key="close_chat_btn"):
                    st.session_state.selected_chat = None
                    st.rerun()

            st.divider()
            messages = load_messages(st.session_state.user.id, other_id)
            if not messages:
                st.info("No messages yet. Start the conversation!")
            else:
                for msg in messages:
                    if msg["sender_id"] == st.session_state.user.id:
                        if msg.get("media_url"):
                            try:
                                if msg.get("media_type") == "image":
                                    st.image(msg["media_url"], width=300)
                                elif msg.get("media_type") == "video":
                                    st.video(msg["media_url"], autoplay=False)
                                else:
                                    st.markdown(f"[Media file]({msg['media_url']})")
                            except Exception:
                                st.markdown(f"[Click to open media]({msg['media_url']})")
                            col1, col2, col3 = st.columns([6,1,1])
                            with col2:
                                if st.button("📤 Share to Feed", key=f"share_own_{msg['id']}"):
                                    with st.popover("Create post"):
                                        with st.form(f"share_own_form_{msg['id']}"):
                                            caption = st.text_area("Add a caption (optional)")
                                            if st.form_submit_button(t("post")):
                                                media_info = [{"url": msg["media_url"], "type": msg["media_type"]}]
                                                create_post(st.session_state.user.id, caption or "", existing_media_urls=media_info, is_public=True)
                                                st.rerun()
                            with col3:
                                if st.button("🔗 Copy Link", key=f"copy_{msg['id']}"):
                                    st.markdown(f"""
                                    <script>
                                    navigator.clipboard.writeText('{msg["media_url"]}').then(() => {{
                                        alert('Link copied!');
                                    }}).catch(() => {{
                                        var input = document.createElement('input');
                                        input.value = '{msg["media_url"]}';
                                        document.body.appendChild(input);
                                        input.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(input);
                                        alert('Link copied!');
                                    }});
                                    </script>
                                    """, unsafe_allow_html=True)
                        if msg.get("content"):
                            clickable_content = make_clickable(msg["content"])
                            st.markdown(f"<div style='text-align:right; background:#e0f7fa; padding:5px; border-radius:10px; margin:5px;'><b>You:</b> {clickable_content}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)
                    else:
                        if msg.get("media_url"):
                            try:
                                if msg.get("media_type") == "image":
                                    st.image(msg["media_url"], width=300)
                                elif msg.get("media_type") == "video":
                                    st.video(msg["media_url"], autoplay=False)
                                else:
                                    st.markdown(f"[Media file]({msg['media_url']})")
                            except Exception:
                                st.markdown(f"[Click to open media]({msg['media_url']})")
                            col1, col2, col3 = st.columns([6,1,1])
                            with col2:
                                if st.button("📤 Share to Feed", key=f"share_{msg['id']}"):
                                    with st.popover("Create post"):
                                        with st.form(f"share_form_{msg['id']}"):
                                            caption = st.text_area("Add a caption (optional)")
                                            if st.form_submit_button(t("post")):
                                                media_info = [{"url": msg["media_url"], "type": msg["media_type"]}]
                                                create_post(st.session_state.user.id, caption or "", existing_media_urls=media_info, is_public=True)
                                                st.rerun()
                            with col3:
                                if st.button("🔗 Copy Link", key=f"copy_{msg['id']}"):
                                    st.markdown(f"""
                                    <script>
                                    navigator.clipboard.writeText('{msg["media_url"]}').then(() => {{
                                        alert('Link copied!');
                                    }}).catch(() => {{
                                        var input = document.createElement('input');
                                        input.value = '{msg["media_url"]}';
                                        document.body.appendChild(input);
                                        input.select();
                                        document.execCommand('copy');
                                        document.body.removeChild(input);
                                        alert('Link copied!');
                                    }});
                                    </script>
                                    """, unsafe_allow_html=True)
                        if msg.get("content"):
                            clickable_content = make_clickable(msg["content"])
                            st.markdown(f"<div style='text-align:left; background:#f1f8e9; padding:5px; border-radius:10px; margin:5px;'><b>{other_name}:</b> {clickable_content}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)

            with st.form("send_message", clear_on_submit=True):
                msg_content = st.text_input(t("send_message"), placeholder="Type your message...")
                uploaded_file = st.file_uploader(t("add_media"), type=["png","jpg","jpeg","gif","mp4","mov","avi"])
                st.caption("⚠️ File size limit: 200MB (configurable). For larger videos, use external links.")
                col1, col2 = st.columns([1,5])
                with col1:
                    sent = st.form_submit_button(t("send"))
                if sent:
                    if msg_content or uploaded_file:
                        send_message(st.session_state.user.id, other_id, msg_content or "", media_file=uploaded_file)
                        st.rerun()

            st.divider()
        else:
            st.info("Select a friend and click 'Chat' to start a private conversation.")

        # Video call
        if st.session_state.in_call and st.session_state.call_room:
            st.subheader(t("active_call"))
            st.markdown(f"{t('room_id')}: `{st.session_state.call_room}`")
            st.markdown(t("share_room"))
            st.info(t("call_permission_hint"))
            st.markdown("#### 🎨 Virtual Background")
            uploaded_bg = st.file_uploader("Upload an image (PNG, JPG, JPEG, GIF)", type=["png","jpg","jpeg","gif"], key="call_bg_uploader")
            if uploaded_bg:
                bytes_data = uploaded_bg.getvalue()
                b64 = base64.b64encode(bytes_data).decode()
                mime = uploaded_bg.type
                data_url = f"data:{mime};base64,{b64}"
                st.session_state.call_background_url = data_url
                st.success("Background uploaded! Refreshing call...")
                st.rerun()
            if st.session_state.get("call_background_url"):
                st.image(st.session_state.call_background_url, width=200, caption="Current background")
                if st.button("🗑️ Clear Background"):
                    st.session_state.call_background_url = None
                    st.rerun()
            if st.button(t("reload_call")):
                st.session_state.call_reload += 1
                st.rerun()
            domain = JITSI_DOMAIN
            room = st.session_state.call_room
            container_id = f"jitsi-container-{st.session_state.call_reload}"
            config_overwrite = {"startWithAudioMuted": False, "startWithVideoMuted": False, "disableWelcomePage": True, "disableDeepLinking": True, "p2p": {"enabled": False}}
            config_json = json.dumps(config_overwrite)
            jitsi_html = f"""
            <div id="{container_id}" style="height: 500px; width: 100%;"></div>
            <script src="https://{domain}/external_api.js"></script>
            <script>
              (function() {{
                const domain = '{domain}';
                const room = '{room}';
                const config = {config_json};
                const container = document.getElementById('{container_id}');
                if (!container) return;
                if (typeof JitsiMeetExternalAPI !== 'undefined') {{
                    const api = new JitsiMeetExternalAPI(domain, {{
                        roomName: room,
                        parentNode: container,
                        configOverwrite: config
                    }});
                }} else {{
                    setTimeout(function() {{
                        if (typeof JitsiMeetExternalAPI !== 'undefined') {{
                            const api = new JitsiMeetExternalAPI(domain, {{
                                roomName: room,
                                parentNode: container,
                                configOverwrite: config
                            }});
                        }}
                    }}, 1000);
                }}
              }})();
            </script>
            """
            st.components.v1.html(jitsi_html, height=520)
            fallback_url = f"https://{domain}/{room}"
            st.markdown(f"**Or open in a new tab:** [Join Room]({fallback_url})", unsafe_allow_html=True)
            if st.button(t("end_call")):
                st.session_state.call_background_url = None
                end_call()
                st.rerun()
        else:
            if st.button(t("start_call")):
                start_call()
                st.rerun()

    except Exception as e:
        st.error(f"An error occurred while loading the Friends & Chat page:\n\n{e}")
        st.exception(e)
        if st.button("Go back to Feed"):
            st.session_state.current_page = "feed"
            st.rerun()

def render_map():
    st.header(t("satellite_map"))
    sats = {
        "Starlink-1": {"lat": 32.77, "lon": -96.79, "status": "Active"},
        "Starlink-2": {"lat": 35.68, "lon": 139.69, "status": "Active"},
        "Starlink-3": {"lat": 51.50, "lon": -0.12, "status": "Active"},
        "Starlink-4": {"lat": 18.53, "lon": -72.33, "status": "Priority"}
    }
    df = pd.DataFrame([{"Satellite": name, "Latitude": data["lat"], "Longitude": data["lon"], "Status": data["status"]} for name, data in sats.items()])
    st.dataframe(df, use_container_width=True)
    st.divider()
    cols = st.columns(4)
    for i, (name, data) in enumerate(sats.items()):
        with cols[i % 4]:
            st.metric(name, data["status"], f"{data['lat']:.1f}°, {data['lon']:.1f}°")

# ====== WORLDCUP – with full‑screen iframes ======
def render_worldcup():
    st.title("⚽ " + t("worldcup"))
    stream1_url = "https://futbol-libres.su/eventos.html?r=aHR0cHM6Ly9sYXRhbXZpZHpzLm9yZy9jYW5hbC5waHA/c3RyZWFtPXRlbGVtdW5kb3VzYQ=="
    stream2_url = "https://futbol-libres.su/eventos.html?r=aHR0cHM6Ly9sYXRhbXZpZHpzLm9yZy9jYW5hbC5waHA/c3RyZWFtPWRzcG9ydHM="
    st.markdown("""
    <div style="background: rgba(255,255,255,0.1); border: 1px solid #2a1f14; border-radius: 12px; padding: 15px; margin-bottom: 20px;">
        <p style="color: #ffffff; font-size: 1.1rem;">🏆 Watch every match of the <strong>FIFA World Cup 2026</strong> live – completely free!<br>
        Choose your stream below and enjoy the game.</p>
    </div>
    """, unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📺 Stream #1 (Main)", "⚽ Live WorldCup 2026 #2"])
    with tab1:
        st.components.v1.html(f'''
        <iframe src="{stream1_url}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>
        ''', height=620)
        st.markdown(f'<a href="{stream1_url}" target="_blank" style="display:inline-block; margin-top:10px; background:#0080ff; color:white; padding:8px 16px; border-radius:8px; text-decoration:none; font-weight:bold;">{t("open_in_new_tab")} ↗</a>', unsafe_allow_html=True)
        st.caption("📺 Live soccer stream – watch the 2026 World Cup matches for free.")
    with tab2:
        st.components.v1.html(f'''
        <iframe src="{stream2_url}" width="100%" height="600" frameborder="0" allowfullscreen></iframe>
        ''', height=620)
        st.markdown(f'<a href="{stream2_url}" target="_blank" style="display:inline-block; margin-top:10px; background:#0080ff; color:white; padding:8px 16px; border-radius:8px; text-decoration:none; font-weight:bold;">{t("open_in_new_tab")} ↗</a>', unsafe_allow_html=True)
        st.caption("⚽ Alternative live stream – enjoy the matches via the second feed.")
    st.markdown("---")
    st.info("ℹ️ Stream provided by a third‑party site. If the stream does not load, try refreshing or switching to the other tab.")

# ====== OWN PROFILE ======
def render_profile():
    st.header(t("profile"))
    render_top_icons()
    if st.session_state.profile is None:
        return
    profile = st.session_state.profile
    col1, col2 = st.columns([1,2])
    with col1:
        display_avatar_and_followers(profile.get("avatar_url"), st.session_state.user.id, size=200, profile=profile)
        uploaded = st.file_uploader(t("change_picture"), type=["png","jpg","jpeg","gif"], label_visibility="collapsed")
        if uploaded:
            url = upload_avatar(st.session_state.user.id, uploaded)
            if url:
                profile["avatar_url"] = url
                update_profile(profile)
                st.success("Avatar updated successfully!")
                st.rerun()
            else:
                st.error("Avatar upload failed. Please try again.")
    with col2:
        with st.form("edit_profile"):
            st.markdown("#### Account Information")
            full_name = st.text_input(t("full_name"), value=profile.get("full_name", ""))
            bio = st.text_area(t("bio"), value=profile.get("bio", ""), height=100)
            location = st.text_input(t("location"), value=profile.get("location", ""))
            moncash_phone = st.text_input(t("moncash_phone"), value=profile.get("moncash_phone", ""))
            natcash_phone = st.text_input(t("natcash_phone"), value=profile.get("natcash_phone", ""))
            email = st.text_input("Email (visible to friends)", value=profile.get("email", ""))
            whatsapp_phone = st.text_input(t("whatsapp_phone"), value=profile.get("whatsapp_phone", ""))
            profile_visibility = st.radio(t("profile_visibility"), ["public", "private"], index=0 if profile.get("profile_visibility", "public") == "public" else 1)
            if st.form_submit_button(t("save_changes"), use_container_width=True):
                profile.update({
                    "full_name": full_name,
                    "bio": bio,
                    "location": location,
                    "moncash_phone": moncash_phone,
                    "natcash_phone": natcash_phone,
                    "email": email,
                    "whatsapp_phone": whatsapp_phone,
                    "profile_visibility": profile_visibility
                })
                if update_profile(profile):
                    st.success(t("profile"))
                    st.rerun()
    st.divider()
    total_posts = get_user_post_count(st.session_state.user.id, public_only=False)
    cola, colb, colc, cold = st.columns(4)
    with cola:
        st.metric(t("posts_count"), total_posts)
    with colb:
        st.metric("Followers", "1MFollowers")
    with colc:
        st.metric(t("verified"), "✅" if profile.get("verified", False) else "❌")
    with cold:
        st.metric(t("member_since"), profile.get("join_date", "2024")[:10])
    st.divider()
    # ---- Albums section in profile ----
    st.subheader(t("albums"))
    albums = get_user_albums(st.session_state.user.id, include_private=True)
    if not albums:
        st.info(t("no_albums"))
    else:
        cols = st.columns(3)
        for idx, album in enumerate(albums):
            with cols[idx % 3]:
                with st.container():
                    st.markdown(f'<div class="album-card">', unsafe_allow_html=True)
                    if album.get("cover_photo"):
                        st.image(album["cover_photo"], width=200)
                    else:
                        st.image("https://via.placeholder.com/200x150?text=No+Photo", width=200)
                    st.markdown(f"<div class='album-title'>{album['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='album-meta'>{album['description'][:50]}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='album-meta'>Visibility: {'Public' if album['visibility']=='public' else 'Private'}</div>", unsafe_allow_html=True)
                    if st.button(t("view_album"), key=f"view_album_own_{album['id']}"):
                        st.session_state.viewing_album = album['id']
                        st.rerun()
                    if st.button(t("delete_album"), key=f"del_album_own_{album['id']}"):
                        if delete_album(album['id']):
                            st.success(t("album_deleted"))
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    with st.expander(t("create_album")):
        with st.form("create_album_form_own"):
            album_title = st.text_input(t("album_title"))
            album_desc = st.text_area(t("album_description"))
            album_vis = st.selectbox(t("album_visibility"), [t("album_public"), t("album_private")])
            uploaded_files = st.file_uploader(t("upload_photos"), type=["png","jpg","jpeg","gif"], accept_multiple_files=True)
            if st.form_submit_button(t("create_album")):
                if album_title and uploaded_files:
                    visibility = 'public' if album_vis == t("album_public") else 'private'
                    album = create_album(st.session_state.user.id, album_title, album_desc, visibility)
                    if album:
                        if upload_album_photos(album["id"], uploaded_files):
                            st.success(t("album_created") + " " + t("photos_uploaded"))
                            st.rerun()
                        else:
                            st.error("Failed to upload photos.")
                else:
                    st.warning("Please provide title and at least one photo.")
    if st.session_state.viewing_album:
        album_id = st.session_state.viewing_album
        album_data = supabase.table("photo_albums").select("*").eq("id", album_id).execute().data
        if album_data:
            album = album_data[0]
            photos = get_album_photos(album_id)
            st.subheader(f"📸 {album['title']}")
            st.caption(album['description'])
            st.caption(f"Visibility: {album['visibility']}")
            if photos:
                st.markdown('<div class="photo-grid">', unsafe_allow_html=True)
                for photo in photos:
                    st.image(photo["photo_url"], use_column_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No photos in this album.")
            if st.button("← Back to Profile"):
                st.session_state.viewing_album = None
                st.rerun()
        else:
            st.error("Album not found.")
            st.session_state.viewing_album = None
    st.divider()
    st.subheader(t("my_live_sessions"))
    user_live_sessions = get_user_live_sessions(st.session_state.user.id)
    if not user_live_sessions:
        st.info("You haven't started any live sessions yet.")
    else:
        for sess in user_live_sessions:
            with st.container():
                col_a, col_b, col_c = st.columns([3,3,1])
                with col_a:
                    st.markdown(f"**{sess['title']}**")
                    st.caption(f"Started: {sess['started_at'][:16]}")
                with col_b:
                    if sess.get('is_live'):
                        st.markdown(f"<span class='live-badge'>{t('live_status_live')}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='color:gray;'>{t('live_status_ended')}</span>", unsafe_allow_html=True)
                with col_c:
                    if sess.get('is_live'):
                        if st.button(t("join_live"), key=f"join_live_{sess['id']}"):
                            st.session_state.viewing_live = sess['id']
                            st.rerun()
                st.divider()
    st.divider()
    st.subheader(t("my_wall"))
    user_posts = [p for p in st.session_state.posts if p['user_id'] == st.session_state.user.id]
    if not user_posts:
        st.info("You haven't posted anything yet.")
    else:
        for post in user_posts:
            with st.container():
                col_a, col_b, col_c, col_d, col_e = st.columns([1,4,2,1,1])
                with col_a:
                    display_avatar_and_followers(post["profiles"].get("avatar_url"), post["user_id"], size=40, profile=st.session_state.profile)
                with col_b:
                    st.markdown(f"**{post['profiles']['full_name']}**")
                    if post.get("profiles", {}).get("is_live"):
                        st.markdown(f"<span class='green-dot'></span>", unsafe_allow_html=True)
                    if not post.get("is_public", True):
                        st.markdown("<span class='private-badge'>Private</span>", unsafe_allow_html=True)
                with col_c:
                    st.caption(post['created_at'][:16])
                with col_d:
                    if st.button("✏️", key=f"edit_{post['id']}"):
                        st.session_state.editing_post = post['id']
                        st.rerun()
                with col_e:
                    if st.button("🗑️", key=f"del_{post['id']}"):
                        st.session_state.delete_confirm = (post['id'], post['content'][:30])
                        st.rerun()
                if st.session_state.editing_post == post['id']:
                    with st.form(key=f"edit_form_{post['id']}"):
                        new_content = st.text_area("Edit caption", value=post.get('content', ''), height=100)
                        new_media = st.file_uploader("Add additional media", type=["png","jpg","jpeg","gif","mp4","mov","avi"], accept_multiple_files=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Save"):
                                existing = post.get('media_urls', [])
                                if update_post(post['id'], st.session_state.user.id, new_content, new_media, existing):
                                    st.session_state.editing_post = None
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.editing_post = None
                                st.rerun()
                    st.divider()
                media_urls = post.get("media_urls", [])
                if media_urls:
                    for media in media_urls:
                        display_media_item(media)
                if post['content']:
                    clickable_content = make_clickable(post['content'])
                    st.markdown(f"<div class='post-card'>{clickable_content}</div>", unsafe_allow_html=True)
                    urls = re.findall(r'(https?://[^\s]+)', post['content'])
                    for url in urls:
                        embed_video_from_url(url)
                emojis = ["👍","👎","❤️","😂","😮","😢","👏"]
                reaction_counts = post.get("reactions", {})
                summary = " ".join([f"{emoji} {count}" for emoji, count in list(reaction_counts.items())[:3]])
                col_react, col_comments, col_shares = st.columns([2,1,1])
                with col_react:
                    if st.button("👍 React", key=f"react_btn_{post['id']}"):
                        st.session_state[f"show_reactions_{post['id']}"] = not st.session_state.get(f"show_reactions_{post['id']}", False)
                        st.rerun()
                    if st.session_state.get(f"show_reactions_{post['id']}", False):
                        st.markdown("**Choose reaction**")
                        for i in range(0, len(emojis), 3):
                            cols = st.columns(3)
                            for j, emoji in enumerate(emojis[i:i+3]):
                                with cols[j]:
                                    if st.button(emoji, key=f"react_{post['id']}_{emoji}"):
                                        toggle_reaction(post['id'], st.session_state.user.id, emoji)
                                        st.session_state[f"show_reactions_{post['id']}"] = False
                                        st.rerun()
                    if summary:
                        st.markdown(f"<small>{summary}</small>", unsafe_allow_html=True)
                with col_comments:
                    st.markdown(f"💬 {post.get('comment_count',0)}")
                with col_shares:
                    if st.button(f"🔄 {post['shares_count']}", key=f"share_{post['id']}"):
                        share_post(post['id'], st.session_state.user.id, is_public=True)
                        st.rerun()
                st.markdown("<div class='comment-section'>", unsafe_allow_html=True)
                st.markdown(f"#### {t('comments')}")
                with st.form(key=f"new_comment_{post['id']}", clear_on_submit=True):
                    msg = st.text_input(t("write_comment"), label_visibility="collapsed", placeholder=t("write_comment"))
                    if st.form_submit_button(t("post")):
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
                    col_avatar_comment, col1, col2, col3, col4 = st.columns([1,4,1,1,1])
                    with col_avatar_comment:
                        display_avatar_and_followers(c['profiles'].get('avatar_url'), c['user_id'], size=30, profile=c['profiles'])
                    with col1:
                        clickable_comment = make_clickable(c['content'])
                        st.markdown(f"**{c['profiles']['full_name']}**: {clickable_comment}")
                        st.markdown(f"<span class='comment-meta'>{c['created_at'][:16]}</span>", unsafe_allow_html=True)
                    with col2:
                        if st.button(f"👍 {c.get('likes',0)}", key=f"like_{c['id']}"):
                            like_comment(c['id'], increment=True)
                            st.rerun()
                    with col3:
                        if st.button(t("reply"), key=f"reply_{c['id']}"):
                            st.session_state.replying_to[c['id']] = not st.session_state.replying_to.get(c['id'], False)
                            st.rerun()
                    with col4:
                        if st.session_state.user and c['user_id'] == st.session_state.user.id:
                            if st.button("🗑️", key=f"del_comment_{c['id']}"):
                                delete_comment(c['id'])
                                st.rerun()
                    if st.session_state.replying_to.get(c['id'], False):
                        with st.form(key=f"reply_form_{c['id']}"):
                            reply = st.text_input(t("your_reply"), label_visibility="collapsed", placeholder=t("your_reply"))
                            if st.form_submit_button(t("post_reply")):
                                if reply:
                                    add_comment(post['id'], st.session_state.user.id, reply, parent_id=c['id'])
                                    st.session_state.replying_to[c['id']] = False
                                    st.rerun()
                    for r in replies.get(c['id'], []):
                        st.markdown("<div class='comment-indent'>", unsafe_allow_html=True)
                        colr_avatar, colr1, colr2, colr3, colr4 = st.columns([1,4,1,1,1])
                        with colr_avatar:
                            display_avatar_and_followers(r['profiles'].get('avatar_url'), r['user_id'], size=30, profile=r['profiles'])
                        with colr1:
                            clickable_reply = make_clickable(r['content'])
                            st.markdown(f"**{r['profiles']['full_name']}**: {clickable_reply}")
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

# ====== OWNER SPACE ======
def owner_space():
    st.header(t("owner_space"))
    if not st.session_state.owner_space_access:
        with st.form("owner_space_login"):
            pwd = st.text_input("Enter Owner Space Password", type="password")
            if st.form_submit_button(t("login_button")):
                if pwd.strip() == OWNSPACE_PASSWORD.strip():
                    st.session_state.owner_space_access = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return

    # ====== OWNER DASHBOARD CONTENT (with full error handling) ======
    try:
        last_seen = get_last_seen_signup()
        new_users = get_new_users(last_seen)
        if new_users:
            send_email_notification(new_users)
            update_last_seen_signup()
    except Exception as e:
        st.warning(f"⚠️ Could not load new users: {e}")
        new_users = []

    tabs = st.tabs([
        t("dashboard"), t("new_users"), t("post_moderation"),
        t("client_payments"), t("gift_management"), t("user_management"),
        "📸 Albums", "🕵️ Live Monitoring"
    ])

    # ---- TAB 1: Dashboard ----
    with tabs[0]:
        try:
            st.subheader(t("owner_dashboard"))
            real_balance = None
            if BACKEND_API_URL and BACKEND_API_URL != "https://your-backend.com":
                try:
                    headers = {"X-API-Key": BACKEND_API_KEY}
                    resp = requests.get(f"{BACKEND_API_URL}/api/balance", headers=headers, timeout=5)
                    if resp.status_code == 200:
                        real_balance = resp.json().get("balance", 0.0)
                    else:
                        st.warning("Could not fetch real balance from backend.")
                except Exception:
                    st.warning("Backend unreachable.")
            else:
                st.info("Backend not configured. Showing simulated data for now.")

            col1, col2, col3 = st.columns(3)
            with col1:
                if real_balance is not None:
                    st.metric(t("balance"), f"${real_balance:,.2f}")
                else:
                    duration = time.time() - st.session_state.connection_time
                    st.session_state.data_comp = duration * 0.035
                    st.metric(t("compensation"), f"${st.session_state.data_comp:.4f}")
            with col2:
                st.metric(t("uptime"), get_uptime())
            with col3:
                st.metric(t("connections"), np.random.randint(100, 500))

            st.divider()
            st.subheader(t("transfer_funds"))
            st.markdown(f"**Your MonCash Business Number:** `{MONCASH_NUM}`")
            st.markdown(f"**Your UNIBANK US Account:** `{UNIBANK_ACCOUNT}`")
            if real_balance is not None:
                amount = st.number_input(t("amount_transfer"), min_value=1.0, max_value=float(real_balance),
                                         value=min(10.0, float(real_balance)), step=10.0, format="%.2f")
                if st.button(t("transfer"), use_container_width=True):
                    if amount <= 0:
                        st.error("Enter a valid amount.")
                    else:
                        with st.spinner("Processing transfer..."):
                            try:
                                headers = {"X-API-Key": BACKEND_API_KEY, "Content-Type": "application/json"}
                                payload = {"amount": amount, "recipient_phone": MONCASH_NUM}
                                resp = requests.post(f"{BACKEND_API_URL}/api/transfer", headers=headers,
                                                     json=payload, timeout=10)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    st.success(f"✅ Transfer initiated! Transaction ID: {data.get('transaction_id')}")
                                else:
                                    st.error(f"Transfer failed: {resp.text}")
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.info("To enable real transfers, set up your backend and configure the secrets.")
        except Exception as e:
            st.error(f"Error in Dashboard tab: {e}")
            st.exception(e)

    # ---- TAB 2: New Users ----
    with tabs[1]:
        try:
            st.subheader(t("new_users"))
            st.markdown("All recent user signups. Click refresh to update, and download the report at any time.")
            with st.spinner("Loading user data..."):
                response = supabase.table("profiles").select(
                    "id, full_name, avatar_url, join_date, location, bio, is_banned, last_active"
                ).order("join_date", desc=True).limit(100).execute()
                recent_users = response.data if response.data else []
            if recent_users:
                display_data = []
                for u in recent_users:
                    display_data.append({
                        "Full Name": u.get('full_name', 'N/A'),
                        "User ID": u['id'],
                        "Joined": u.get('join_date', '')[:16] if u.get('join_date') else 'Unknown',
                        "Location": u.get('location', 'Not set'),
                        "Bio": u.get('bio', '')[:50] + ('...' if len(u.get('bio', '')) > 50 else ''),
                        "Banned": "✅" if u.get('is_banned') else "❌",
                        "Online": "🟢" if is_user_online(u.get('last_active')) else "⚪"
                    })
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Report as CSV",
                    data=csv,
                    file_name=f"new_users_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No users found in the database.")
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        except Exception as e:
            st.error(f"Error in New Users tab: {e}")
            st.exception(e)

    # ---- TAB 3: Post Moderation ----
    with tabs[2]:
        try:
            st.subheader(t("post_moderation"))
            st.markdown("Review all posts (public & private) and take action if needed.")
            posts_resp = supabase.table("posts").select("*").order("created_at", desc=True).execute()
            all_posts = posts_resp.data or []
            user_ids = {p["user_id"] for p in all_posts}
            profiles = {}
            if user_ids:
                prof_resp = supabase.table("profiles").select(
                    "id, full_name, avatar_url, last_active"
                ).in_("id", list(user_ids)).execute()
                for p in prof_resp.data or []:
                    profiles[p["id"]] = p
            for p in all_posts:
                prof = profiles.get(p["user_id"], {})
                p["profiles"] = {
                    "full_name": prof.get("full_name", "Unknown"),
                    "avatar_url": prof.get("avatar_url"),
                    "id": p["user_id"],
                    "last_active": prof.get("last_active")
                }
            if not all_posts:
                st.info("No posts found.")
            else:
                if "warn_post_id" not in st.session_state:
                    st.session_state.warn_post_id = None
                for post in all_posts:
                    with st.container():
                        cols = st.columns([2, 3, 2, 1, 1, 1])
                        with cols[0]:
                            display_avatar_and_followers(post['profiles']['avatar_url'],
                                                         post['user_id'], size=30, profile=post['profiles'])
                            st.markdown(f"**User:** {post['profiles']['full_name']}")
                        with cols[1]:
                            content = post.get('content', '')[:100] + "..." if post.get('content') and len(
                                post['content']) > 100 else post.get('content', '')
                            st.markdown(f"**Content:** {content}")
                        with cols[2]:
                            visibility_label = "Public" if post.get('is_public', True) else "Private"
                            st.markdown(f"**Visibility:** {visibility_label}")
                            st.caption(post['created_at'][:16])
                        with cols[3]:
                            if post.get('is_public', True):
                                if st.button("🔒 Hide from Public", key=f"hide_{post['id']}"):
                                    success, msg = toggle_post_visibility(post['id'], False)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            else:
                                if st.button("🌐 Make Public", key=f"unhide_{post['id']}"):
                                    success, msg = toggle_post_visibility(post['id'], True)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                        with cols[4]:
                            if st.button(t("delete_post"), key=f"del_{post['id']}"):
                                if delete_post(post['id']):
                                    st.success("Post deleted.")
                                    st.rerun()
                                else:
                                    st.error("Delete failed.")
                        with cols[5]:
                            if st.button("⚠️ Warn", key=f"warn_{post['id']}"):
                                st.session_state.warn_post_id = post['id']
                                st.rerun()
                        if st.session_state.warn_post_id == post['id']:
                            with st.form(key=f"warn_form_{post['id']}"):
                                default_msg = f"Your post '{post.get('content', '')[:50]}...' contains sensitive content and has been removed. Please review our community guidelines."
                                warn_msg = st.text_area("Warning message", value=default_msg, height=100)
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("Send Warning"):
                                        success = send_message(st.session_state.user.id, post['user_id'],
                                                                f"[MODERATION] {warn_msg}")
                                        if success:
                                            st.success("Warning sent to user.")
                                            if delete_post(post['id']):
                                                st.info("Post also deleted.")
                                            st.session_state.warn_post_id = None
                                            st.rerun()
                                        else:
                                            st.error("Failed to send message.")
                                with col2:
                                    if st.form_submit_button("Cancel"):
                                        st.session_state.warn_post_id = None
                                        st.rerun()
                        st.divider()
        except Exception as e:
            st.error(f"Error in Post Moderation tab: {e}")
            st.exception(e)

    # ---- TAB 4: Client Payments ----
    with tabs[3]:
        try:
            st.subheader(t("client_payments"))
            st.markdown("""
            **Option 1 – MonCash (for amounts ≤ 1000 HTG)**  
            Clients can send money directly to your MonCash personal number:  
            `+50947385663`  
            *(They must use the MonCash app or a MonCash agent.)*

            **Option 2 – US Bank Transfer (for any amount)**  
            For international clients, you can receive USD via bank transfer to your UNIBANK account:  
            `105-2016-16594727`  
            *(Provide them with your bank name: UNIBANK, Haiti.)*

            **Option 3 – Request a payment link**  
            For larger amounts, contact the development team to generate a secure payment link.
            """)
        except Exception as e:
            st.error(f"Error in Payments tab: {e}")
            st.exception(e)

    # ---- TAB 5: Gift Management ----
    with tabs[4]:
        try:
            st.subheader(t("gift_management"))
            st.markdown("View all completed gifts and process payouts to streamers.")
            if supabase is None:
                st.warning("Supabase not connected.")
                return
            gifts_resp = supabase.table("live_gifts").select("*").eq("status", "completed").order("created_at",
                                                                                                 desc=True).execute()
            gifts_data = gifts_resp.data if gifts_resp.data else []
            if not gifts_data:
                st.info(t("no_gifts"))
            else:
                df = pd.DataFrame([{
                    "ID": g['id'],
                    "Date": g['created_at'][:16],
                    "Session ID": g['session_id'],
                    "Sender": g.get('sender_name', 'Unknown'),
                    "Recipient ID": g['recipient_id'],
                    "Amount": f"{g['amount']} {g['currency']}",
                    "Converted (HTG)": f"{g['converted_amount_htg']:.0f} HTG"
                } for g in gifts_data])
                st.dataframe(df, use_container_width=True)
                st.markdown(f"### {t('payout_summary')}")
                total_pending = sum(g['converted_amount_htg'] for g in gifts_data if g.get('status') == 'completed')
                st.metric(t("total_gifts_htg"), f"{total_pending:.0f} HTG")
                if st.button(t("mark_paid")):
                    st.success("Payout simulation complete. In reality, this would transfer funds to streamers' MonCash accounts.")
        except Exception as e:
            st.error(f"Error in Gift Management tab: {e}")
            st.exception(e)

    # ---- TAB 6: User Management ----
    with tabs[5]:
        try:
            st.subheader(t("user_management"))
            st.markdown("Search and manage users: ban/unban accounts.")
            search_term = st.text_input("🔍 Search by name or user ID")
            all_users = get_all_users()
            if search_term:
                filtered = [u for u in all_users if search_term.lower() in u['full_name'].lower() or search_term in u['id']]
            else:
                filtered = all_users
            if not filtered:
                st.info("No users found.")
            else:
                for user in filtered:
                    cols = st.columns([2, 2, 2, 1, 1])
                    with cols[0]:
                        st.markdown(f"**{user['full_name']}**")
                    with cols[1]:
                        st.caption(f"ID: {user['id'][:8]}...")
                    with cols[2]:
                        status = "🚫 Banned" if user.get('is_banned') else "✅ Active"
                        st.markdown(status)
                        if user.get('is_banned') and user.get('ban_reason'):
                            st.caption(f"Reason: {user['ban_reason']}")
                    with cols[3]:
                        if user.get('is_banned'):
                            if st.button(t("unban_user"), key=f"unban_{user['id']}"):
                                success, msg = unban_user(user['id'])
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            if st.button(t("ban_user"), key=f"ban_{user['id']}"):
                                with st.popover("Enter ban reason"):
                                    reason = st.text_input("Reason (optional)")
                                    if st.button("Confirm Ban"):
                                        success, msg = ban_user(user['id'], reason)
                                        if success:
                                            st.success(msg)
                                            st.rerun()
                                        else:
                                            st.error(msg)
                    with cols[4]:
                        online = is_user_online(user.get('last_active'))
                        st.markdown("🟢 Online" if online else "⚪ Offline")
        except Exception as e:
            st.error(f"Error in User Management tab: {e}")
            st.exception(e)

    # ---- TAB 7: Albums (Owner view all albums) ----
    with tabs[6]:
        try:
            st.subheader(t("owner_albums"))
            all_albums = get_all_albums(include_private=True)
            if not all_albums:
                st.info("No albums created yet.")
            else:
                for album in all_albums:
                    with st.container():
                        cols = st.columns([1,3,1,1])
                        with cols[0]:
                            if album.get("cover_photo"):
                                st.image(album["cover_photo"], width=100)
                            else:
                                st.image("https://via.placeholder.com/100x100?text=No+Photo", width=100)
                        with cols[1]:
                            st.markdown(f"**{album['title']}**")
                            st.caption(f"Owner: {album.get('owner_name', 'Unknown')}")
                            st.caption(f"Description: {album['description']}")
                            st.caption(f"Visibility: {album['visibility']}")
                        with cols[2]:
                            if st.button("View", key=f"owner_view_album_{album['id']}"):
                                st.session_state.viewing_album = album['id']
                                st.rerun()
                        with cols[3]:
                            if st.button("Delete", key=f"owner_del_album_{album['id']}"):
                                if delete_album(album['id']):
                                    st.success("Album deleted.")
                                    st.rerun()
                        st.divider()
        except Exception as e:
            st.error(f"Error in Albums tab: {e}")
            st.exception(e)

    # ---- TAB 8: Live Monitoring ----
    with tabs[7]:
        try:
            st.subheader("🕵️ Live Video Call Monitoring")
            st.info("Here you can see all active video calls. Click 'Monitor' to join the call anonymously (the participants will see you as 'Monitor'). To record, we recommend using a screen recorder tool, as Jitsi recording requires additional setup.")
            active_calls = get_active_video_calls()
            if not active_calls:
                st.info("No active video calls at the moment.")
            else:
                for call in active_calls:
                    with st.container():
                        cols = st.columns([2,2,1,1])
                        with cols[0]:
                            st.markdown(f"**Room:** {call['room']}")
                            st.caption(f"Started: {call['started_at'][:16]}")
                        with cols[1]:
                            user_name = call.get('profiles', {}).get('full_name', 'Unknown')
                            st.markdown(f"**User:** {user_name}")
                        with cols[2]:
                            # Join as Monitor - we can provide the room link
                            room = call['room']
                            domain = JITSI_DOMAIN
                            monitor_url = f"https://{domain}/{room}"
                            st.markdown(f'<a href="{monitor_url}" target="_blank"><button>Monitor</button></a>', unsafe_allow_html=True)
                        with cols[3]:
                            if st.button("End Call (force)", key=f"end_call_{call['id']}"):
                                st.warning("Force ending call is not implemented. Please ask user to end call.")
                        st.divider()
        except Exception as e:
            st.error(f"Error in Live Monitoring tab: {e}")
            st.exception(e)

    # ---- Footer ----
    st.divider()
    st.markdown(f"### {t('contact_support')}")
    st.markdown("Email: `deslandes78@gmail.com`  \nWhatsApp: `+50947385663`")
    if st.button(t("logout_owner")):
        st.session_state.owner_space_access = False
        st.rerun()

# ====== VIDEO CALL PAGE ======
def render_video_call():
    st.header(t("video_call"))
    st.info(t("demo_note"))
    user_id = st.session_state.user.id
    room = f"lakay-call-{user_id}"
    st.markdown(f"### {t('your_personal_room')}: `{room}`")
    try:
        base_url = st.request.url.split('?')[0]
    except:
        base_url = "https://lakay-se-lakay.streamlit.app"
    room_url = f"{base_url}?call={room}"
    st.text_input("🔗 Shareable Link", value=room_url, key="call_room_link")
    if st.button(t("copy_link")):
        st.markdown(f"<script>navigator.clipboard.writeText('{room_url}');</script>", unsafe_allow_html=True)
        st.success(t("room_link_copied"))
    st.markdown(f"### {t('join_room')}")
    domain = JITSI_DOMAIN
    container_id = f"jitsi-call-{user_id}"
    config_overwrite = {"startWithAudioMuted": False, "startWithVideoMuted": False, "disableWelcomePage": True, "disableDeepLinking": True, "p2p": {"enabled": False}}
    config_json = json.dumps(config_overwrite)
    jitsi_html = f"""
    <div id="{container_id}" style="height: 500px; width: 100%;"></div>
    <script src="https://{domain}/external_api.js"></script>
    <script>
      (function() {{
        const domain = '{domain}';
        const room = '{room}';
        const config = {config_json};
        const container = document.getElementById('{container_id}');
        if (!container) return;
        if (typeof JitsiMeetExternalAPI !== 'undefined') {{
            const api = new JitsiMeetExternalAPI(domain, {{
                roomName: room,
                parentNode: container,
                configOverwrite: config
            }});
        }} else {{
            setTimeout(function() {{
                if (typeof JitsiMeetExternalAPI !== 'undefined') {{
                    const api = new JitsiMeetExternalAPI(domain, {{
                        roomName: room,
                        parentNode: container,
                        configOverwrite: config
                    }});
                }}
            }}, 1000);
        }}
      }})();
    </script>
    """
    st.components.v1.html(jitsi_html, height=520)
    st.markdown(f"**Or open in a new tab:** [Join Room](https://{domain}/{room})", unsafe_allow_html=True)
    st.caption(t("call_permission_hint"))

# ====== LIVE PAGE ======
def render_live_page(session_id):
    session = get_live_session(session_id)
    if not session or not session.get("is_live"):
        st.error("This live session has ended or does not exist.")
        if st.button(t("back_to_feed")):
            st.session_state.viewing_live = None
            st.rerun()
        return
    is_broadcaster = st.session_state.user and session["user_id"] == st.session_state.user.id
    st.header(f"🔴 LIVE: {session['title']}")
    if st.session_state.user:
        bg_key = f"bg_{session_id}_{st.session_state.user.id}"
        if st.session_state.get(bg_key) is None:
            st.session_state[bg_key] = None
        if not is_broadcaster:
            participant_status = None
            try:
                part = supabase.table("live_participants").select("status").eq("session_id", session_id).eq("user_id", st.session_state.user.id).execute()
                if part.data:
                    participant_status = part.data[0]["status"]
            except Exception:
                pass
            if participant_status == "accepted":
                with st.expander(t("choose_background"), expanded=False):
                    uploaded_bg = st.file_uploader(t("upload_background"), type=["png","jpg","jpeg"], key=f"bg_upload_{session_id}")
                    if uploaded_bg:
                        bytes_data = uploaded_bg.getvalue()
                        b64 = base64.b64encode(bytes_data).decode()
                        mime = uploaded_bg.type
                        data_url = f"data:{mime};base64,{b64}"
                        st.session_state[bg_key] = data_url
                        supabase.table("live_participants").update({"background_url": data_url}).eq("session_id", session_id).eq("user_id", st.session_state.user.id).execute()
                        st.success(t("background_set"))
                        st.rerun()
    gifts = load_gifts_for_session(session_id)
    total_gifts_htg = sum(g.get('converted_amount_htg', 0) for g in gifts)
    col1, col2 = st.columns([2,1])
    with col1:
        col_avatar_broadcaster, col_name_broadcaster = st.columns([1,4])
        with col_avatar_broadcaster:
            display_avatar_and_followers(session["profiles"]["avatar_url"], session["user_id"], size=60, profile=session["profiles"])
        with col_name_broadcaster:
            st.markdown(f"**{session['profiles']['full_name']}** is live")
        stream_method = session.get("stream_method", "external")
        if stream_method == "external":
            stream_url = session.get("stream_url")
            platform = session.get("platform")
            if is_broadcaster:
                with st.expander(t("set_stream_url"), expanded=not stream_url):
                    with st.form("update_stream_url"):
                        new_url = st.text_input(f"{t('paste_url')} (YouTube, Facebook, Twitch)", value=stream_url or "")
                        if st.form_submit_button(t("update_url")):
                            if new_url:
                                if update_live_stream_url(session_id, new_url):
                                    st.success("Stream URL updated! Refreshing...")
                                    st.rerun()
                            else:
                                st.warning("Please enter a URL")
            if stream_url:
                if "facebook.com" in stream_url:
                    st.components.v1.html(f'<div id="fb-root"></div><script async defer src="https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v3.2"></script><div class="fb-video" data-href="{stream_url}" data-width="100%" data-allowfullscreen="true"></div>', height=450)
                elif "youtube.com" in stream_url or "youtu.be" in stream_url:
                    if "youtu.be" in stream_url:
                        video_id = stream_url.split("/")[-1].split("?")[0]
                    elif "watch?v=" in stream_url:
                        video_id = stream_url.split("v=")[-1].split("&")[0]
                    else:
                        video_id = None
                    if video_id:
                        st.components.v1.html(f'<iframe width="100%" height="400" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="encrypted-media" allowfullscreen></iframe>', height=410)
                    else:
                        st.video(stream_url, autoplay=False)
                elif "twitch.tv" in stream_url:
                    channel = stream_url.split("/")[-1].split("?")[0]
                    embed_url = f"https://player.twitch.tv/?channel={channel}&parent={st.request.host}"
                    st.components.v1.html(f'<iframe src="{embed_url}" height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>', height=410)
                else:
                    st.video(stream_url, autoplay=False)
            else:
                st.info("The streamer has not provided a video URL yet.")
        else:
            can_view = is_broadcaster
            if not can_view and st.session_state.user:
                part = supabase.table("live_participants").select("status").eq("session_id", session_id).eq("user_id", st.session_state.user.id).execute()
                if part.data and part.data[0]["status"] == "accepted":
                    can_view = True
            if can_view:
                room_name = f"lakay-live-{session_id}"
                container_id = f"jitsi-live-{session_id}"
                domain = JITSI_DOMAIN
                config_overwrite = {"startWithAudioMuted": False, "startWithVideoMuted": False, "disableWelcomePage": True, "disableDeepLinking": True, "p2p": {"enabled": False}}
                config_json = json.dumps(config_overwrite)
                jitsi_html = f"""
                <div id="{container_id}" style="height: 500px; width: 100%;"></div>
                <script src="https://{domain}/external_api.js"></script>
                <script>
                  (function() {{
                    const domain = '{domain}';
                    const room = '{room_name}';
                    const config = {config_json};
                    const container = document.getElementById('{container_id}');
                    if (!container) return;
                    if (typeof JitsiMeetExternalAPI !== 'undefined') {{
                        const api = new JitsiMeetExternalAPI(domain, {{
                            roomName: room,
                            parentNode: container,
                            configOverwrite: config
                        }});
                    }} else {{
                        setTimeout(function() {{
                            if (typeof JitsiMeetExternalAPI !== 'undefined') {{
                                const api = new JitsiMeetExternalAPI(domain, {{
                                    roomName: room,
                                    parentNode: container,
                                    configOverwrite: config
                                }});
                            }}
                        }}, 1000);
                    }}
                  }})();
                </script>
                """
                st.components.v1.html(jitsi_html, height=520)
            else:
                if st.session_state.user:
                    part = supabase.table("live_participants").select("status").eq("session_id", session_id).eq("user_id", st.session_state.user.id).execute()
                    if part.data:
                        if part.data[0]["status"] == "pending":
                            st.info(t("request_pending"))
                        elif part.data[0]["status"] == "rejected":
                            st.warning("Your request was rejected by the broadcaster.")
                        else:
                            st.info("You are a viewer. The broadcaster has not yet accepted your request.")
                    else:
                        if st.button(t("request_to_join"), key=f"request_join_{session_id}"):
                            try:
                                supabase.table("live_participants").insert({"session_id": session_id, "user_id": st.session_state.user.id, "status": "pending"}).execute()
                                st.success("Request sent! Waiting for broadcaster approval.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to send request: {e}")
                else:
                    st.info("Please log in to request to join this live stream.")
            if is_broadcaster:
                st.subheader(t("broadcaster_controls"))
                try:
                    pending = supabase.table("live_participants").select("*, profiles!live_participants_user_id_fkey(full_name, avatar_url, last_active)").eq("session_id", session_id).eq("status", "pending").execute()
                    pending_list = pending.data or []
                except Exception:
                    pending_list = []
                if pending_list:
                    st.markdown("**Pending join requests**")
                    for req in pending_list:
                        cols = st.columns([3,1,1])
                        with cols[0]:
                            display_avatar_and_followers(req['profiles']['avatar_url'], req['user_id'], size=30, profile=req['profiles'])
                            st.markdown(f"**{req['profiles']['full_name']}** wants to join")
                        with cols[1]:
                            if st.button("✅ Accept", key=f"accept_{req['id']}"):
                                supabase.table("live_participants").update({"status": "accepted"}).eq("id", req["id"]).execute()
                                try:
                                    supabase.table("notifications").insert({"user_id": req["user_id"], "type": "live_join_accepted", "message": f"You have been accepted to join the live stream: {session['title']}", "read": False}).execute()
                                except Exception:
                                    pass
                                st.rerun()
                        with cols[2]:
                            if st.button("❌ Reject", key=f"reject_{req['id']}"):
                                supabase.table("live_participants").delete().eq("id", req["id"]).execute()
                                st.rerun()
                else:
                    st.info("No pending requests")
                try:
                    accepted = supabase.table("live_participants").select("*, profiles!live_participants_user_id_fkey(full_name, avatar_url, last_active)").eq("session_id", session_id).eq("status", "accepted").execute()
                    accepted_list = accepted.data or []
                except Exception:
                    accepted_list = []
                if accepted_list:
                    st.markdown("**Active participants**")
                    for part in accepted_list:
                        cols = st.columns([2,1,1,1])
                        with cols[0]:
                            display_avatar_and_followers(part['profiles']['avatar_url'], part['user_id'], size=30, profile=part['profiles'])
                            st.markdown(f"**{part['profiles']['full_name']}**")
                        with cols[1]:
                            if st.button("🔊 Mute", key=f"mute_{part['id']}"):
                                supabase.table("live_participants").update({"status": "muted"}).eq("id", part["id"]).execute()
                                try:
                                    supabase.table("notifications").insert({"user_id": part["user_id"], "type": "live_mute", "message": f"The broadcaster has muted your microphone in {session['title']}", "read": False}).execute()
                                except Exception:
                                    pass
                                st.rerun()
                        with cols[2]:
                            if st.button("🔊 Unmute", key=f"unmute_{part['id']}"):
                                supabase.table("live_participants").update({"status": "accepted"}).eq("id", part["id"]).execute()
                                try:
                                    supabase.table("notifications").insert({"user_id": part["user_id"], "type": "live_unmute", "message": f"The broadcaster has unmuted your microphone in {session['title']}", "read": False}).execute()
                                except Exception:
                                    pass
                                st.rerun()
                        with cols[3]:
                            if st.button("❌ Remove", key=f"remove_{part['id']}"):
                                supabase.table("live_participants").delete().eq("id", part["id"]).execute()
                                st.rerun()
                else:
                    st.info("No active participants")
        try:
            base_url = st.request.url.split('?')[0]
        except:
            base_url = "https://lakay-se-lakay.streamlit.app"
        share_url = f"{base_url}?live={session_id}"
        st.text_input(t("shareable_link"), value=share_url)
    with col2:
        st.subheader(t("live_chat_gifts"))
        if not is_broadcaster:
            st.markdown(f"### {t('send_gift')}")
            if not st.session_state.profile.get("moncash_phone"):
                st.info(t("add_moncash"))
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
                            success, msg = send_gift(session_id, st.session_state.user.id, session["user_id"], opt["amount"], opt["currency"])
                            if success:
                                st.success(msg)
                                st.session_state.live_gifts = load_gifts_for_session(session_id)
                                st.rerun()
                            else:
                                st.error(msg)
            st.markdown("### 😊 Reactions")
            reaction_emojis = ["❤️", "👍", "😂", "😮", "😢", "👏"]
            cols = st.columns(len(reaction_emojis))
            for i, emoji in enumerate(reaction_emojis):
                with cols[i]:
                    if st.button(emoji, key=f"reaction_{i}"):
                        add_comment(session_id, st.session_state.user.id, f"🎉 {emoji}")
                        st.rerun()
        if is_broadcaster:
            st.metric(t("total_gifts"), f"{total_gifts_htg:.0f} HTG")
            moncash = session["profiles"].get("moncash_phone")
            natcash = session["profiles"].get("natcash_phone")
            if moncash:
                st.info(f"{t('gifts_sent_to')}: {moncash}")
            if natcash:
                st.info(f"{t('gifts_sent_to_natcash')}: {natcash}")
            if not moncash and not natcash:
                st.warning(t("add_moncash") + " / " + t("add_natcash"))
        else:
            moncash = session["profiles"].get("moncash_phone")
            natcash = session["profiles"].get("natcash_phone")
            if moncash or natcash:
                st.markdown("**💝 Support the broadcaster:**")
                if moncash:
                    st.markdown(f"MonCash: {moncash}")
                if natcash:
                    st.markdown(f"NATCASH: {natcash}")
        with st.form(f"live_comment_{session_id}", clear_on_submit=True):
            msg = st.text_input(t("write_comment"))
            if st.form_submit_button(t("send")):
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
                if c['content'].startswith("🎉"):
                    st.markdown(f"**{c['profiles']['full_name']}** {c['content']}")
                else:
                    st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
            else:
                g = ev['data']
                sender = g.get('sender', {}).get('full_name', 'Someone')
                st.markdown(f"🎁 **{sender}** sent a gift of {g['amount']} {g['currency']}!")

# ====== GLOBAL PAGE KEYS / TITLES for navigation ======
PAGE_KEYS = ["feed", "friends_chat", "satellite_map", "worldcup", "profile", "video_call", "owner_space"]
PAGE_TITLES = {key: t(key) for key in PAGE_KEYS}

# ========== MAIN APP ==========
def main_app():
    # Check for any lingering call status (auto-end after 30 sec)
    if st.session_state.call_ringing and st.session_state.call_initiated_time:
        elapsed = time.time() - st.session_state.call_initiated_time
        if elapsed > 30:
            st.session_state.call_ringing = False
            st.session_state.call_initiated_time = None
            end_call()
            st.warning(t("call_unavailable"))

    if st.session_state.logged_in and st.session_state.user:
        update_last_active(st.session_state.user.id)
    with st.sidebar:
        if st.session_state.logged_in:
            st.success("✅ Logged in")
        else:
            st.info("🔓 Not logged in")
        st.divider()
        st.markdown("<div class='haiti-symbol'>🇭🇹</div>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name'><span class='lakay-flag-text'>Lakay Se Lakay</span></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes<br>
            Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align: center; font-size: 0.9rem; color: #0a2a44; margin-top: 5px;'>
            <b>Gesner Deslandes</b><br>
            <span style='font-size: 0.8rem; color: #2c3e50;'>Software Engineer Founder</span>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        lang_options = {"en":"English","fr":"Français","es":"Español","ht":"Kreyòl Ayisyen"}
        selected_lang = st.selectbox(t("voice_lang"), options=list(lang_options.keys()), format_func=lambda x: lang_options[x], index=list(lang_options.keys()).index(st.session_state.language))
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()
        st.divider()

        # ====== EXTERNAL APP LINKS ======
        st.markdown("### 🌐 GlobalInternet.py Apps")
        st.markdown(
            """
            <a href="https://globalsurveillanceradarad-zxajfceg4timbxqkmpmyqt.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#00209F; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🛰️ Global Radar
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://globalinternetsitepy-abh7v6tnmskxxnuplrdcgk.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#D21034; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🌍 GlobalInternet.py
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://mathematics-problem-solver-2026-cjhmmanktwdwglxpxdpqtn.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#1a5276; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🧮 AI Math Solver
            </a>
            <p style="text-align:center; font-size:0.8rem; color:#2c3e50;">🔑 Login: 20082010</p>
            """,
            unsafe_allow_html=True
        )
        st.markdown("### 🎮 More GlobalInternet.py Apps")
        st.markdown(
            """
            <a href="https://playchessagainstthemachinemarch2026-hqnjksiy9jemcb4np5pzmp.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#2c3e50; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                ♟️ Chess vs Machine
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://puzzle-game-gdcx5vdkwhbbm824cwxcc9.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#8e44ad; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🧩 Puzzle Game
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://whiteboard-software-fdcqkycya2oe38ufvcybjm.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#1a5276; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                ✏️ Whiteboard Software
            </a>
            """,
            unsafe_allow_html=True
        )
        # NEW: Haiti Bus Race Game
        st.markdown(
            """
            <a href="https://haiti-bus-game-2026-gmoxzgjx8jqcuiarbg9mab.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#e67e22; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🚌 Haiti Bus Race Game
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://jqx4o4apg4jjnn3qi9jlhn.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#c0392b; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🎯 App 4
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://nic-honestly-crafted-ice-creams-je9srxl472sjg9xkaxzqgj.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#d4a017; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🍦 Ice Cream App
            </a>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
            <a href="https://hteer6e6gap5kpgmfsdh92.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#16a085; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                📊 App 6
            </a>
            """,
            unsafe_allow_html=True
        )
        st.divider()

        # ====== LOVE STORIES SECTION ======
        st.markdown("### 💕 Love Stories")
        love_stories = [
            ("Live in Love – Episode 1", "https://www.viki.com/videos/1260791v-live-in-love-episode-1"),
            ("Love Alarm", "https://www.viki.com/tv/37089c-love-alarm"),
            ("My Secret Romance", "https://www.viki.com/tv/34681c-my-secret-romance"),
            ("What's Wrong with Secretary Kim", "https://www.viki.com/tv/37295c-whats-wrong-with-secretary-kim"),
            ("Her Private Life", "https://www.viki.com/tv/37139c-her-private-life"),
            ("Touch Your Heart", "https://www.viki.com/tv/37398c-touch-your-heart"),
        ]
        for label, url in love_stories:
            if st.button(f"💕 {label}", key=f"love_{url}", use_container_width=True):
                st.session_state.love_story_url = url
                st.session_state.show_love_story = True
                st.rerun()
        st.divider()

        # ====== GLOBAL SHIELD STATUS ======
        st.markdown(f"### 🛡️ {t('security_badge')}")
        st.markdown(f"<div class='security-badge'>{t('security_caption')}</div>", unsafe_allow_html=True)
        if GLOBAL_SHIELD_ACTIVE:
            st.success("✅ Global Shield API Key active")
        else:
            st.warning("⚠️ Global Shield API Key not configured")
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
                        if st.button("📺 YouTube", key="yt"): platform = "YouTube"
                    with col2:
                        if st.button("📘 Facebook", key="fb"): platform = "Facebook"
                    with col3:
                        if st.button("🎮 Twitch", key="tw"): platform = "Twitch"
                else:
                    platform = "inapp"
                if platform:
                    st.markdown(f"**Selected: {platform if platform != 'inapp' else t('in_app_camera')}**")
                    with st.form("go_live_form"):
                        title = st.text_input(t("live_title"))
                        if st.form_submit_button(t("create_live_session")):
                            if title:
                                session_id = create_live_session(title, platform, method='external' if platform != 'inapp' else 'inapp')
                                if session_id:
                                    st.success(t("you_are_live"))
                                    if platform != 'inapp':
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
        if st.session_state.language == 'ht':
            st.warning("🔊 Voice explanation is not available in Kreyòl Ayisyen. Please select another language for audio.")
        else:
            if st.button(t("listen_explanation"), use_container_width=True):
                voice_map = {"en":"en-US-JennyNeural","fr":"fr-FR-DeniseNeural","es":"es-ES-ElviraNeural","ht":"ht-HT-FabriceNeural"}
                voice = voice_map.get(st.session_state.language, "en-US-JennyNeural")
                text = t("app_explanation")
                audio_file = generate_audio(text, voice)
                if audio_file:
                    play_audio(audio_file)
                else:
                    st.error("Failed to generate audio.")
        st.divider()

        # ---------- NAVIGATION ----------
        current_index = PAGE_KEYS.index(st.session_state.current_page)
        selected_title = st.selectbox(
            "Navigate",
            options=[PAGE_TITLES[key] for key in PAGE_KEYS],
            index=current_index,
            key="nav_selectbox"
        )
        selected_key = next(key for key, title in PAGE_TITLES.items() if title == selected_title)
        if selected_key != st.session_state.current_page:
            st.session_state.show_love_story = False
            st.session_state.love_story_url = None
            st.session_state.current_page = selected_key
            st.rerun()

        st.divider()
        # ---- Small Owner Space unlock in sidebar ----
        st.markdown("### 🕊️ Owner Space")
        if st.session_state.owner_space_access:
            st.success("✅ Access granted")
        else:
            with st.form("sidebar_owner_unlock"):
                pwd_sidebar = st.text_input("Password", type="password", placeholder="Enter owner password")
                if st.form_submit_button("🔓 Unlock", use_container_width=True):
                    if pwd_sidebar.strip() == OWNSPACE_PASSWORD.strip():
                        st.session_state.owner_space_access = True
                        st.session_state.current_page = "owner_space"
                        st.rerun()
                    else:
                        st.error("Invalid password")

    # Render the selected page
    page_functions = {
        "feed": render_feed,
        "friends_chat": render_friends_page,
        "satellite_map": render_map,
        "worldcup": render_worldcup,
        "profile": render_profile,
        "video_call": render_video_call,
        "owner_space": owner_space,
    }
    page_functions.get(st.session_state.current_page, render_feed)()

# ========== ENTRY ==========
if __name__ == "__main__":
    if st.session_state.logged_in:
        st.markdown(f"""
        <div class="home-title">
            <div style="overflow:hidden; width:100%;">
                <div class="marquee">
                    <span class="lakay-flag-text">New Haiti Facebook / Lakay Se Lakay</span>
                </div>
            </div>
            <p style="font-size:1.2rem; margin-top:0.2rem;">{t('home_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
