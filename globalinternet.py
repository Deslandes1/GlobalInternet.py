# ====== FULL app.py (Lakay se Lakay - Ultra-Fast with Call & Messaging) ======
# Lakay se Lakay - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes (Python Developer, Haiti)
# Version: 90.0.0 (Phone Call on Profile, Message Inbox, Missed Calls, Speed Optimized)
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
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password")

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
# ---- Audio-only call flag ----
if "call_audio_only" not in st.session_state:
    st.session_state.call_audio_only = False
# ---- Navigation page ----
if "current_page" not in st.session_state:
    st.session_state.current_page = "feed"
# ---- Feed search term ----
if "feed_search_term" not in st.session_state:
    st.session_state.feed_search_term = ""
# ---- Mobile optimization flags ----
if "_session_restored" not in st.session_state:
    st.session_state._session_restored = False
if "_last_token_refresh" not in st.session_state:
    st.session_state._last_token_refresh = 0
if "_cookie_read" not in st.session_state:
    st.session_state._cookie_read = False
# ---- Cache timestamp for posts ----
if "_posts_cache_time" not in st.session_state:
    st.session_state._posts_cache_time = 0

# ---- NAVIGATION FROM QUERY PARAMS ----
if "page" in st.query_params:
    page_param = st.query_params["page"]
    valid_pages = ["feed", "friends_chat", "satellite_map", "worldcup", "profile", "video_call", "owner_space"]
    if page_param in valid_pages:
        st.session_state.current_page = page_param
    del st.query_params["page"]

