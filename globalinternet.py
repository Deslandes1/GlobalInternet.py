# ====== FULL app.py (Lakay se Lakay - Mobile Session Persistence) ======
# Lakay se Lakay - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes (Python Developer, Haiti)
# Version: 81.0.0 (Mobile Session Fix + Documentation)
# ============================================================
# MOBILE SESSION PERSISTENCE:
# This app now uses localStorage (instead of cookies) to restore
# sessions on mobile devices. See MOBILE_SESSION_PERSISTENCE.md
# for full explanation and code details.
# ============================================================
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
st.set_page_config(page_title="Lakay se Lakay", page_icon="🏠", layout="centered")

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

# --- Secrets ---
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

GLOBAL_SHIELD_API_KEY = st.secrets.get("GLOBAL_SHIELD_API_KEY")
GLOBAL_SHIELD_ACTIVE = bool(GLOBAL_SHIELD_API_KEY)

GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

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
if "groq_search_results" not in st.session_state:
    st.session_state.groq_search_results = []
if "groq_selected_item" not in st.session_state:
    st.session_state.groq_selected_item = None
if "groq_search_query" not in st.session_state:
    st.session_state.groq_search_query = ""
if "viewing_album" not in st.session_state:
    st.session_state.viewing_album = None
if "creating_album" not in st.session_state:
    st.session_state.creating_album = False
if "call_initiated_time" not in st.session_state:
    st.session_state.call_initiated_time = None
if "call_target_user" not in st.session_state:
    st.session_state.call_target_user = None
if "call_ringing" not in st.session_state:
    st.session_state.call_ringing = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "feed"
if "feed_search_term" not in st.session_state:
    st.session_state.feed_search_term = ""
if "_session_restored" not in st.session_state:
    st.session_state._session_restored = False
if "_last_token_refresh" not in st.session_state:
    st.session_state._last_token_refresh = 0
if "_cookie_read" not in st.session_state:
    st.session_state._cookie_read = False
if "_posts_cache_time" not in st.session_state:
    st.session_state._posts_cache_time = 0

# ---- NAVIGATION FROM QUERY PARAMS ----
if "page" in st.query_params:
    page_param = st.query_params["page"]
    valid_pages = ["feed", "friends_chat", "satellite_map", "worldcup", "profile", "video_call", "owner_space", "movies"]
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
        "movies": "🎬 Movies",
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
        "cin_number": "CIN Card Number"
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
        "movies": "🎬 Films",
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
        "cin_number": "Numéro de carte CIN"
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
        "movies": "🎬 Películas",
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
        "cin_number": "Número de CIN"
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
        "movies": "🎬 Sinema",
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
        "cin_number": "Nimewo kat CIN"
    }
}

def t(key):
    return LANG.get(st.session_state.language, LANG["en"]).get(key, key)

# ====== COOKIE HELPERS (UPDATED FOR MOBILE SESSION PERSISTENCE) ======
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
        document.cookie = name + "=" + (value || "")  + expires + "; path=/; Secure; SameSite=None";
        localStorage.setItem(name, value);
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
    var refreshToken = localStorage.getItem('sb_refresh_token');
    if (!refreshToken) {
        refreshToken = getCookie('sb_refresh_token');
    }
    if (refreshToken) {
        var url = new URL(window.location.href);
        if (!url.searchParams.has('cookie_sb_refresh_token')) {
            url.searchParams.set('cookie_sb_refresh_token', refreshToken);
            window.location.href = url.toString();
        }
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

# --- Lazy token refresh ---
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
    .dove-symbol { font-size: 7rem; display: block; margin: 0 auto; color: #ffffff; text-shadow: 0 0 20px rgba(0,0,0,0.1); }
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

# ====== REST OF THE APP (FUNCTIONS, RENDERING, ETC.) ======
# The following functions are the same as in your original app.
# They are not repeated here for brevity.
# IMPORTANT: In your actual app.py, you must include all the remaining
# functions: get_or_create_profile, update_profile, ban_user, unban_user,
# safe_select_profiles, compress_image, upload_avatar, upload_post_media,
# upload_media_base64, upload_chat_media, delete_post, fetch_exchange_rate,
# toggle_post_visibility, update_last_active, is_user_online,
# display_avatar_and_followers, get_user_post_count, load_posts_cached,
# shuffle_feed_posts, load_posts, load_user_posts, create_post,
# update_post, toggle_reaction, share_post, load_comments, add_comment,
# delete_comment, like_comment, load_live_sessions, get_user_live_sessions,
# create_live_session, update_live_stream_url, end_live_session,
# get_live_session, send_gift, load_gifts_for_session, load_notifications,
# mark_notification_read, send_friend_request, respond_friend_request,
# load_friend_data_cached, load_friend_data, search_users_cached,
# search_users, get_all_users_cached, get_all_users, send_message,
# load_messages, start_call, end_call, initiate_call, check_call_status,
# ensure_owner_state_table, get_last_seen_signup, update_last_seen_signup,
# get_new_users, send_email_notification, create_album, upload_album_photos,
# get_user_albums, get_album_photos, delete_album, toggle_album_visibility,
# get_all_albums, get_active_video_calls, get_network_status, get_uptime,
# sign_up_email, reset_password_email, format_phone, send_phone_otp,
# verify_phone_otp, logout, generate_audio, play_audio, log_in_email,
# render_top_icons, login_interface, display_media_item, groq_search,
# render_discover_section, render_feed, render_user_profile,
# render_friends_page, render_map, render_worldcup, render_profile,
# owner_space, render_video_call, render_live_page, render_movies,
# main_app.

# The rest of your app's code (the long sections) must be copied from your original file.
# They are not included here to keep this answer focused on the fix.

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