# ====== LANGUAGE DICTIONARY (FULL TRANSLATIONS) ======
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
        "search_groq": "🔍 Search Books & Videos",
        "groq_search_placeholder": "What are you looking for? (books, tutorials, etc.)",
        "groq_results": "Results",
        "groq_open": "📖 Open",
        "groq_close": "✖ Close",
        "no_groq_results": "No recommendations found.",
        "groq_api_key_missing": "⚠️ Groq API key not set. Add GROQ_API_KEY to your secrets.",
        "youtube_not_supported": "⚠️ YouTube links are not supported in this search. Please search for books or other videos.",
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
        "private_profile": "🔒 This profile is private. Send a friend request to see their posts and albums.",
        "search_posts": "🔍 Search posts...",
        "refresh_feed": "🔄 Refresh Feed",
        "security_badge": "🛡️ Security Badge",
        "security_caption": "🔒 End-to-end encrypted connection",
        "unibank_usd_account": "UNIBANK USD Account Number",
        "unibank_htg_account": "UNIBANK HTG Account Number",
        "cin_number": "CIN Card Number",
        # New keys for call and messaging
        "missed_call": "Missed call from {name}",
        "call_back": "Call Back",
        "incoming_call": "📞 Incoming call from {name}",
        "accept_call": "Accept",
        "reject_call": "Reject",
        "call_ended": "Call ended",
        "call_rejected": "Call rejected",
        "call_missed": "Missed call",
        "conversations": "Conversations",
        "no_conversations": "No conversations yet.",
        "chat_with": "Chat with {name}",
        "emoji_picker": "😊",
        "attach_file": "📎 Attach file",
        "send_message_btn": "Send",
    },
    "fr": {
        "login_title": "Connexion",
        "signup_title": "S'inscrire",
        "forgot_password": "Mot de passe oublié",
        "email": "E-mail",
        "password": "Mot de passe",
        "full_name": "Nom complet",
        "remember_me": "Se souvenir de moi",
        "login_button": "🚀 Se connecter",
        "signup_button": "📝 S'inscrire",
        "send_reset_link": "Envoyer le lien de réinitialisation",
        "feed": "📡 Fil d'actualité",
        "friends_chat": "👥 Amis et discussion",
        "satellite_map": "🛰️ Carte satellite",
        "worldcup": "⚽ Coupe du monde en direct",
        "profile": "👤 Profil",
        "owner_space": "🕊️ Espace propriétaire",
        "logout": "🚪 Déconnexion",
        "system_health": "🛡️ Santé du système",
        "signal": "📡 Signal",
        "latency": "⏱️ Latence",
        "quality": "📊 Qualité",
        "uptime": "⏰ Disponibilité",
        "encrypted": "🔒 Statut : CHIFFRÉ",
        "compensation": "💰 Compensation",
        "logged_in_as": "👤 Connecté en tant que",
        "go_live": "Lancer un live (streaming réel)",
        "external_platform": "Plateforme externe (YouTube/Facebook/Twitch)",
        "in_app_camera": "Caméra intégrée",
        "select_platform": "Choisir une plateforme",
        "live_title": "Titre du live",
        "create_live_session": "Créer une session live",
        "you_are_live": "🔴 Vous êtes en direct !",
        "end_live_session": "Terminer le live",
        "set_stream_url": "📹 Définir l'URL du stream",
        "paste_url": "Collez votre URL de stream",
        "update_url": "Mettre à jour l'URL",
        "shareable_link": "Lien partageable",
        "live_chat_gifts": "Chat en direct et cadeaux",
        "send_gift": "🎁 Envoyer un cadeau",
        "add_moncash": "Ajoutez votre numéro MonCash dans votre profil pour envoyer des cadeaux.",
        "add_natcash": "Ajoutez votre numéro NATCASH pour recevoir des cadeaux.",
        "total_gifts": "Total des cadeaux reçus",
        "gifts_sent_to": "Les cadeaux seront envoyés sur votre MonCash",
        "gifts_sent_to_natcash": "NATCASH",
        "write_comment": "Écrire un commentaire...",
        "send": "Envoyer",
        "back_to_feed": "Retour au fil",
        "create_post": "Créer une publication",
        "caption_placeholder": "Écrivez quelque chose... ou collez un lien vidéo (YouTube, Vimeo, etc.)",
        "add_media": "Ajouter des images ou vidéos (PNG, JPG, JPEG, GIF, MP4, MOV, AVI)",
        "visibility": "Visibilité",
        "public": "Public",
        "private": "Privé",
        "post": "🚀 Publier",
        "delete_post": "🗑️ Supprimer",
        "comments": "Commentaires",
        "reply": "💬 Répondre",
        "post_reply": "Publier la réponse",
        "your_reply": "Votre réponse",
        "clear_error": "Effacer l'erreur",
        "join_live": "Rejoindre le live",
        "watch_stream": "▶ REGARDER LE STREAM",
        "start_broadcast": "▶ DÉMARRER LA DIFFUSION",
        "stop_broadcast": "■ ARRÊTER LA DIFFUSION",
        "you_are_broadcaster": "✅ Vous êtes le diffuseur. Utilisez les commandes ci‑dessous pour commencer.",
        "you_are_viewer": "👀 Vous êtes un spectateur. Cliquez sur 'Regarder le stream' pour voir la vidéo.",
        "choose_background": "🎨 Filtres d'arrière‑plan",
        "bg_option": "BG",
        "upload_background": "Ou téléchargez votre propre image",
        "background_set": "Arrière‑plan défini !",
        "ready_to_start": "Prêt à démarrer. Cliquez sur le bouton ci‑dessus.",
        "camera_access": "📷 Demande d'accès à la caméra...",
        "camera_granted": "✅ Accès à la caméra accordé. Connexion au serveur peer...",
        "broadcasting": "✅ Diffusion en cours ! Votre ID peer",
        "peer_error": "❌ Erreur peer",
        "error": "❌ Erreur",
        "broadcast_ended": "Diffusion terminée",
        "initializing": "Initialisation...",
        "connected_requesting": "Connecté. Demande du stream au diffuseur...",
        "calling": "Appel en cours",
        "received_stream": "Stream distant reçu",
        "now_watching": "✅ Vous regardez maintenant le live",
        "call_error": "❌ Erreur d'appel",
        "call_ended": "Appel terminé",
        "disconnected": "Déconnecté. Veuillez rafraîchir.",
        "send_message": "Envoyer",
        "close_chat": "Fermer le chat",
        "active_call": "📞 Appel actif",
        "room_id": "ID de la salle",
        "share_room": "Partagez cet ID avec la personne que vous voulez appeler.",
        "start_call": "Démarrer un appel",
        "end_call": "Raccrocher",
        "find_users": "🔍 Trouver des utilisateurs",
        "search_by_name": "Rechercher par nom",
        "add_friend": "➕ Ajouter en ami",
        "view_profile": "👤 Voir le profil",
        "friend_requests": "📨 Demandes d'amis reçues",
        "accept": "✅ Accepter",
        "reject": "❌ Rejeter",
        "your_friends": "👥 Vos amis",
        "no_friends": "Vous n'avez pas encore d'amis",
        "chat": "💬 Chat",
        "call": "📞 Appeler",
        "profile_btn": "👤 Profil",
        "edit_profile": "Modifier le profil",
        "save_changes": "💾 Enregistrer",
        "change_picture": "📸 Changer la photo",
        "bio": "Bio",
        "location": "Localisation",
        "moncash_phone": "Numéro MonCash (pour recevoir des cadeaux)",
        "natcash_phone": "Numéro NATCASH (pour recevoir des cadeaux)",
        "posts_count": "Publications",
        "connections": "Connexions",
        "verified": "Vérifié",
        "member_since": "Membre depuis",
        "dashboard": "💰 Tableau de bord",
        "new_users": "📈 Nouveaux utilisateurs",
        "post_moderation": "🛡️ Modération des publications",
        "client_payments": "📥 Paiements clients",
        "gift_management": "🎁 Gestion des cadeaux",
        "owner_dashboard": "🔐 Tableau de bord du propriétaire",
        "balance": "Solde MonCash Business",
        "transfer_funds": "💰 Transférer des fonds vers votre compte",
        "amount_transfer": "Montant à transférer ($)",
        "transfer": "🚀 Transférer vers mon MonCash",
        "no_gifts": "Aucun cadeau pour l'instant.",
        "payout_summary": "Résumé des paiements",
        "total_gifts_htg": "Total des cadeaux (HTG)",
        "mark_paid": "Tout marquer comme payé (simulation)",
        "contact_support": "📬 Contactez le support / Paiements importants",
        "logout_owner": "Se déconnecter de l'espace propriétaire",
        "setup_instructions": "ℹ️ Instructions de configuration (si les téléchargements échouent)",
        "storage_error": "Erreur de permission de stockage : configurez les politiques RLS pour le bucket 'avatars'.",
        "listen_explanation": "🔊 Écouter l'explication de l'application",
        "voice_lang": "🌐 Langue vocale",
        "app_explanation": "Cette application a été construite par Gesner Deslandes, Ingénieur en Chef chez GlobalInternet.py. Tél : (509) 4738-5663. Email : deslandes78@gmail.com. Contactez Gesner si vous souhaitez créer un site web ou un logiciel. Cette application est une plateforme sociale haïtienne qui vous permet de vous connecter avec vos amis, partager des publications, faire des lives, envoyer des cadeaux et chatter en temps réel. Elle utilise Supabase pour les données, supporte le live streaming avec des filtres d'arrière‑plan, et inclut une carte satellite pour le plaisir. Elle est conçue pour être un espace moderne, sécurisé et amusant pour les utilisateurs haïtiens. Toutes les fonctionnalités sont construites avec Python et Streamlit. De plus, lorsqu'il y a un match de la Coupe du Monde, vous pouvez le regarder en direct sur la plateforme !",
        "network_error": "⚠️ Impossible de se connecter au serveur d'authentification. Vérifiez votre connexion Internet et réessayez. Si le problème persiste, contactez le support.",
        "debug_hint": "Si vous êtes administrateur, activez 'Afficher les infos de débogage' ci‑dessous pour voir l'erreur brute.",
        "show_debug": "Afficher les infos de débogage",
        "home_title": "🏠 Lakay se Lakay",
        "home_haiti": "HAÏTI",
        "home_subtitle": "Votre plateforme sociale haïtienne",
        "call_permission_hint": "📌 Assurez‑vous que les deux participants accordent l'accès à la caméra et au microphone lorsque le navigateur le demande. Si vous ne vous voyez pas, rafraîchissez la page et réessayez.",
        "join_instructions": "📌 Après avoir rejoint la salle, cliquez sur le bouton **'Rejoindre'** dans la fenêtre vidéo et autorisez l'accès à la caméra/micro. Si vous ne voyez toujours pas l'autre personne, demandez‑lui de vérifier ses paramètres de caméra.",
        "reload_call": "🔄 Rafraîchir l'appel",
        "request_to_join": "📨 Demande de participation",
        "request_pending": "⏳ Demande en attente... en attente d'approbation du diffuseur.",
        "broadcaster_controls": "🎛️ Commandes du diffuseur",
        "join_live": "🔴 Rejoindre le live",
        "user_management": "👥 Gestion des utilisateurs",
        "ban_user": "🚫 Bannir",
        "unban_user": "✅ Débannir",
        "ban_reason": "Raison du bannissement",
        "banned": "Banni",
        "active": "Actif",
        "my_wall": "📝 Mon mur",
        "my_live_sessions": "📺 Mes sessions live",
        "live_status_live": "🔴 EN DIRECT",
        "live_status_ended": "Terminé",
        "video_call": "📞 Appel vidéo (démo Jitsi)",
        "demo_note": "ℹ️ Ceci est une demo utilisant Jitsi Meet – gratuit et open‑source. Vous pouvez démarrer un appel et partager le lien de la salle avec n'importe qui.",
        "copy_link": "📋 Copier le lien de la salle",
        "room_link_copied": "✅ Lien de la salle copié dans le presse‑papiers !",
        "start_video_call": "Démarrer un appel vidéo",
        "your_personal_room": "Votre salle personnelle",
        "join_room": "Rejoindre la salle",
        "search_groq": "🔍 Rechercher des livres & vidéos",
        "groq_search_placeholder": "Que recherchez‑vous ? (livres, tutoriels, etc.)",
        "groq_results": "Résultats",
        "groq_open": "📖 Ouvrir",
        "groq_close": "✖ Fermer",
        "no_groq_results": "Aucune recommandation trouvée.",
        "groq_api_key_missing": "⚠️ Clé API Groq manquante. Ajoutez GROQ_API_KEY à vos secrets.",
        "youtube_not_supported": "⚠️ Les liens YouTube ne sont pas pris en charge dans cette recherche. Recherchez des livres ou autres vidéos.",
        "albums": "📸 Albums photo",
        "create_album": "Créer un album",
        "album_title": "Titre de l'album",
        "album_description": "Description",
        "album_visibility": "Visibilité",
        "album_public": "Public",
        "album_private": "Privé",
        "upload_photos": "Télécharger des photos",
        "no_albums": "Aucun album.",
        "view_album": "Voir l'album",
        "delete_album": "Supprimer l'album",
        "album_created": "Album créé avec succès !",
        "photos_uploaded": "Photos téléchargées avec succès !",
        "album_deleted": "Album supprimé.",
        "cover_photo": "Photo de couverture",
        "owner_albums": "Tous les albums (vue propriétaire)",
        "paste_video_link_hint": "💡 Pour les liens YouTube, Vimeo ou autres, collez simplement l'URL dans la légende ci‑dessus. Le téléchargeur de fichiers est pour les fichiers vidéo/image de votre appareil.",
        "open_in_new_tab": "Ouvrir dans un nouvel onglet",
        "profile_visibility": "Visibilité du profil",
        "whatsapp_phone": "Numéro WhatsApp (avec indicatif, ex. 50947385663)",
        "call_unavailable": "L'utilisateur n'est pas disponible ou hors ligne. Veuillez réessayer plus tard.",
        "calling": "📞 Appel en cours... Sonnerie...",
        "ringing": "🔔 Sonnerie... en attente de réponse.",
        "email_user": "📧 E-mail",
        "whatsapp": "💬 WhatsApp",
        "call_now": "📞 Appeler maintenant",
        "private_profile": "🔒 Ce profil est privé. Envoyez une demande d'ami pour voir ses publications et albums.",
        "search_posts": "🔍 Rechercher dans les publications...",
        "refresh_feed": "🔄 Rafraîchir le fil",
        "security_badge": "🛡️ Badge de sécurité",
        "security_caption": "🔒 Connexion chiffrée de bout en bout",
        "unibank_usd_account": "Numéro de compte UNIBANK USD",
        "unibank_htg_account": "Numéro de compte UNIBANK HTG",
        "cin_number": "Numéro de carte CIN",
        # New keys
        "missed_call": "Appel manqué de {name}",
        "call_back": "Rappeler",
        "incoming_call": "📞 Appel entrant de {name}",
        "accept_call": "Accepter",
        "reject_call": "Refuser",
        "call_ended": "Appel terminé",
        "call_rejected": "Appel refusé",
        "call_missed": "Appel manqué",
        "conversations": "Conversations",
        "no_conversations": "Aucune conversation.",
        "chat_with": "Discuter avec {name}",
        "emoji_picker": "😊",
        "attach_file": "📎 Joindre un fichier",
        "send_message_btn": "Envoyer",
    },
    "es": {
        "login_title": "Iniciar sesión",
        "signup_title": "Registrarse",
        "forgot_password": "Olvidé mi contraseña",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "full_name": "Nombre completo",
        "remember_me": "Recordarme",
        "login_button": "🚀 Iniciar sesión",
        "signup_button": "📝 Registrarse",
        "send_reset_link": "Enviar enlace de reinicio",
        "feed": "📡 Feed",
        "friends_chat": "👥 Amigos y chat",
        "satellite_map": "🛰️ Mapa satelital",
        "worldcup": "⚽ Copa del Mundo en vivo",
        "profile": "👤 Perfil",
        "owner_space": "🕊️ Espacio del propietario",
        "logout": "🚪 Cerrar sesión",
        "system_health": "🛡️ Salud del sistema",
        "signal": "📡 Señal",
        "latency": "⏱️ Latencia",
        "quality": "📊 Calidad",
        "uptime": "⏰ Tiempo activo",
        "encrypted": "🔒 Estado: CIFRADO",
        "compensation": "💰 Compensación",
        "logged_in_as": "👤 Conectado como",
        "go_live": "Ir en vivo (transmisión real)",
        "external_platform": "Plataforma externa (YouTube/Facebook/Twitch)",
        "in_app_camera": "Cámara integrada",
        "select_platform": "Seleccionar plataforma",
        "live_title": "Título del live",
        "create_live_session": "Crear sesión en vivo",
        "you_are_live": "🔴 ¡Estás en vivo!",
        "end_live_session": "Finalizar transmisión",
        "set_stream_url": "📹 Configurar URL de transmisión",
        "paste_url": "Pega tu URL de transmisión",
        "update_url": "Actualizar URL",
        "shareable_link": "Enlace compartible",
        "live_chat_gifts": "Chat en vivo y regalos",
        "send_gift": "🎁 Enviar un regalo",
        "add_moncash": "Agrega tu número de MonCash en tu perfil para enviar regalos.",
        "add_natcash": "Agrega tu número de NATCASH para recibir regalos.",
        "total_gifts": "Total de regalos recibidos",
        "gifts_sent_to": "Los regalos se enviarán a tu MonCash",
        "gifts_sent_to_natcash": "NATCASH",
        "write_comment": "Escribe un comentario...",
        "send": "Enviar",
        "back_to_feed": "Volver al feed",
        "create_post": "Crear una publicación",
        "caption_placeholder": "Escribe algo... o pega un enlace de video (YouTube, Vimeo, etc.)",
        "add_media": "Agregar imágenes o videos (PNG, JPG, JPEG, GIF, MP4, MOV, AVI)",
        "visibility": "Visibilidad",
        "public": "Público",
        "private": "Privado",
        "post": "🚀 Publicar",
        "delete_post": "🗑️ Eliminar",
        "comments": "Comentarios",
        "reply": "💬 Responder",
        "post_reply": "Publicar respuesta",
        "your_reply": "Tu respuesta",
        "clear_error": "Borrar error",
        "join_live": "Unirse al live",
        "watch_stream": "▶ VER TRANSMISIÓN",
        "start_broadcast": "▶ INICIAR TRANSMISIÓN",
        "stop_broadcast": "■ DETENER TRANSMISIÓN",
        "you_are_broadcaster": "✅ Eres el transmisor. Usa los controles a continuación para comenzar.",
        "you_are_viewer": "👀 Eres un espectador. Haz clic en 'Ver transmisión' para ver el video.",
        "choose_background": "🎨 Filtros de fondo",
        "bg_option": "BG",
        "upload_background": "O sube tu propia imagen",
        "background_set": "¡Fondo establecido!",
        "ready_to_start": "Listo para comenzar. Haz clic en el botón de arriba.",
        "camera_access": "📷 Solicitando acceso a la cámara...",
        "camera_granted": "✅ Acceso a la cámara concedido. Conectando al servidor peer...",
        "broadcasting": "✅ Transmitiendo en vivo! Tu ID peer",
        "peer_error": "❌ Error de peer",
        "error": "❌ Error",
        "broadcast_ended": "Transmisión finalizada",
        "initializing": "Inicializando...",
        "connected_requesting": "Conectado. Solicitando transmisión al transmisor...",
        "calling": "Llamando",
        "received_stream": "Transmisión remota recibida",
        "now_watching": "✅ Ahora viendo transmisión en vivo",
        "call_error": "❌ Error de llamada",
        "call_ended": "Llamada finalizada",
        "disconnected": "Desconectado. Por favor, actualiza.",
        "send_message": "Enviar",
        "close_chat": "Cerrar chat",
        "active_call": "📞 Llamada activa",
        "room_id": "ID de sala",
        "share_room": "Comparte este ID con la persona a la que quieres llamar.",
        "start_call": "Iniciar una llamada",
        "end_call": "Terminar llamada",
        "find_users": "🔍 Encontrar usuarios",
        "search_by_name": "Buscar por nombre",
        "add_friend": "➕ Agregar amigo",
        "view_profile": "👤 Ver perfil",
        "friend_requests": "📨 Solicitudes de amistad recibidas",
        "accept": "✅ Aceptar",
        "reject": "❌ Rechazar",
        "your_friends": "👥 Tus amigos",
        "no_friends": "Aún no tienes amigos",
        "chat": "💬 Chatear",
        "call": "📞 Llamar",
        "profile_btn": "👤 Perfil",
        "edit_profile": "Editar perfil",
        "save_changes": "💾 Guardar cambios",
        "change_picture": "📸 Cambiar foto",
        "bio": "Biografía",
        "location": "Ubicación",
        "moncash_phone": "Número de MonCash (para recibir regalos)",
        "natcash_phone": "Número de NATCASH (para recibir regalos)",
        "posts_count": "Publicaciones",
        "connections": "Conexiones",
        "verified": "Verificado",
        "member_since": "Miembro desde",
        "dashboard": "💰 Panel de control",
        "new_users": "📈 Nuevos usuarios",
        "post_moderation": "🛡️ Moderación de publicaciones",
        "client_payments": "📥 Pagos de clientes",
        "gift_management": "🎁 Gestión de regalos",
        "owner_dashboard": "🔐 Panel del propietario",
        "balance": "Saldo de MonCash Business",
        "transfer_funds": "💰 Transferir fondos a tu cuenta",
        "amount_transfer": "Monto a transferir ($)",
        "transfer": "🚀 Transferir a mi MonCash",
        "no_gifts": "Aún no hay regalos.",
        "payout_summary": "Resumen de pagos",
        "total_gifts_htg": "Total de regalos (HTG)",
        "mark_paid": "Marcar todo como pagado (simulación)",
        "contact_support": "📬 Contactar para soporte / pagos grandes",
        "logout_owner": "Cerrar sesión del espacio del propietario",
        "setup_instructions": "ℹ️ Instrucciones de configuración (si las cargas fallan)",
        "storage_error": "Error de permiso de almacenamiento: configura las políticas RLS para el bucket 'avatars'.",
        "listen_explanation": "🔊 Escuchar explicación de la aplicación",
        "voice_lang": "🌐 Idioma de voz",
        "app_explanation": "Esta aplicación fue construida por Gesner Deslandes, Ingeniero Jefe en GlobalInternet.py. Teléfono: (509) 4738-5663. Correo: deslandes78@gmail.com. Ponte en contacto con Gesner si quieres construir cualquier sitio web o software. Esta aplicación es una plataforma de redes sociales haitiana que te permite conectar con amigos, compartir publicaciones, hacer transmisiones en vivo, enviar regalos y chatear en tiempo real. Utiliza Supabase para los datos, soporta transmisiones en vivo con filtros de fondo e incluye un mapa satelital por diversión. Está diseñada para ser un espacio moderno, seguro y divertido para que los usuarios haitianos interactúen en línea. Todas las características están construidas con Python y Streamlit. Además, cuando hay un partido de la Copa del Mundo, puedes verlo en vivo aquí mismo en la plataforma.",
        "network_error": "⚠️ No se puede conectar al servidor de autenticación. Verifica tu conexión a Internet e inténtalo de nuevo. Si el problema persiste, contacta al soporte.",
        "debug_hint": "Si eres administrador, activa 'Mostrar información de depuración' a continuación para ver el error crudo.",
        "show_debug": "Mostrar información de depuración",
        "home_title": "🏠 Lakay se Lakay",
        "home_haiti": "HAITÍ",
        "home_subtitle": "Tu plataforma de redes sociales haitiana",
        "call_permission_hint": "📌 Asegúrate de que ambos participantes concedan acceso a la cámara y al micrófono cuando el navegador lo solicite. Si no se ven, actualiza la página y vuelve a intentarlo.",
        "join_instructions": "📌 Después de unirte a la sala, haz clic en el botón **'Unirse'** en la ventana de video y permite el acceso a la cámara/micrófono. Si aún no ves a la otra persona, pídele que revise su configuración de cámara.",
        "reload_call": "🔄 Recargar llamada",
        "request_to_join": "📨 Solicitar unirse",
        "request_pending": "⏳ Solicitud pendiente... esperando aprobación del transmisor.",
        "broadcaster_controls": "🎛️ Controles del transmisor",
        "join_live": "🔴 Unirse al live",
        "user_management": "👥 Gestión de usuarios",
        "ban_user": "🚫 Banear usuario",
        "unban_user": "✅ Desbanear usuario",
        "ban_reason": "Razón del baneo",
        "banned": "Baneado",
        "active": "Activo",
        "my_wall": "📝 Mi muro",
        "my_live_sessions": "📺 Mis sesiones en vivo",
        "live_status_live": "🔴 EN VIVO",
        "live_status_ended": "Finalizado",
        "video_call": "📞 Videollamada (demo Jitsi)",
        "demo_note": "ℹ️ Esta es una demo usando Jitsi Meet – gratuito y de código abierto. Puedes iniciar una llamada y compartir el enlace de la sala con cualquiera.",
        "copy_link": "📋 Copiar enlace de la sala",
        "room_link_copied": "✅ ¡Enlace de la sala copiado al portapapeles!",
        "start_video_call": "Iniciar una videollamada",
        "your_personal_room": "Tu sala personal",
        "join_room": "Unirse a la sala",
        "search_groq": "🔍 Buscar libros y videos",
        "groq_search_placeholder": "¿Qué estás buscando? (libros, tutoriales, etc.)",
        "groq_results": "Resultados",
        "groq_open": "📖 Abrir",
        "groq_close": "✖ Cerrar",
        "no_groq_results": "No se encontraron recomendaciones.",
        "groq_api_key_missing": "⚠️ Clave API de Groq no configurada. Agrega GROQ_API_KEY a tus secretos.",
        "youtube_not_supported": "⚠️ Los enlaces de YouTube no son compatibles en esta búsqueda. Busca libros u otros videos.",
        "albums": "📸 Álbumes de fotos",
        "create_album": "Crear nuevo álbum",
        "album_title": "Título del álbum",
        "album_description": "Descripción",
        "album_visibility": "Visibilidad",
        "album_public": "Público",
        "album_private": "Privado",
        "upload_photos": "Subir fotos",
        "no_albums": "Aún no hay álbumes.",
        "view_album": "Ver álbum",
        "delete_album": "Eliminar álbum",
        "album_created": "¡Álbum creado exitosamente!",
        "photos_uploaded": "¡Fotos subidas exitosamente!",
        "album_deleted": "Álbum eliminado.",
        "cover_photo": "Foto de portada",
        "owner_albums": "Todos los álbumes (vista de propietario)",
        "paste_video_link_hint": "💡 Para enlaces de YouTube, Vimeo u otros, simplemente pega la URL en el texto de arriba. El cargador de archivos es para subir archivos de video/imagen desde tu dispositivo.",
        "open_in_new_tab": "Abrir en una nueva pestaña",
        "profile_visibility": "Visibilidad del perfil",
        "whatsapp_phone": "Número de WhatsApp (con código de país, ej. 50947385663)",
        "call_unavailable": "El usuario no está disponible o fuera de línea. Vuelve a intentarlo más tarde.",
        "calling": "📞 Llamando... Sonando...",
        "ringing": "🔔 Sonando... esperando que el usuario responda.",
        "email_user": "📧 Correo",
        "whatsapp": "💬 WhatsApp",
        "call_now": "📞 Llamar ahora",
        "private_profile": "🔒 Este perfil es privado. Envía una solicitud de amistad para ver sus publicaciones y álbumes.",
        "search_posts": "🔍 Buscar publicaciones...",
        "refresh_feed": "🔄 Actualizar feed",
        "security_badge": "🛡️ Insignia de seguridad",
        "security_caption": "🔒 Conexión cifrada de extremo a extremo",
        "unibank_usd_account": "Número de cuenta UNIBANK USD",
        "unibank_htg_account": "Número de cuenta UNIBANK HTG",
        "cin_number": "Número de CIN",
        # New keys
        "missed_call": "Llamada perdida de {name}",
        "call_back": "Devolver llamada",
        "incoming_call": "📞 Llamada entrante de {name}",
        "accept_call": "Aceptar",
        "reject_call": "Rechazar",
        "call_ended": "Llamada finalizada",
        "call_rejected": "Llamada rechazada",
        "call_missed": "Llamada perdida",
        "conversations": "Conversaciones",
        "no_conversations": "No hay conversaciones.",
        "chat_with": "Chatear con {name}",
        "emoji_picker": "😊",
        "attach_file": "📎 Adjuntar archivo",
        "send_message_btn": "Enviar",
    },
    "ht": {
        "login_title": "Konekte",
        "signup_title": "Enskri",
        "forgot_password": "Modpas ou bliye",
        "email": "Imèl",
        "password": "Modpas",
        "full_name": "Non konplè",
        "remember_me": "Sonje mwen",
        "login_button": "🚀 Konekte",
        "signup_button": "📝 Enskri",
        "send_reset_link": "Voye lyen reyinisyalizasyon",
        "feed": "📡 Feed",
        "friends_chat": "👥 Zanmi ak Chat",
        "satellite_map": "🛰️ Kat satelit",
        "worldcup": "⚽ Koup Mondyal an dirèk",
        "profile": "👤 Pwofil",
        "owner_space": "🕊️ Espas Pwopriyetè",
        "logout": "🚪 Dekonekte",
        "system_health": "🛡️ Sante Sistèm",
        "signal": "📡 Siyal",
        "latency": "⏱️ Lantans",
        "quality": "📊 Kalite",
        "uptime": "⏰ Tan moute",
        "encrypted": "🔒 Estati: CHIFRE",
        "compensation": "💰 Konpansasyon",
        "logged_in_as": "👤 Konekte kòm",
        "go_live": "Ale an dirèk (streaming reyèl)",
        "external_platform": "Platfòm ekstèn (YouTube/Facebook/Twitch)",
        "in_app_camera": "Kamera entegre",
        "select_platform": "Chwazi platfòm",
        "live_title": "Tit dirèk",
        "create_live_session": "Kreye sesyon an dirèk",
        "you_are_live": "🔴 Ou an dirèk!",
        "end_live_session": "Fini sesyon an dirèk",
        "set_stream_url": "📹 Mete URL stream",
        "paste_url": "Kole URL stream ou a",
        "update_url": "Mete ajou URL",
        "shareable_link": "Lyen patajab",
        "live_chat_gifts": "Chat an dirèk ak kado",
        "send_gift": "🎁 Voye yon kado",
        "add_moncash": "Ajoute nimewo MonCash ou nan pwofil ou pou voye kado.",
        "add_natcash": "Ajoute nimewo NATCASH ou pou resevwa kado.",
        "total_gifts": "Total kado resevwa",
        "gifts_sent_to": "Kado yo pral voye sou MonCash ou",
        "gifts_sent_to_natcash": "NATCASH",
        "write_comment": "Ekri yon kòmantè...",
        "send": "Voye",
        "back_to_feed": "Retounen nan feed",
        "create_post": "Kreye yon pòs",
        "caption_placeholder": "Ekri yon bagay... oswa kole yon lyen videyo (YouTube, Vimeo, elatriye)",
        "add_media": "Ajoute imaj oswa videyo (PNG, JPG, JPEG, GIF, MP4, MOV, AVI)",
        "visibility": "Vizibilite",
        "public": "Piblik",
        "private": "Prive",
        "post": "🚀 Pibliye",
        "delete_post": "🗑️ Efase",
        "comments": "Kòmantè",
        "reply": "💬 Reponn",
        "post_reply": "Pibliye repons",
        "your_reply": "Repons ou",
        "clear_error": "Efase erè",
        "join_live": "Antre nan dirèk",
        "watch_stream": "▶ GADE STREAM",
        "start_broadcast": "▶ KOUMANSE DIFIZYON",
        "stop_broadcast": "■ ARETE DIFIZYON",
        "you_are_broadcaster": "✅ Se ou ki difizè. Sèvi ak kontwòl anba a pou kòmanse.",
        "you_are_viewer": "👀 Ou se yon spektatè. Klike sou 'Gade Stream' pou wè videyo a.",
        "choose_background": "🎨 Filtre background",
        "bg_option": "BG",
        "upload_background": "Oswa telechaje pwòp imaj ou",
        "background_set": "Background mete!",
        "ready_to_start": "Pare pou kòmanse. Klike sou bouton anwo a.",
        "camera_access": "📷 Mande aksè kamera...",
        "camera_granted": "✅ Aksè kamera akòde. Konekte ak sèvè peer...",
        "broadcasting": "✅ Difizyon an dirèk! ID peer ou",
        "peer_error": "❌ Erè peer",
        "error": "❌ Erè",
        "broadcast_ended": "Difizyon fini",
        "initializing": "Inisyalizasyon...",
        "connected_requesting": "Konekte. Mande stream nan men difizè...",
        "calling": "Ap rele",
        "received_stream": "Resevwa stream a distans",
        "now_watching": "✅ Kounye a w ap gade dirèk",
        "call_error": "❌ Erè apèl",
        "call_ended": "Apèl fini",
        "disconnected": "Dekonekte. Tanpri rafrechi.",
        "send_message": "Voye",
        "close_chat": "Fèmen chat",
        "active_call": "📞 Apèl aktif",
        "room_id": "ID sal",
        "share_room": "Pataje ID sa a ak moun ou vle rele a.",
        "start_call": "Kòmanse yon apèl",
        "end_call": "Fini apèl",
        "find_users": "🔍 Jwenn itilizatè",
        "search_by_name": "Chèche pa non",
        "add_friend": "➕ Ajoute zanmi",
        "view_profile": "👤 Gade pwofil",
        "friend_requests": "📨 Demann zanmi resevwa",
        "accept": "✅ Aksepte",
        "reject": "❌ Rejte",
        "your_friends": "👥 Zanmi ou yo",
        "no_friends": "Ou poko gen zanmi",
        "chat": "💬 Chat",
        "call": "📞 Rele",
        "profile_btn": "👤 Pwofil",
        "edit_profile": "Modifye pwofil",
        "save_changes": "💾 Anrejistre chanjman",
        "change_picture": "📸 Chanje foto",
        "bio": "Biyografi",
        "location": "Lokalizasyon",
        "moncash_phone": "Nimewo MonCash (pou resevwa kado)",
        "natcash_phone": "Nimewo NATCASH (pou resevwa kado)",
        "posts_count": "Pòs",
        "connections": "Koneksyon",
        "verified": "Verifye",
        "member_since": "Manm depi",
        "dashboard": "💰 Tablo de bor",
        "new_users": "📈 Nouvo itilizatè",
        "post_moderation": "🛡️ Moderasyon pòs itilizatè",
        "client_payments": "📥 Peman kliyan",
        "gift_management": "🎁 Jesyon kado",
        "owner_dashboard": "🔐 Tablo de bor pwopriyetè",
        "balance": "MonCash Business Balance",
        "transfer_funds": "💰 Transfere lajan nan kont ou",
        "amount_transfer": "Montan pou transfere ($)",
        "transfer": "🚀 Transfere nan MonCash mwen",
        "no_gifts": "Pok pok gen kado.",
        "payout_summary": "Rezime peman",
        "total_gifts_htg": "Total kado (HTG)",
        "mark_paid": "Make tout kòm peye (similasyon)",
        "contact_support": "📬 Kontakte sipò / Gwo peman",
        "logout_owner": "Dekonekte nan espas pwopriyetè",
        "setup_instructions": "ℹ️ Enstriksyon konfigirasyon (si telechajman echwe)",
        "storage_error": "Erè pèmisyon depo: tanpri mete politik RLS pou bucket 'avatars'.",
        "listen_explanation": "🔊 Koute eksplikasyon aplikasyon an",
        "voice_lang": "🌐 Lang vwa",
        "app_explanation": "Aplikasyon sa a te kreye pa Gesner Deslandes, Enjenyè an Chèf nan GlobalInternet.py. Telefòn: (509) 4738-5663. Imèl: deslandes78@gmail.com. Kontakte Gesner si ou vle bati yon sitwèb oswa lojisyèl. Aplikasyon sa a se yon platfòm sosyal ayisyen ki pèmèt ou konekte ak zanmi, pataje pòs, fè dirèk, voye kado, epi chato an tan reyèl. Li sèvi ak Supabase pou done, sipòte dirèk ak filt background, epi li gen yon kat satelit pou plezi. Li fèt pou yon espas modèn, sekirize ak amizan pou itilizatè ayisyen yo. Tout karakteristik yo bati ak Python ak Streamlit. Anplis de sa, lè gen yon match Koup Mondyal, ou ka gade l an dirèk isit la sou platfòm nan!",
        "network_error": "⚠️ Pa ka konekte ak sèvè otantifikasyon an. Tanpri tcheke koneksyon entènèt ou epi eseye ankò. Si pwoblèm nan kontinye, kontakte sipò.",
        "debug_hint": "Si ou se administratè, aktive 'Montre enfòmasyon debogaj' anba a pou wè erè a.",
        "show_debug": "Montre enfòmasyon debogaj",
        "home_title": "🏠 Lakay se Lakay",
        "home_haiti": "AYITI",
        "home_subtitle": "Platfòm sosyal ayisyen ou",
        "call_permission_hint": "📌 Asire w ke tou de patisipan yo akòde aksè kamera ak mikwofòn lè navigatè a mande li. Si ou pa wè youn lòt, rafrechi paj la epi eseye ankò.",
        "join_instructions": "📌 Apre w fin antre nan sal la, klike sou bouton **'Antre'** nan fenèt videyo a epi pèmèt aksè kamera/mikwofòn. Si ou toujou pa wè lòt moun nan, mande l pou l tcheke paramèt kamera li.",
        "reload_call": "🔄 Relanse apèl",
        "request_to_join": "📨 Demann pou antre",
        "request_pending": "⏳ Demann annat... ap tann apwobasyon difizè.",
        "broadcaster_controls": "🎛️ Kontwòl difizè",
        "join_live": "🔴 Antre nan dirèk",
        "user_management": "👥 Jesyon itilizatè",
        "ban_user": "🚫 Bani itilizatè",
        "unban_user": "✅ Retire bani",
        "ban_reason": "Raison banisman",
        "banned": "Bani",
        "active": "Aktif",
        "my_wall": "📝 Mi mwen",
        "my_live_sessions": "📺 Sesi dirèk mwen",
        "live_status_live": "🔴 AN DIRÈK",
        "live_status_ended": "Fini",
        "video_call": "📞 Apèl videyo (Demo Jitsi)",
        "demo_note": "ℹ️ Sa a se yon demo ki itilize Jitsi Meet – gratis ak sous louvri. Ou ka kòmanse yon apèl epi pataje lyen sal la ak nenpòt moun.",
        "copy_link": "📋 Kopi lyen sal",
        "room_link_copied": "✅ Lyen sal la kopi nan clipboard!",
        "start_video_call": "Kòmanse yon apèl videyo",
        "your_personal_room": "Sal pèsonèl ou",
        "join_room": "Antre nan sal",
        "search_groq": "🔍 Chèche Liv & Videyo",
        "groq_search_placeholder": "Kisa w ap chèche? (liv, leson, elatriye)",
        "groq_results": "Rezilta",
        "groq_open": "📖 Louvri",
        "groq_close": "✖ Fèmen",
        "no_groq_results": "Pa gen rekòmandasyon jwenn.",
        "groq_api_key_missing": "⚠️ Kle API Groq pa mete. Ajoute GROQ_API_KEY nan secrets ou.",
        "youtube_not_supported": "⚠️ Lyen YouTube pa sipòte nan rechèch sa a. Tanpri chèche liv oswa lòt videyo.",
        "albums": "📸 Albòm foto",
        "create_album": "Kreye nouvo albòm",
        "album_title": "Tit albòm",
        "album_description": "Deskripsyon",
        "album_visibility": "Vizibilite",
        "album_public": "Piblik",
        "album_private": "Prive",
        "upload_photos": "Telechaje foto",
        "no_albums": "Pokoko gen albòm.",
        "view_album": "Gade albòm",
        "delete_album": "Efase albòm",
        "album_created": "Albòm kreye avèk siksè!",
        "photos_uploaded": "Foto telechaje avèk siksè!",
        "album_deleted": "Albòm efase.",
        "cover_photo": "Foto kouvèti",
        "owner_albums": "Tout albòm (gade pwopriyetè)",
        "paste_video_link_hint": "💡 Pou lyen YouTube, Vimeo, oswa lòt lyen videyo, kole URL nan tèks ki anwo a. Telechajè a se pou telechaje fichye videyo/imaj ki soti nan aparèy ou.",
        "open_in_new_tab": "Louvri nan nouvo onglè",
        "profile_visibility": "Vizibilite pwofil",
        "whatsapp_phone": "Nimewo WhatsApp (ak kòd peyi, egz. 50947385663)",
        "call_unavailable": "Itilizatè a pa disponib oswa dekonte. Tanpri eseye ankò pita.",
        "calling": "📞 Ap rele... Sonnen...",
        "ringing": "🔔 Sonnen... ap tann itilizatè a reponn.",
        "email_user": "📧 Imèl",
        "whatsapp": "💬 WhatsApp",
        "call_now": "📞 Rele kounye a",
        "private_profile": "🔒 Pwofil sa a prive. Voye yon demann zanmi pou wè pòs ak albòm li.",
        "search_posts": "🔍 Chèche pòs...",
        "refresh_feed": "🔄 Rafrechi feed",
        "security_badge": "🛡️ Badge sekirite",
        "security_caption": "🔒 Koneksyon chifre bout nan bout",
        "unibank_usd_account": "Nimewo kont UNIBANK USD",
        "unibank_htg_account": "Nimewo kont UNIBANK HTG",
        "cin_number": "Nimewo kat CIN",
        # New keys
        "missed_call": "Apèl manke de {name}",
        "call_back": "Rapèl",
        "incoming_call": "📞 Apèl antre de {name}",
        "accept_call": "Aksepte",
        "reject_call": "Refize",
        "call_ended": "Apèl fini",
        "call_rejected": "Apèl refize",
        "call_missed": "Apèl manke",
        "conversations": "Konvèsasyon",
        "no_conversations": "Pa gen konvèsasyon.",
        "chat_with": "Chat ak {name}",
        "emoji_picker": "😊",
        "attach_file": "📎 Atache yon fichye",
        "send_message_btn": "Voye",
    }
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
    param_name = f"cookie_{name}"
    if param_name in st.query_params:
        val = st.query_params[param_name]
        del st.query_params[param_name]
        return val
    return None

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

# --- Restore session (runs only once) ---
if not st.session_state._session_restored and supabase:
    st.session_state._session_restored = True
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
        except Exception as e:
            set_cookie("sb_refresh_token", "", -1)
            st.warning("Could not restore session. Please log in again.")
            st.session_state.last_error = str(e)

# --- Lazy token refresh (only if more than 1 hour has passed) ---
if st.session_state.logged_in and supabase and st.session_state.refresh_token:
    if time.time() - st.session_state._last_token_refresh > 3600:
        try:
            new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
            if new_session and new_session.user:
                st.session_state.user = new_session.user
                st.session_state.refresh_token = new_session.session.refresh_token
                st.session_state._last_token_refresh = time.time()
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
    const NUM_STARS = 150;
    function initStars() {
        stars.length = 0;
        for (let i = 0; i < NUM_STARS; i++) {
            stars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 1.5 + 0.5,
                twinkleSpeed: 0.02 + Math.random() * 0.04,
                phase: Math.random() * Math.PI * 2
            });
        }
    }
    initStars();
    let frameId = null;
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
        frameId = requestAnimationFrame(drawStars);
    }
    drawStars(0);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && frameId) {
            cancelAnimationFrame(frameId);
            frameId = null;
        } else if (!document.hidden && !frameId) {
            drawStars(0);
        }
    });
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
    .profile-avatar { border-radius: 50%; border: 3px solid #00209F; box-shadow: 0 4px 12px rgba(0,0,0,0.15); object-fit: cover; }
    .profile-avatar-large { width: 300px; height: 300px; border-radius: 50%; border: 4px solid #00209F; box-shadow: 0 8px 25px rgba(0,0,0,0.2); object-fit: cover; }
    @media (max-width: 768px) { .profile-avatar-large { width: 200px; height: 200px; } }
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
    .home-title { 
        text-align: center; 
        padding: 1.5rem; 
        background: linear-gradient(135deg, rgba(255,215,0,0.15) 0%, rgba(255,215,0,0.05) 100%);
        border-radius: 20px; 
        margin-bottom: 1.5rem; 
        backdrop-filter: blur(4px); 
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255,215,0,0.3);
    }
    .home-title .golden-stars {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 0;
    }
    .home-title .golden-stars span {
        position: absolute;
        display: inline-block;
        font-size: 2rem;
        color: gold;
        text-shadow: 0 0 20px #ffd700, 0 0 40px #ff8c00;
        animation: shimmer 3s ease-in-out infinite alternate;
    }
    .home-title .golden-stars span:nth-child(1) { top: 10%; left: 5%; animation-delay: 0s; font-size: 2.5rem; }
    .home-title .golden-stars span:nth-child(2) { top: 15%; right: 8%; animation-delay: 1.2s; font-size: 2rem; }
    .home-title .golden-stars span:nth-child(3) { bottom: 20%; left: 10%; animation-delay: 0.6s; font-size: 1.8rem; }
    .home-title .golden-stars span:nth-child(4) { bottom: 25%; right: 12%; animation-delay: 1.8s; font-size: 2.2rem; }
    .home-title .golden-stars span:nth-child(5) { top: 45%; left: 2%; animation-delay: 0.3s; font-size: 1.5rem; }
    .home-title .golden-stars span:nth-child(6) { top: 50%; right: 2%; animation-delay: 1.5s; font-size: 1.6rem; }
    .home-title .golden-stars span:nth-child(7) { bottom: 5%; left: 45%; animation-delay: 0.9s; font-size: 2rem; }
    .home-title .golden-stars span:nth-child(8) { top: 5%; left: 45%; animation-delay: 2.1s; font-size: 1.8rem; }
    @keyframes shimmer {
        0% { opacity: 0.2; transform: scale(0.8) rotate(0deg); }
        100% { opacity: 1; transform: scale(1.2) rotate(20deg); }
    }
    .home-title .marquee-container {
        position: relative;
        z-index: 1;
        overflow: hidden;
        width: 100%;
    }
    .home-title .marquee {
        white-space: nowrap;
        overflow: hidden;
        display: block;
        animation: scrollLeft 12s linear infinite;
        font-size: 2.5rem;
        font-weight: bold;
        padding: 0.2rem 0;
    }
    .home-title .marquee span {
        display: inline-block;
        padding-right: 2rem;
    }
    .home-title p {
        position: relative;
        z-index: 1;
        margin: 0.3rem 0 0;
        opacity: 0.85;
        color: #1e2a3a;
        font-size: 1.1rem;
    }
    @keyframes scrollLeft {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }
    .home-title .dove-symbol { font-size: 4rem; color: #ffffff; text-shadow: 0 0 20px rgba(0,0,0,0.1); display: block; margin: 0 auto; }
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
    /* ---- Big icon buttons for profile actions ---- */
    .big-icon-btn {
        display: inline-block;
        text-align: center;
        background: #f0f7ff;
        border: 2px solid #0080ff;
        border-radius: 50%;
        width: 70px;
        height: 70px;
        line-height: 70px;
        font-size: 2.2rem;
        transition: 0.2s;
        cursor: pointer;
        text-decoration: none;
        color: #0080ff;
        margin: 0 6px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    .big-icon-btn:hover {
        background: #0080ff;
        color: white;
        border-color: #0080ff;
        transform: scale(1.05);
        box-shadow: 0 8px 16px rgba(0,128,255,0.25);
    }
    .big-icon-btn i { display: block; line-height: 70px; }
    .big-icon-row {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
        margin: 15px 0;
    }
    .big-icon-btn .label {
        display: block;
        font-size: 0.65rem;
        line-height: 1.2;
        margin-top: -10px;
        color: inherit;
        font-weight: 600;
    }
    .big-icon-btn:hover .label {
        color: white;
    }
    /* ---- New: Top action bar for profile ---- */
    .profile-action-bar {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 10px 0 20px 0;
        flex-wrap: wrap;
    }
    .profile-action-bar .action-icon {
        font-size: 2rem;
        background: rgba(255,255,255,0.8);
        padding: 8px 16px;
        border-radius: 40px;
        border: 1px solid #0080ff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: 0.2s;
        cursor: pointer;
    }
    .profile-action-bar .action-icon:hover {
        background: #0080ff;
        color: white;
        transform: scale(1.05);
    }
    .profile-action-bar .action-icon .label {
        font-size: 0.7rem;
        display: block;
        margin-top: -5px;
        font-weight: 600;
    }
    .incoming-call-box {
        background: #ffdddd;
        border-left: 6px solid #ff4444;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .missed-call-box {
        background: #fff3cd;
        border-left: 6px solid #ffc107;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    /* ---- Chat conversation list ---- */
    .conversation-item {
        background: rgba(255,255,255,0.7);
        padding: 10px 15px;
        border-radius: 12px;
        margin: 5px 0;
        border: 1px solid rgba(0,168,255,0.2);
        cursor: pointer;
        transition: 0.2s;
    }
    .conversation-item:hover {
        background: rgba(255,255,255,0.9);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .conversation-item .unread-badge {
        background: #0080ff;
        color: white;
        border-radius: 50%;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: bold;
        margin-left: 10px;
    }
    .chat-media-preview {
        max-width: 100%;
        max-height: 300px;
        border-radius: 8px;
        margin: 5px 0;
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
                "profile_visibility": "public",
                "whatsapp_phone": None,
                "join_date": datetime.now().isoformat(),
                "is_banned": False,
                "ban_reason": None,
                "last_active": datetime.now().isoformat(),
                "unibank_usd_account": None,
                "unibank_htg_account": None,
                "cin_number": None
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
        if "42703" in str(e):
            base_fields = ["id", "full_name", "avatar_url", "is_banned", "ban_reason", "join_date", "last_active"]
            query = supabase.table("profiles").select(",".join(base_fields))
            for col, val in filters.items():
                query = query.eq(col, val)
            resp = query.execute()
            return resp.data if resp.data else []
        else:
            raise

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
        b64 = base64.b64encode(file_bytes).decode()
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

# ---- POST CRUD (optimised) ----
def delete_post(post_id):
    if supabase is None:
        return False
    try:
        supabase.table("posts").delete().eq("id", post_id).execute()
        st.cache_data.clear()
        st.session_state.posts = load_posts()
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

# ====== PROFESSIONAL AVATAR DISPLAY ======
def display_avatar_and_followers(avatar_url, user_id, size=50, profile=None, large=False):
    online = False
    if profile is not None:
        online = is_user_online(profile.get('last_active'))
    elif st.session_state.user and user_id == st.session_state.user.id:
        online = is_user_online(st.session_state.profile.get('last_active')) if st.session_state.profile else False
    dot_class = "online-indicator" if online else "offline-indicator"
    dot_html = f'<span class="{dot_class}"></span>'
    if large:
        if avatar_url:
            st.markdown(f'<img src="{avatar_url}" class="profile-avatar-large" />', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="profile-avatar-large" style="background:#ccc; display:flex; align-items:center; justify-content:center; font-size:100px; color:#555;">👤</div>', unsafe_allow_html=True)
        st.markdown(dot_html, unsafe_allow_html=True)
        st.caption("1KFollowers")
    else:
        if avatar_url:
            st.markdown(f'<img src="{avatar_url}" class="profile-avatar" style="width:{size}px; height:{size}px;" />', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="profile-avatar" style="width:{size}px; height:{size}px; background:#ccc; display:flex; align-items:center; justify-content:center; font-size:{size*0.6}px; color:#555;">👤</div>', unsafe_allow_html=True)
        st.markdown(dot_html, unsafe_allow_html=True)
        st.caption("1KFollowers")

# ====== USER POST COUNT ======
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

# ====== OPTIMISED POST LOADING ======
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

        if not posts:
            return []

        post_ids = [p["id"] for p in posts]

        # Fetch all reactions in one query
        reactions_resp = supabase.table("reactions").select("post_id, emoji").in_("post_id", post_ids).execute()
        reactions = reactions_resp.data or []
        reaction_counts = {}
        for r in reactions:
            pid = r["post_id"]
            emoji = r["emoji"]
            if pid not in reaction_counts:
                reaction_counts[pid] = {}
            reaction_counts[pid][emoji] = reaction_counts[pid].get(emoji, 0) + 1

        # Fetch comment counts in one query
        comments_resp = supabase.table("comments").select("post_id").in_("post_id", post_ids).execute()
        all_comments = comments_resp.data or []
        comment_counts = {}
        for c in all_comments:
            pid = c["post_id"]
            comment_counts[pid] = comment_counts.get(pid, 0) + 1

        # Fetch profiles for the users
        user_ids = {p["user_id"] for p in posts}
        profiles = {}
        if user_ids:
            profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, is_live, last_active").in_("id", list(user_ids)).execute()
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p

        # Assemble final post objects
        for post in posts:
            p = profiles.get(post["user_id"], {})
            post["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "is_live": p.get("is_live", False),
                "last_active": p.get("last_active"),
            }
            post["media_urls"] = post.get("media_urls", [])
            post["reactions"] = reaction_counts.get(post["id"], {})
            post["comment_count"] = comment_counts.get(post["id"], 0)

        return posts
    except Exception as e:
        st.session_state.last_error = f"Error loading posts: {e}"
        return []

def shuffle_feed_posts(posts):
    if not posts:
        return []
    from collections import defaultdict
    groups = defaultdict(list)
    for p in posts:
        groups[p['user_id']].append(p)
    for uid in groups:
        groups[uid].sort(key=lambda x: x['created_at'], reverse=True)
    result = []
    while any(groups.values()):
        active_users = [uid for uid, lst in groups.items() if lst]
        random.shuffle(active_users)
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

# --- POST CRUD with cache invalidation ---
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

# ---- Friends / Chat / Notifications (cached) ----
@st.cache_data(ttl=60)
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
        st.cache_data.clear()
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
        st.cache_data.clear()
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
            load_friend_data()
        st.cache_data.clear()
        return True, f"Request {new_status}"
    except Exception as e:
        return False, str(e)

# ====== FIXED load_friend_data with retry and caching ======
@st.cache_data(ttl=60)
def load_friend_data_cached(user_id):
    """Cached version of friend data loading."""
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            pending_resp = supabase.table("friend_requests") \
                .select("id, sender_id, receiver_id, status, created_at") \
                .eq("receiver_id", user_id) \
                .eq("status", "pending") \
                .execute()
            pending_raw = pending_resp.data or []

            sent_resp = supabase.table("friend_requests") \
                .select("id, sender_id, receiver_id, status, created_at") \
                .eq("sender_id", user_id) \
                .eq("status", "accepted") \
                .execute()
            received_resp = supabase.table("friend_requests") \
                .select("id, sender_id, receiver_id, status, created_at") \
                .eq("receiver_id", user_id) \
                .eq("status", "accepted") \
                .execute()

            accepted_raw = (sent_resp.data or []) + (received_resp.data or [])

            user_ids = set()
            for req in pending_raw:
                user_ids.add(req["sender_id"])
            for req in accepted_raw:
                user_ids.add(req["sender_id"])
                user_ids.add(req["receiver_id"])
            user_ids.discard(user_id)

            profiles = {}
            if user_ids:
                try:
                    fields = ["id", "full_name", "avatar_url", "last_active", "profile_visibility", "email", "whatsapp_phone"]
                    profiles_resp = supabase.table("profiles") \
                        .select(",".join(fields)) \
                        .in_("id", list(user_ids)) \
                        .execute()
                    for p in profiles_resp.data or []:
                        profiles[p["id"]] = p
                except Exception as e:
                    if "42703" in str(e):
                        fields = ["id", "full_name", "avatar_url", "last_active"]
                        profiles_resp = supabase.table("profiles") \
                            .select(",".join(fields)) \
                            .in_("id", list(user_ids)) \
                            .execute()
                        for p in profiles_resp.data or []:
                            p["profile_visibility"] = "public"
                            p["email"] = None
                            p["whatsapp_phone"] = None
                            profiles[p["id"]] = p
                    else:
                        raise

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

            return pending_requests, friends

        except Exception as e:
            st.session_state.last_error = f"Error loading friend data (attempt {attempt+1}/{max_retries}): {e}"
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                st.session_state.last_error = f"Failed to load friend data after {max_retries} attempts: {e}"
                return [], []

    return [], []

def load_friend_data():
    if supabase is None or not st.session_state.user:
        st.session_state.friend_requests = []
        st.session_state.friends = []
        return
    pending_requests, friends = load_friend_data_cached(st.session_state.user.id)
    st.session_state.friend_requests = pending_requests
    st.session_state.friends = friends

# ---- Search users (cached) ----
@st.cache_data(ttl=300)
def search_users_cached(query, current_user_id):
    if supabase is None:
        return []
    try:
        fields = ["id", "full_name", "avatar_url", "last_active", "profile_visibility", "email", "whatsapp_phone"]
        query_builder = supabase.table("profiles").select(",".join(fields)).neq("id", current_user_id).ilike("full_name", f"%{query}%").limit(50)
        resp = query_builder.execute()
        results = resp.data if resp.data else []
        for r in results:
            r.setdefault("profile_visibility", "public")
            r.setdefault("email", None)
            r.setdefault("whatsapp_phone", None)
        return results
    except Exception as e:
        if "42703" in str(e):
            fields = ["id", "full_name", "avatar_url", "last_active"]
            query_builder = supabase.table("profiles").select(",".join(fields)).neq("id", current_user_id).ilike("full_name", f"%{query}%").limit(50)
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

def search_users(query):
    if supabase is None or not st.session_state.user:
        return []
    return search_users_cached(query, st.session_state.user.id)

@st.cache_data(ttl=300)
def get_all_users_cached():
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

def get_all_users():
    return get_all_users_cached()

# ---- Messaging with conversation list ----
@st.cache_data(ttl=60)
def get_conversations(user_id):
    """Return a list of users the current user has exchanged messages with, with latest message and unread count."""
    if supabase is None:
        return []
    try:
        # Get all messages where user is sender or receiver
        sent = supabase.table("messages").select("receiver_id, created_at, content, read").eq("sender_id", user_id).execute()
        received = supabase.table("messages").select("sender_id, created_at, content, read").eq("receiver_id", user_id).execute()
        all_msgs = (sent.data or []) + (received.data or [])
        if not all_msgs:
            return []
        # Build a dict of other user -> latest message info
        conv_dict = {}
        for msg in all_msgs:
            other_id = msg["receiver_id"] if msg["receiver_id"] != user_id else msg["sender_id"]
            if other_id not in conv_dict or msg["created_at"] > conv_dict[other_id]["created_at"]:
                conv_dict[other_id] = {
                    "other_id": other_id,
                    "last_message": msg["content"],
                    "created_at": msg["created_at"],
                    "unread": (msg["receiver_id"] == user_id and not msg.get("read", True))
                }
            else:
                # Update unread count if it's a received message
                if msg["receiver_id"] == user_id and not msg.get("read", True):
                    conv_dict[other_id]["unread"] = True
        # Get profiles for these users
        other_ids = list(conv_dict.keys())
        profiles = {}
        if other_ids:
            fields = ["id", "full_name", "avatar_url", "last_active"]
            prof_resp = supabase.table("profiles").select(",".join(fields)).in_("id", other_ids).execute()
            for p in prof_resp.data or []:
                profiles[p["id"]] = p
        # Assemble final list
        conversations = []
        for other_id, data in conv_dict.items():
            p = profiles.get(other_id, {})
            conversations.append({
                "other_id": other_id,
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "last_active": p.get("last_active"),
                "last_message": data["last_message"][:80] + ("..." if len(data["last_message"]) > 80 else ""),
                "created_at": data["created_at"],
                "unread": data["unread"],
            })
        # Sort by latest message
        conversations.sort(key=lambda x: x["created_at"], reverse=True)
        return conversations
    except Exception as e:
        st.session_state.last_error = f"Error loading conversations: {e}"
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
        # Mark as read
        supabase.table("messages").update({"read": True}).eq("sender_id", other_id).eq("receiver_id", user_id).execute()
        return all_msgs
    except Exception as e:
        st.session_state.last_error = f"Error loading messages: {e}"
        return []

# ---- Call System (with ringtone and missed calls) ----
def create_call_record(caller_id, receiver_id, room):
    if supabase is None:
        return None
    try:
        data = {
            "caller_id": caller_id,
            "receiver_id": receiver_id,
            "room": room,
            "status": "ringing",
            "started_at": datetime.now().isoformat()
        }
        result = supabase.table("calls").insert(data).execute()
        if result.data:
            return result.data[0]["id"]
        return None
    except Exception as e:
        st.session_state.last_error = f"Error creating call record: {e}"
        return None

def update_call_status(call_id, status, ended_at=None):
    if supabase is None:
        return
    try:
        update_data = {"status": status}
        if ended_at:
            update_data["ended_at"] = ended_at
        supabase.table("calls").update(update_data).eq("id", call_id).execute()
    except Exception as e:
        st.session_state.last_error = f"Error updating call status: {e}"

def get_missed_calls(user_id):
    """Get missed calls for the user."""
    if supabase is None:
        return []
    try:
        resp = supabase.table("calls").select("*, caller:caller_id(full_name)").eq("receiver_id", user_id).eq("status", "missed").order("started_at", desc=True).execute()
        return resp.data or []
    except Exception as e:
        st.session_state.last_error = f"Error loading missed calls: {e}"
        return []

def initiate_call(target_user_id, audio_only=False):
    """Initiate a call: create call record, send notification with ringtone."""
    if st.session_state.call_ringing:
        st.warning("You already have an ongoing call or ringing.")
        return
    room = hashlib.md5(f"{st.session_state.user.id}_{target_user_id}_{time.time()}".encode()).hexdigest()[:10]
    call_type = " (Audio)" if audio_only else ""
    # Create call record
    call_id = create_call_record(st.session_state.user.id, target_user_id, room)
    if not call_id:
        st.error("Failed to initiate call.")
        return
    # Send notification to receiver with call details
    try:
        # We'll store call_id in the notification data or as related_id
        supabase.table("notifications").insert({
            "user_id": target_user_id,
            "type": "call_request",
            "message": f"📞 {st.session_state.profile['full_name']} is calling you{call_type}.",
            "read": False,
            "created_at": datetime.now().isoformat(),
            "related_id": call_id,  # store call_id
            "data": {"room": room, "caller": st.session_state.user.id}
        }).execute()
    except Exception as e:
        st.error(f"Failed to send call notification: {e}")
        update_call_status(call_id, "missed", datetime.now().isoformat())
        return
    # Set session state for ringing
    start_call(room, audio_only)
    st.session_state.call_target_user = target_user_id
    st.session_state.call_ringing = True
    st.session_state.call_initiated_time = time.time()
    st.session_state.current_call_id = call_id  # store for later
    st.rerun()

def accept_call(notification):
    """Accept an incoming call: update call status, start Jitsi session."""
    call_id = notification.get("related_id")
    if not call_id:
        return
    # Update call status to answered
    update_call_status(call_id, "answered", datetime.now().isoformat())
    # Get room from notification data
    data = notification.get("data", {})
    room = data.get("room")
    if room:
        st.session_state.call_room = room
        st.session_state.in_call = True
        st.session_state.call_audio_only = False  # could be audio-only but we'll let Jitsi handle
        st.rerun()
    else:
        st.error("Call room not found.")

def reject_call(notification):
    call_id = notification.get("related_id")
    if call_id:
        update_call_status(call_id, "rejected", datetime.now().isoformat())
        st.success("Call rejected.")
        st.rerun()

def check_missed_calls():
    """Check for any call that has been ringing for more than 30s and mark as missed."""
    if supabase is None:
        return
    try:
        # Get all ringing calls older than 30s
        cutoff = (datetime.now() - timedelta(seconds=30)).isoformat()
        resp = supabase.table("calls").select("id, caller_id, receiver_id, room").eq("status", "ringing").lt("started_at", cutoff).execute()
        for call in resp.data or []:
            # Update status to missed
            update_call_status(call["id"], "missed", datetime.now().isoformat())
            # Notify the caller that the call was missed
            try:
                caller_name = supabase.table("profiles").select("full_name").eq("id", call["caller_id"]).single().execute().data.get("full_name", "Someone")
            except:
                caller_name = "Someone"
            supabase.table("notifications").insert({
                "user_id": call["caller_id"],
                "type": "missed_call",
                "message": f"📞 Missed call from {caller_name}. Do you want to call back?",
                "read": False,
                "related_id": call["id"],
                "data": {"room": call["room"], "receiver": call["receiver_id"]}
            }).execute()
            # Also notify the receiver? They already got a notification.
    except Exception as e:
        st.session_state.last_error = f"Error checking missed calls: {e}"

def render_incoming_call(notification):
    """Render Accept/Reject buttons for an incoming call."""
    st.markdown(f"<div class='incoming-call-box'><b>{t('incoming_call', name=notification.get('message',''))}</b></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("accept_call"), key=f"accept_call_{notification['id']}"):
            accept_call(notification)
    with col2:
        if st.button(t("reject_call"), key=f"reject_call_{notification['id']}"):
            reject_call(notification)

def render_missed_call(notification):
    """Render missed call notification with call back button."""
    st.markdown(f"<div class='missed-call-box'><b>{notification['message']}</b></div>", unsafe_allow_html=True)
    if st.button(t("call_back"), key=f"callback_{notification['id']}"):
        # Extract receiver/caller info from notification data
        data = notification.get("data", {})
        receiver_id = data.get("receiver")
        if receiver_id:
            initiate_call(receiver_id, audio_only=True)
        else:
            # Try to get from related_id
            call_id = notification.get("related_id")
            if call_id:
                # Fetch call details to get receiver
                try:
                    call_resp = supabase.table("calls").select("receiver_id").eq("id", call_id).single().execute()
                    if call_resp.data:
                        receiver_id = call_resp.data["receiver_id"]
                        initiate_call(receiver_id, audio_only=True)
                except:
                    pass
        st.rerun()

# ---- Video call functions ----
def start_call(room_id=None, audio_only=False):
    if not room_id:
        room_id = hashlib.md5(f"{st.session_state.user.id}_{time.time()}".encode()).hexdigest()[:10]
    st.session_state.call_room = room_id
    st.session_state.in_call = True
    st.session_state.call_audio_only = audio_only
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
        if supabase:
            try:
                supabase.table("video_calls").update({"ended_at": datetime.now().isoformat(), "is_active": False}).eq("room", st.session_state.call_room).eq("is_active", True).execute()
            except Exception:
                pass
    st.session_state.in_call = False
    st.session_state.call_room = None
    st.session_state.call_ringing = False
    st.session_state.call_initiated_time = None
    st.session_state.call_audio_only = False
    st.session_state.current_call_id = None

def initiate_phone_call(target_user_id):
    """Wrapper to initiate an audio-only phone call."""
    initiate_call(target_user_id, audio_only=True)

def check_call_status():
    if st.session_state.call_ringing and st.session_state.call_initiated_time:
        elapsed = time.time() - st.session_state.call_initiated_time
        if elapsed > 30:
            st.session_state.call_ringing = False
            st.session_state.call_initiated_time = None
            st.session_state.call_audio_only = False
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
            if not ensure_bucket_exists("album_photos"):
                bucket = "post_media"
            else:
                bucket = "album_photos"
            supabase.storage.from_(bucket).upload(
                file_name,
                compressed_bytes,
                {"content-type": content_type}
            )
            public_url = supabase.storage.from_(bucket).get_public_url(file_name)
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
        photos = supabase.table("album_photos").select("id").eq("album_id", album_id).execute().data or []
        for p in photos:
            supabase.table("album_photos").delete().eq("id", p["id"]).execute()
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
    if supabase is None:
        return []
    try:
        albums = supabase.table("photo_albums").select("*").order("created_at", desc=True).execute().data or []
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
        return latency, signal, quality
    except Exception:
        return 999, "OFFLINE", 0

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
    st.session_state.call_audio_only = False
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
    """Render the top action icons: Phone, Messages, Notifications (for logged-in user)."""
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
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        label = f"📞"  # Phone icon
        if st.button(label, key="top_call_icon", use_container_width=True):
            # If viewing a profile, call that user; otherwise, maybe show a call prompt?
            if st.session_state.viewing_profile:
                initiate_phone_call(st.session_state.viewing_profile)
            else:
                st.info("Go to a user's profile to call them.")
    with col2:
        label = f"💬 {unread_msgs}" if unread_msgs > 0 else "💬"
        if st.button(label, key="top_msg_icon", use_container_width=True):
            st.session_state.current_page = "friends_chat"
            st.rerun()
    with col3:
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
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        st.error("Groq API key not set. Add GROQ_API_KEY to your secrets.")
        return []

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
    if supabase is None:
        st.info("Unable to load users – database not connected.")
        return
    try:
        current_user_id = st.session_state.user.id
        all_users = get_all_users()
        if not all_users:
            st.info("No other users found.")
            return

        friends_ids = {f["id"] for f in st.session_state.friends}
        req_resp = supabase.table("friend_requests").select("*").eq("status", "pending").execute()
        pending_requests = req_resp.data or []
        sent_dict = {}
        received_dict = {}
        for req in pending_requests:
            if req["sender_id"] == current_user_id:
                sent_dict[req["receiver_id"]] = req["id"]
            if req["receiver_id"] == current_user_id:
                received_dict[req["sender_id"]] = req["id"]

        non_friends = []
        for u in all_users:
            uid = u["id"]
            if uid == current_user_id:
                continue
            if uid in friends_ids:
                continue
            if uid in sent_dict:
                status = "sent"
                request_id = sent_dict[uid]
            elif uid in received_dict:
                status = "received"
                request_id = received_dict[uid]
            else:
                status = "none"
                request_id = None
            u.setdefault("profile_visibility", "public")
            non_friends.append({**u, "status": status, "request_id": request_id})

        if not non_friends:
            st.info("🎉 You are already friends with everyone on the platform!")
            return

        cols = st.columns(3)
        for idx, user in enumerate(non_friends):
            with cols[idx % 3]:
                with st.container():
                    st.markdown('<div class="discover-card">', unsafe_allow_html=True)
                    col_av, col_name = st.columns([1, 3])
                    with col_av:
                        display_avatar_and_followers(user.get("avatar_url"), user["id"], size=70, profile=user)
                    with col_name:
                        if st.button(user['full_name'], key=f"discover_name_{user['id']}"):
                            st.session_state.viewing_profile = user['id']
                            st.rerun()
                        if user.get("is_banned"):
                            st.caption("🚫 Banned")
                        else:
                            st.caption("📌 " + user.get("location", ""))

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
    st.info(t("paste_video_link_hint"))
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

    # ====== FEED SEARCH AND REFRESH ======
    st.markdown("#### 📋 Feed")
    search_col, refresh_col = st.columns([3, 1])
    with search_col:
        search_term = st.text_input(
            t("search_posts"),
            value=st.session_state.feed_search_term,
            key="feed_search_input",
            placeholder=t("search_posts"),
            label_visibility="collapsed"
        )
        if search_term != st.session_state.feed_search_term:
            st.session_state.feed_search_term = search_term
    with refresh_col:
        if st.button(t("refresh_feed"), use_container_width=True):
            st.cache_data.clear()
            st.session_state.posts = load_posts()
            st.session_state.feed_search_term = ""
            st.rerun()

    all_posts = st.session_state.posts
    search_term_lower = st.session_state.feed_search_term.lower().strip()
    if search_term_lower:
        filtered_posts = [p for p in all_posts if search_term_lower in p.get('content', '').lower()]
    else:
        filtered_posts = all_posts

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

    if not filtered_posts:
        if st.session_state.feed_search_term:
            st.info("No posts match your search. Try a different term.")
        else:
            st.info("No posts yet. Be the first to create one!")
    else:
        for post in filtered_posts:
            with st.container():
                col_a, col_b, col_c, col_d, col_e = st.columns([1,4,2,1,1])
                with col_a:
                    display_avatar_and_followers(post["profiles"].get("avatar_url"), post["user_id"], size=50, profile=post["profiles"])
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
                    if post['content'].startswith("🔴 I'm live:"):
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

                media_urls = post.get("media_urls", [])
                if media_urls:
                    for media in media_urls:
                        display_media_item(media)

                if post['content']:
                    clickable_content = make_clickable(post['content'])
                    st.markdown(f"<div class='post-card'>{clickable_content}</div>", unsafe_allow_html=True)
                    urls = re.findall(r'(https?://[^\s]+)', post['content'])
                    for url in urls:
                        try:
                            embed_video_from_url(url)
                        except Exception:
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

    # ---- Top Action Bar: Phone, Message, Notification ----
    is_own_profile = (user_id == st.session_state.user.id)
    if not is_own_profile:
        st.markdown('<div class="profile-action-bar">', unsafe_allow_html=True)
        col_phone, col_msg, col_notif = st.columns(3)
        with col_phone:
            if st.button("📞", key=f"top_call_{user_id}", help="Call this user"):
                initiate_phone_call(user_id)
                st.rerun()
            st.caption("Call")
        with col_msg:
            if st.button("💬", key=f"top_msg_{user_id}", help="Send a message"):
                st.session_state.selected_chat = user_id
                st.session_state.current_page = "friends_chat"
                st.rerun()
            st.caption("Message")
        with col_notif:
            # This could be a bell icon, but we already have a global notification icon.
            # We'll just show a bell that goes to notifications page.
            if st.button("🔔", key=f"top_notif_{user_id}", help="Notifications"):
                st.session_state.current_page = "friends_chat"
                st.rerun()
            st.caption("Notifications")
        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

    st.header(f"👤 {profile['full_name']}'s Profile")
    col1, col2 = st.columns([1,2])
    with col1:
        display_avatar_and_followers(profile.get("avatar_url"), user_id, large=True, profile=profile)
        st.markdown(f"**{t('bio')}:** {profile.get('bio', 'No bio')}")
        st.markdown(f"**{t('location')}:** {profile.get('location', 'Unknown')}")
        st.markdown(f"**{t('moncash_phone')}:** {profile.get('moncash_phone', 'Not set')}")
        st.markdown(f"**{t('natcash_phone')}:** {profile.get('natcash_phone', 'Not set')}")
        st.markdown(f"**{t('member_since')}:** {profile.get('join_date', '')[:10]}")
        st.markdown(f"**{t('profile_visibility')}:** {profile.get('profile_visibility', 'public').capitalize()}")
        st.markdown(f"**{t('unibank_usd_account')}:** {profile.get('unibank_usd_account', 'Not set')}")
        st.markdown(f"**{t('unibank_htg_account')}:** {profile.get('unibank_htg_account', 'Not set')}")
        st.markdown(f"**{t('cin_number')}:** {profile.get('cin_number', 'Not set')}")

        if not is_own_profile:
            # ---- BIG ICON ROW: Phone, Chat, Email, WhatsApp ----
            st.markdown('<div class="big-icon-row">', unsafe_allow_html=True)

            # Phone icon (audio-only call)
            col_phone, col_chat, col_email, col_wa = st.columns(4)
            with col_phone:
                if st.button("📞\nCall", key=f"phone_call_{user_id}", use_container_width=True):
                    initiate_phone_call(user_id)
                    st.rerun()
            with col_chat:
                if st.button("💬\nChat", key=f"chat_{user_id}_big", use_container_width=True):
                    st.session_state.selected_chat = user_id
                    st.session_state.viewing_profile = None
                    st.rerun()
            with col_email:
                if profile.get("email"):
                    st.markdown(f'<a href="mailto:{profile["email"]}" target="_blank" style="display:block; text-align:center; background:#f0f7ff; border:2px solid #0080ff; border-radius:50%; width:70px; height:70px; line-height:70px; font-size:2.2rem; text-decoration:none; color:#0080ff; margin:0 auto; box-shadow:0 4px 8px rgba(0,0,0,0.05);"><i>📧</i><span style="display:block; font-size:0.65rem; line-height:1.2; margin-top:-10px; color:inherit; font-weight:600;">Email</span></a>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="width:70px; height:70px; border-radius:50%; background:#ccc; line-height:70px; text-align:center; font-size:2rem; color:#888; margin:0 auto;">📧</div>', unsafe_allow_html=True)
            with col_wa:
                if profile.get("whatsapp_phone"):
                    wa_number = profile["whatsapp_phone"].replace("+", "").strip()
                    st.markdown(f'<a href="https://wa.me/{wa_number}" target="_blank" style="display:block; text-align:center; background:#f0f7ff; border:2px solid #25D366; border-radius:50%; width:70px; height:70px; line-height:70px; font-size:2.2rem; text-decoration:none; color:#25D366; margin:0 auto; box-shadow:0 4px 8px rgba(0,0,0,0.05);"><i>💬</i><span style="display:block; font-size:0.65rem; line-height:1.2; margin-top:-10px; color:inherit; font-weight:600;">WhatsApp</span></a>', unsafe_allow_html=True)
                else:
                    st.markdown('<div style="width:70px; height:70px; border-radius:50%; background:#ccc; line-height:70px; text-align:center; font-size:2rem; color:#888; margin:0 auto;">💬</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        if show_back_button:
            if st.button(t("back_to_feed")):
                st.session_state.viewing_profile = None
                st.rerun()

    with col2:
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

        # ---- 💳 BANK TRANSFER INSTRUCTIONS (ONLY ON OWN PRIVATE PROFILE) ----
        if is_own_profile:
            st.divider()
            st.subheader("💳 My Bank Transfer Instructions")
            st.markdown("""
            Download your personal UNIBANK wire transfer instructions.
            These documents include your personal account numbers and CIN.
            """)

            # Get user's personal banking details
            usd_account = profile.get('unibank_usd_account', 'Not set')
            htg_account = profile.get('unibank_htg_account', 'Not set')
            cin_number = profile.get('cin_number', 'Not set')
            full_name = profile.get('full_name', 'User')
            moncash_phone = profile.get('moncash_phone', 'Not set')
            natcash_phone = profile.get('natcash_phone', 'Not set')

            # ---- ENGLISH VERSION (Personalized) ----
            instructions_en = f"""
            ============================================================
            UNIBANK WIRE TRANSFER INSTRUCTIONS
            (for receiving funds from abroad)
            ============================================================

            BANK: UNIBANK S.A.
            ADDRESS: IMMEUBLE RIVOLI, 157, RUE FLAUBERT, PETION-VILLE, HAITI
            SWIFT/BIC: UBNKHTPPXXX

            CIN CARD NUMBER : {cin_number}
            BENEFICIARY NAME : {full_name}

            ------------------------------------------------------------
            FOR USD TRANSFERS (from USA)
            ------------------------------------------------------------
            Beneficiary Bank: UNIBANK S.A., Haiti
            SWIFT: UBNKHTPPXXX
            Beneficiary Account Number: {usd_account}
            Beneficiary Name: {full_name}

            Choose ONE of the following intermediary banks:

            1) Bank of America, Miami, FL
               SWIFT: BOFAUS3M
               ABA: 026009593
               Account: 1901892336

            2) Bank of New York, New York, NY
               SWIFT: IRVTUS3N
               ABA: 021000018
               Account: 8900570881

            3) Citibank N.A., New York, NY
               SWIFT: CITIUS33
               ABA: 021000089
               Account: 36338572

            ------------------------------------------------------------
            FOR USD TRANSFERS (from Europe)
            ------------------------------------------------------------
            Intermediary Bank: Bank of America, London, England
            SWIFT: BOFAGB22
            IBAN (for EUR SEPA): GB33BOFA16505023805023
            Account: 600823805023

            Beneficiary Bank: UNIBANK S.A., Haiti
            SWIFT: UBNKHTPPXXX
            Beneficiary Account Number: {usd_account}
            Beneficiary Name: {full_name}

            ------------------------------------------------------------
            FOR HTG TRANSFERS (from abroad)
            ------------------------------------------------------------
            HTG transfers from outside Haiti typically use the same USD routing.
            The funds are sent in USD via one of the intermediary banks above,
            and UNIBANK will automatically convert them to HTG at the prevailing
            exchange rate upon arrival.

            Beneficiary Account Number (HTG): {htg_account}
            Beneficiary Name: {full_name}

            For domestic HTG transfers inside Haiti, use the SPIH system (no SWIFT).

            ------------------------------------------------------------
            PRISME TRANSFER – WORLDWIDE QUICK & INSTANT TRANSACTIONS
            ------------------------------------------------------------
            For fast and easy payments, you can also use Prisme Transfer via:
            - Digicel MonCash: {moncash_phone}
            - Natcom Natcash: {natcash_phone}

            This method is ideal for quick, small to medium amounts and works globally.
            Contact the recipient to confirm their mobile money details before sending.

            ------------------------------------------------------------
            IMPORTANT NOTES
            ------------------------------------------------------------
            - Always double‑check the beneficiary name and account number.
            - Transfers usually arrive within 24‑48 hours, but can take 3‑5 business days.
            - Contact UNIBANK directly if you need the latest intermediary bank list.
            - For large amounts, consider using a test transaction first.

            CIN CARD NUMBER : {cin_number}

            ============================================================
            """

            # ---- FRENCH VERSION (Personalized) ----
            instructions_fr = f"""
            ============================================================
            INSTRUCTIONS DE VIREMENT BANCAIRE UNIBANK
            (pour recevoir des fonds de l'étranger)
            ============================================================

            BANQUE : UNIBANK S.A.
            ADRESSE : IMMEUBLE RIVOLI, 157, RUE FLAUBERT, PETION-VILLE, HAÏTI
            SWIFT/BIC : UBNKHTPPXXX

            CIN CARD NUMBER : {cin_number}
            NOM DU BÉNÉFICIAIRE : {full_name}

            ------------------------------------------------------------
            POUR LES TRANSFERTS EN USD (depuis les États-Unis)
            ------------------------------------------------------------
            Banque bénéficiaire : UNIBANK S.A., Haïti
            SWIFT : UBNKHTPPXXX
            Numéro de compte du bénéficiaire : {usd_account}
            Nom du bénéficiaire : {full_name}

            Choisissez UNE des banques intermédiaires suivantes :

            1) Bank of America, Miami, FL
               SWIFT : BOFAUS3M
               ABA : 026009593
               Compte : 1901892336

            2) Bank of New York, New York, NY
               SWIFT : IRVTUS3N
               ABA : 021000018
               Compte : 8900570881

            3) Citibank N.A., New York, NY
               SWIFT : CITIUS33
               ABA : 021000089
               Compte : 36338572

            ------------------------------------------------------------
            POUR LES TRANSFERTS EN USD (depuis l'Europe)
            ------------------------------------------------------------
            Banque intermédiaire : Bank of America, Londres, Angleterre
            SWIFT : BOFAGB22
            IBAN (pour virement SEPA en EUR) : GB33BOFA16505023805023
            Compte : 600823805023

            Banque bénéficiaire : UNIBANK S.A., Haïti
            SWIFT : UBNKHTPPXXX
            Numéro de compte du bénéficiaire : {usd_account}
            Nom du bénéficiaire : {full_name}

            ------------------------------------------------------------
            POUR LES TRANSFERTS EN HTG (depuis l'étranger)
            ------------------------------------------------------------
            Les transferts en HTG depuis l'extérieur d'Haïti utilisent généralement le même
            routage que les USD. Les fonds sont envoyés en USD via l'une des banques
            intermédiaires ci-dessus, et UNIBANK les convertit automatiquement en HTG
            au taux de change en vigueur à l'arrivée.

            Numéro de compte du bénéficiaire (HTG) : {htg_account}
            Nom du bénéficiaire : {full_name}

            Pour les transferts HTG nationaux à l'intérieur d'Haïti, utilisez le système SPIH
            (pas de SWIFT).

            ------------------------------------------------------------
            PRISME TRANSFER – TRANSACTIONS RAPIDES ET INSTANTANÉES DANS LE MONDE
            ------------------------------------------------------------
            Pour des paiements rapides et faciles, vous pouvez également utiliser Prisme Transfer via :
            - Digicel MonCash : {moncash_phone}
            - Natcom Natcash : {natcash_phone}

            Cette méthode est idéale pour des montants petits à moyens, et fonctionne à l'échelle mondiale.
            Contactez le bénéficiaire pour confirmer ses coordonnées avant d'envoyer.

            ------------------------------------------------------------
            REMARQUES IMPORTANTES
            ------------------------------------------------------------
            - Vérifiez toujours le nom du bénéficiaire et le numéro de compte.
            - Les virements arrivent généralement sous 24 à 48 heures, mais peuvent
              prendre 3 à 5 jours ouvrables.
            - Contactez directement UNIBANK pour obtenir la liste la plus récente
              des banques intermédiaires.
            - Pour les montants importants, envisagez d'effectuer un test de transfert
              au préalable.

            CIN CARD NUMBER : {cin_number}

            ============================================================
            """

            # ---- Download buttons side by side ----
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.download_button(
                    label="🇬🇧 Download Instructions (English)",
                    data=instructions_en,
                    file_name=f"UNIBANK_instructions_{full_name.replace(' ', '_')}_EN_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            with col_btn2:
                st.download_button(
                    label="🇫🇷 Télécharger les instructions (Français)",
                    data=instructions_fr,
                    file_name=f"UNIBANK_instructions_{full_name.replace(' ', '_')}_FR_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            if usd_account == 'Not set' or htg_account == 'Not set':
                st.warning("⚠️ Please add your UNIBANK account numbers in your profile settings to generate personalized instructions.")

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

    if st.session_state.call_ringing and st.session_state.call_target_user == user_id:
        st.info(t("ringing"))
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
        render_top_icons()  # show phone, message, notification icons

        # ---- Check for missed calls ----
        check_missed_calls()

        # ---- Handle incoming call notifications ----
        # We'll scan notifications for call_request and render accept/reject if any
        call_request_notifications = [n for n in st.session_state.notifications if n.get('type') == 'call_request' and not n.get('read')]
        for notif in call_request_notifications:
            render_incoming_call(notif)

        # ---- Handle missed call notifications ----
        missed_call_notifications = [n for n in st.session_state.notifications if n.get('type') == 'missed_call' and not n.get('read')]
        for notif in missed_call_notifications:
            render_missed_call(notif)

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
                    # Skip call_request and missed_call as they are handled above
                    if n.get('type') in ['call_request', 'missed_call']:
                        continue
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
                    if st.button(friend['full_name'], key=f"friend_name_{friend['id']}"):
                        st.session_state.viewing_profile = friend['id']
                        st.rerun()
                with cols[2]:
                    if st.button(t("chat"), key=f"chat_{friend['id']}"):
                        st.session_state.selected_chat = friend['id']
                        st.rerun()
                with cols[3]:
                    if st.button(t("call"), key=f"call_{friend['id']}"):
                        initiate_phone_call(friend['id'])
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

        # ---- Conversation List (Inbox) ----
        st.divider()
        st.subheader("📬 " + t("conversations"))
        conversations = get_conversations(st.session_state.user.id)
        if not conversations:
            st.info(t("no_conversations"))
        else:
            for conv in conversations:
                with st.container():
                    cols = st.columns([1,6,1])
                    with cols[0]:
                        display_avatar_and_followers(conv.get('avatar_url'), conv['other_id'], size=50, profile=conv)
                    with cols[1]:
                        if st.button(conv['full_name'], key=f"conv_{conv['other_id']}"):
                            st.session_state.selected_chat = conv['other_id']
                            st.rerun()
                        st.caption(conv['last_message'])
                        if conv['unread']:
                            st.markdown(f"<span class='unread-badge'>New</span>", unsafe_allow_html=True)
                    with cols[2]:
                        st.caption(conv['created_at'][:16])
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
                # Emoji picker: simple buttons
                st.markdown("**Emojis:** 😀 😂 ❤️ 👍 😮 😢 😡 🎉 🔥 💯")
                col_emoji = st.columns(10)
                emojis = ["😀","😂","❤️","👍","😮","😢","😡","🎉","🔥","💯"]
                for i, emoji in enumerate(emojis):
                    with col_emoji[i]:
                        if st.button(emoji, key=f"emoji_{i}"):
                            # Append emoji to message input
                            # We'll use a session state variable to store the current message
                            current_msg = st.session_state.get("chat_input", "")
                            st.session_state.chat_input = current_msg + emoji
                            st.rerun()
                msg_content = st.text_input(t("send_message"), placeholder="Type your message...", value=st.session_state.get("chat_input", ""))
                uploaded_file = st.file_uploader(t("add_media"), type=["png","jpg","jpeg","gif","mp4","mov","avi"])
                st.caption("⚠️ File size limit: 200MB. For larger videos, use external links.")
                col1, col2 = st.columns([1,5])
                with col1:
                    sent = st.form_submit_button(t("send_message_btn"))
                if sent:
                    if msg_content or uploaded_file:
                        send_message(st.session_state.user.id, other_id, msg_content or "", media_file=uploaded_file)
                        st.session_state.chat_input = ""
                        st.rerun()

            st.divider()
        else:
            st.info("Select a friend and click 'Chat' to start a private conversation, or click a conversation from the inbox above.")

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
            # If audio-only, mute video by default
            start_with_video_muted = st.session_state.get('call_audio_only', False)
            config_overwrite = {"startWithAudioMuted": False,
                                "startWithVideoMuted": start_with_video_muted,
                                "disableWelcomePage": True,
                                "disableDeepLinking": True,
                                "p2p": {"enabled": False}}
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
                st.session_state.call_audio_only = False
                end_call()
                st.rerun()
        else:
            if st.button(t("start_call")):
                start_call(audio_only=False)  # video call from here
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

def render_profile():
    st.header(t("profile"))
    render_top_icons()
    if st.session_state.profile is None:
        return
    profile = st.session_state.profile
    col1, col2 = st.columns([1,2])
    with col1:
        display_avatar_and_followers(profile.get("avatar_url"), st.session_state.user.id, large=True, profile=profile)
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

            # ---- NEW BANKING FIELDS ----
            st.markdown("#### 💳 Banking Information")
            unibank_usd_account = st.text_input(t("unibank_usd_account"), value=profile.get("unibank_usd_account", ""))
            unibank_htg_account = st.text_input(t("unibank_htg_account"), value=profile.get("unibank_htg_account", ""))
            cin_number = st.text_input(t("cin_number"), value=profile.get("cin_number", ""))

            if st.form_submit_button(t("save_changes"), use_container_width=True):
                profile.update({
                    "full_name": full_name,
                    "bio": bio,
                    "location": location,
                    "moncash_phone": moncash_phone,
                    "natcash_phone": natcash_phone,
                    "email": email,
                    "whatsapp_phone": whatsapp_phone,
                    "profile_visibility": profile_visibility,
                    "unibank_usd_account": unibank_usd_account,
                    "unibank_htg_account": unibank_htg_account,
                    "cin_number": cin_number
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
                    display_avatar_and_followers(post["profiles"].get("avatar_url"), post["user_id"], size=50, profile=st.session_state.profile)
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

# ====== OWNER SPACE (UPDATED WITH PRISME TRANSFER) ======
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

    try:
        last_seen = get_last_seen_signup()
        new_users = get_new_users(last_seen)
        if new_users:
            send_email_notification(new_users)
            update_last_seen_signup()
    except Exception as e:
        st.warning(f"⚠️ Could not load new users: {e}")
        new_users = []

    # ---- TABS LIST (includes "💳 Bank Transfer Info") ----
    tabs = st.tabs([
        t("dashboard"), t("new_users"), t("post_moderation"),
        t("client_payments"), t("gift_management"), t("user_management"),
        "📸 Albums", "🕵️ Live Monitoring", "💳 Bank Transfer Info"
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

    # ---- TAB 9: 💳 Bank Transfer Info (with Prisme Transfer) ----
    with tabs[8]:
        st.subheader("💳 UNIBANK Wire Transfer Instructions")
        st.markdown("""
        Use the information below to receive international wire transfers in **USD** or **HTG**.
        All routing details are public – your **account numbers** are kept secret and loaded from secure secrets.
        """)

        # ----- Read account numbers from secrets (never hardcoded!) -----
        usd_account = st.secrets.get("UNIBANK_USD_ACCOUNT", "⚠️ NOT SET in secrets")
        htg_account = st.secrets.get("UNIBANK_HTG_ACCOUNT", "⚠️ NOT SET in secrets")

        # ----- ENGLISH VERSION (with Prisme Transfer) -----
        instructions_en = f"""
        ============================================================
        UNIBANK WIRE TRANSFER INSTRUCTIONS
        (for receiving funds from abroad)
        ============================================================

        BANK: UNIBANK S.A.
        ADDRESS: IMMEUBLE RIVOLI, 157, RUE FLAUBERT, PETION-VILLE, HAITI
        SWIFT/BIC: UBNKHTPPXXX

        CIN CARD NUMBER : 1248795849

        ------------------------------------------------------------
        FOR USD TRANSFERS (from USA)
        ------------------------------------------------------------
        Beneficiary Bank: UNIBANK S.A., Haiti
        SWIFT: UBNKHTPPXXX
        Beneficiary Account Number: {usd_account}
        Beneficiary Name: [Your full business/personal name as registered with UNIBANK]

        Choose ONE of the following intermediary banks:

        1) Bank of America, Miami, FL
           SWIFT: BOFAUS3M
           ABA: 026009593
           Account: 1901892336

        2) Bank of New York, New York, NY
           SWIFT: IRVTUS3N
           ABA: 021000018
           Account: 8900570881

        3) Citibank N.A., New York, NY
           SWIFT: CITIUS33
           ABA: 021000089
           Account: 36338572

        ------------------------------------------------------------
        FOR USD TRANSFERS (from Europe)
        ------------------------------------------------------------
        Intermediary Bank: Bank of America, London, England
        SWIFT: BOFAGB22
        IBAN (for EUR SEPA): GB33BOFA16505023805023
        Account: 600823805023

        Beneficiary Bank: UNIBANK S.A., Haiti
        SWIFT: UBNKHTPPXXX
        Beneficiary Account Number: {usd_account}
        Beneficiary Name: [Your full business/personal name]

        ------------------------------------------------------------
        FOR HTG TRANSFERS (from abroad)
        ------------------------------------------------------------
        HTG transfers from outside Haiti typically use the same USD routing.
        The funds are sent in USD via one of the intermediary banks above,
        and UNIBANK will automatically convert them to HTG at the prevailing
        exchange rate upon arrival.

        Beneficiary Account Number (HTG): {htg_account}
        Beneficiary Name: [Your full business/personal name]

        For domestic HTG transfers inside Haiti, use the SPIH system (no SWIFT).

        ------------------------------------------------------------
        PRISME TRANSFER – WORLDWIDE QUICK & INSTANT TRANSACTIONS
        ------------------------------------------------------------
        For fast and easy payments, you can also use Prisme Transfer via:
        - Digicel MonCash: (509) 4738-5663
        - Natcom Natcash: [Your NATCASH Number]

        This method is ideal for quick, small to medium amounts and works globally.
        Contact us to confirm the recipient's mobile money details before sending.

        ------------------------------------------------------------
        IMPORTANT NOTES
        ------------------------------------------------------------
        - Always double‑check the beneficiary name and account number.
        - Transfers usually arrive within 24‑48 hours, but can take 3‑5 business days.
        - Contact UNIBANK directly if you need the latest intermediary bank list.
        - For large amounts, consider using a test transaction first.

        For assistance, contact us:
        Phone: (509) 4738-5663
        Email: deslandes78@gmail.com
        WhatsApp: +50947385663

        CIN CARD NUMBER : 1248795849

        ============================================================
        """

        # ----- FRENCH VERSION (with Prisme Transfer) -----
        instructions_fr = f"""
        ============================================================
        INSTRUCTIONS DE VIREMENT BANCAIRE UNIBANK
        (pour recevoir des fonds de l'étranger)
        ============================================================

        BANQUE : UNIBANK S.A.
        ADRESSE : IMMEUBLE RIVOLI, 157, RUE FLAUBERT, PETION-VILLE, HAÏTI
        SWIFT/BIC : UBNKHTPPXXX

        CIN CARD NUMBER : 1248795849

        ------------------------------------------------------------
        POUR LES TRANSFERTS EN USD (depuis les États-Unis)
        ------------------------------------------------------------
        Banque bénéficiaire : UNIBANK S.A., Haïti
        SWIFT : UBNKHTPPXXX
        Numéro de compte du bénéficiaire : {usd_account}
        Nom du bénéficiaire : [Votre nom commercial / personnel complet tel qu'enregistré auprès d'UNIBANK]

        Choisissez UNE des banques intermédiaires suivantes :

        1) Bank of America, Miami, FL
           SWIFT : BOFAUS3M
           ABA : 026009593
           Compte : 1901892336

        2) Bank of New York, New York, NY
           SWIFT : IRVTUS3N
           ABA : 021000018
           Compte : 8900570881

        3) Citibank N.A., New York, NY
           SWIFT : CITIUS33
           ABA : 021000089
           Compte : 36338572

        ------------------------------------------------------------
        POUR LES TRANSFERTS EN USD (depuis l'Europe)
        ------------------------------------------------------------
        Banque intermédiaire : Bank of America, Londres, Angleterre
        SWIFT : BOFAGB22
        IBAN (pour virement SEPA en EUR) : GB33BOFA16505023805023
        Compte : 600823805023

        Banque bénéficiaire : UNIBANK S.A., Haïti
        SWIFT : UBNKHTPPXXX
        Numéro de compte du bénéficiaire : {usd_account}
        Nom du bénéficiaire : [Votre nom commercial / personnel complet]

        ------------------------------------------------------------
        POUR LES TRANSFERTS EN HTG (depuis l'étranger)
        ------------------------------------------------------------
        Les transferts en HTG depuis l'extérieur d'Haïti utilisent généralement le même
        routage que les USD. Les fonds sont envoyés en USD via l'une des banques
        intermédiaires ci-dessus, et UNIBANK les convertit automatiquement en HTG
        au taux de change en vigueur à l'arrivée.

        Numéro de compte du bénéficiaire (HTG) : {htg_account}
        Nom du bénéficiaire : [Votre nom commercial / personnel complet]

        Pour les transferts HTG nationaux à l'intérieur d'Haïti, utilisez le système SPIH
        (pas de SWIFT).

        ------------------------------------------------------------
        PRISME TRANSFER – TRANSACTIONS RAPIDES ET INSTANTANÉES DANS LE MONDE
        ------------------------------------------------------------
        Pour des paiements rapides et faciles, vous pouvez également utiliser Prisme Transfer via :
        - Digicel MonCash : (509) 4738-5663
        - Natcom Natcash : [Votre numéro NATCASH]

        Cette méthode est idéale pour des montants petits à moyens, et fonctionne à l'échelle mondiale.
        Contactez-nous pour confirmer les coordonnées du bénéficiaire avant d'envoyer.

        ------------------------------------------------------------
        REMARQUES IMPORTANTES
        ------------------------------------------------------------
        - Vérifiez toujours le nom du bénéficiaire et le numéro de compte.
        - Les virements arrivent généralement sous 24 à 48 heures, mais peuvent
          prendre 3 à 5 jours ouvrables.
        - Contactez directement UNIBANK pour obtenir la liste la plus récente
          des banques intermédiaires.
        - Pour les montants importants, envisagez d'effectuer un test de transfert
          au préalable.

        Pour toute assistance, contactez-nous :
        Téléphone : (509) 4738-5663
        E-mail : deslandes78@gmail.com
        WhatsApp : +50947385663

        CIN CARD NUMBER : 1248795849

        ============================================================
        """

        # ----- Display the info on screen -----
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🇺🇸 USD Account")
            st.code(f"Account: {usd_account}", language="text")
            st.markdown("**SWIFT:** `UBNKHTPPXXX`")
            st.markdown("**Intermediary banks:** Bank of America / BNY / Citibank (USA) or Bank of America London (Europe)")
        with col2:
            st.markdown("#### 🇭🇹 HTG Account")
            st.code(f"Account: {htg_account}", language="text")
            st.markdown("**Routing:** Same as USD – converted to HTG on arrival")
            st.markdown("**Domestic:** SPIH system (no SWIFT)")

        st.divider()
        st.markdown("#### 📥 Download Full Instructions")

        # ----- Two download buttons: English and French -----
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.download_button(
                label="🇬🇧 Download Instructions (English)",
                data=instructions_en,
                file_name=f"UNIBANK_wire_instructions_EN_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_btn2:
            st.download_button(
                label="🇫🇷 Télécharger les instructions (Français)",
                data=instructions_fr,
                file_name=f"UNIBANK_wire_instructions_FR_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.info("✅ The account numbers are read from `st.secrets` – they are **not** stored in the source code.")
        if "⚠️ NOT SET" in usd_account or "⚠️ NOT SET" in htg_account:
            st.warning("⚠️ One or both account numbers are missing from secrets. Please set `UNIBANK_USD_ACCOUNT` and `UNIBANK_HTG_ACCOUNT` in your Streamlit Cloud secrets.")

    # ---- End of tabs ----
    st.divider()
    st.markdown(f"### {t('contact_support')}")
    st.markdown("Email: `deslandes78@gmail.com`  \nWhatsApp: `+50947385663`")
    if st.button(t("logout_owner")):
        st.session_state.owner_space_access = False
        st.rerun()

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
    if st.session_state.call_ringing and st.session_state.call_initiated_time:
        elapsed = time.time() - st.session_state.call_initiated_time
        if elapsed > 30:
            st.session_state.call_ringing = False
            st.session_state.call_initiated_time = None
            st.session_state.call_audio_only = False
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
            <a href="https://helicopter-game-47ahqciazjk4appwt6jvrsr.streamlit.app/" target="_blank" style="display:block; text-align:center; background:#1a5276; color:white; padding:8px; border-radius:8px; text-decoration:none; margin-bottom:5px; font-weight:bold;">
                🚁 Helicopter War Game
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
            # For Haitian Creole, we use a French voice (closest available)
            voice_lang = 'fr'
        else:
            voice_lang = st.session_state.language
        voice_map = {"en":"en-US-JennyNeural","fr":"fr-FR-DeniseNeural","es":"es-ES-ElviraNeural"}
        voice = voice_map.get(voice_lang, "en-US-JennyNeural")
        if st.button(t("listen_explanation"), use_container_width=True):
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
        # ---- GOLDEN STARS TITLE BOX ----
        st.markdown(f"""
        <div class="home-title">
            <div class="golden-stars">
                <span>✦</span>
                <span>✦</span>
                <span>✦</span>
                <span>✦</span>
                <span>✦</span>
                <span>✦</span>
                <span>✦</span>
                <span>✦</span>
            </div>
            <div class="marquee-container">
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
