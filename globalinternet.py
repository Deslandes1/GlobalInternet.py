# ====== FULL app.py (Lakay se Lakay - Mobile Session Persistence) ======
# Lakay se Lakay - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes (Python Developer, Haiti)
# Version: 82.0.0 (Mobile Session Fix + Complete Functions)
# ============================================================
# MOBILE SESSION PERSISTENCE:
# This app now uses localStorage (instead of cookies) to restore
# sessions on mobile devices. See code comments for details.
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

# =======================================================
# ALL APPLICATION FUNCTIONS (must be defined before entry)
# =======================================================

def get_or_create_profile(user_id, email, name):
    """Fetch or create a user profile in the 'profiles' table."""
    if supabase is None:
        return None
    try:
        # Try to get existing profile
        res = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if res.data:
            return res.data[0]
        else:
            # Create new profile
            new_profile = {
                "id": user_id,
                "email": email,
                "full_name": name,
                "bio": "",
                "location": "",
                "avatar_url": "",
                "moncash_phone": "",
                "natcash_phone": "",
                "whatsapp_phone": "",
                "unibank_usd": "",
                "unibank_htg": "",
                "cin": "",
                "is_banned": False,
                "is_private": False,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            res = supabase.table("profiles").insert(new_profile).execute()
            if res.data:
                return res.data[0]
            else:
                return None
    except Exception as e:
        st.session_state.last_error = f"get_or_create_profile: {e}"
        return None

def update_profile(user_id, updates):
    """Update user profile."""
    if supabase is None:
        return False
    try:
        res = supabase.table("profiles").update(updates).eq("id", user_id).execute()
        return bool(res.data)
    except Exception as e:
        st.session_state.last_error = f"update_profile: {e}"
        return False

def ban_user(user_id):
    """Set is_banned = True for a user."""
    if supabase is None:
        return False
    try:
        supabase.table("profiles").update({"is_banned": True}).eq("id", user_id).execute()
        return True
    except Exception:
        return False

def unban_user(user_id):
    """Set is_banned = False."""
    if supabase is None:
        return False
    try:
        supabase.table("profiles").update({"is_banned": False}).eq("id", user_id).execute()
        return True
    except Exception:
        return False

def safe_select_profiles(column, value):
    """Helper to select profiles safely."""
    if supabase is None:
        return []
    try:
        res = supabase.table("profiles").select("*").eq(column, value).execute()
        return res.data if res.data else []
    except Exception:
        return []

def compress_image(image_file, max_size=(800, 800), quality=70):
    """Compress an uploaded image."""
    try:
        img = Image.open(image_file)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        return buf
    except Exception:
        return image_file  # fallback

def upload_avatar(user_id, file):
    """Upload avatar to Supabase Storage."""
    if supabase is None:
        return None
    try:
        bucket = "avatars"
        if not ensure_bucket_exists(bucket):
            return None
        compressed = compress_image(file)
        file_name = f"{user_id}.jpg"
        supabase.storage.from_(bucket).upload(file_name, compressed, {"content-type": "image/jpeg"})
        # Get public URL
        url = supabase.storage.from_(bucket).get_public_url(file_name)
        # Update profile
        update_profile(user_id, {"avatar_url": url})
        return url
    except Exception as e:
        st.session_state.last_error = f"upload_avatar: {e}"
        return None

def upload_post_media(file):
    """Upload media for a post (images/videos)."""
    if supabase is None:
        return None
    try:
        bucket = "post_media"
        ensure_bucket_exists(bucket)
        ext = file.name.split('.')[-1]
        file_name = f"{int(time.time())}_{random.randint(1000,9999)}.{ext}"
        supabase.storage.from_(bucket).upload(file_name, file, {"content-type": file.type})
        return supabase.storage.from_(bucket).get_public_url(file_name)
    except Exception as e:
        st.session_state.last_error = f"upload_post_media: {e}"
        return None

def upload_media_base64(base64_str):
    """Upload a base64 image (e.g. from camera capture)."""
    # Placeholder – implement if needed
    return None

def upload_chat_media(file):
    """Upload media for chat messages."""
    # Similar to upload_post_media
    return upload_post_media(file)

def delete_post(post_id):
    """Delete a post and its media."""
    if supabase is None:
        return False
    try:
        # Get post to delete media
        post = supabase.table("posts").select("media_url").eq("id", post_id).execute()
        if post.data and post.data[0].get("media_url"):
            # Delete from storage (optional)
            pass
        supabase.table("posts").delete().eq("id", post_id).execute()
        # Also delete comments, likes, etc. (cascade if set in DB)
        return True
    except Exception:
        return False

def fetch_exchange_rate():
    """Fetch current USD/HTG exchange rate."""
    try:
        resp = requests.get(EXCHANGE_RATE_API, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("rates", {}).get("HTG", 100)
    except Exception:
        pass
    return 100

def toggle_post_visibility(post_id):
    """Toggle public/private."""
    if supabase is None:
        return False
    try:
        post = supabase.table("posts").select("visibility").eq("id", post_id).execute()
        if post.data:
            current = post.data[0]["visibility"]
            new_val = "public" if current == "private" else "private"
            supabase.table("posts").update({"visibility": new_val}).eq("id", post_id).execute()
            return True
    except Exception:
        pass
    return False

def update_last_active(user_id):
    """Update last_active timestamp."""
    if supabase is None:
        return
    try:
        supabase.table("profiles").update({"last_active": datetime.now().isoformat()}).eq("id", user_id).execute()
    except Exception:
        pass

def is_user_online(user_id):
    """Check if user was active in last 2 minutes."""
    if supabase is None:
        return False
    try:
        res = supabase.table("profiles").select("last_active").eq("id", user_id).execute()
        if res.data:
            last = res.data[0].get("last_active")
            if last:
                last_time = datetime.fromisoformat(last)
                return (datetime.now() - last_time) < timedelta(minutes=2)
    except Exception:
        pass
    return False

def display_avatar_and_followers(user_id):
    """Return avatar URL and friend count."""
    if supabase is None:
        return "", 0
    try:
        res = supabase.table("profiles").select("avatar_url").eq("id", user_id).execute()
        avatar = res.data[0].get("avatar_url", "") if res.data else ""
        # Count friends (accepted friend requests)
        friends_res = supabase.table("friend_requests").select("id").or_(
            f"from_user.eq.{user_id},to_user.eq.{user_id}"
        ).eq("status", "accepted").execute()
        count = len(friends_res.data) if friends_res.data else 0
        return avatar, count
    except Exception:
        return "", 0

def get_user_post_count(user_id):
    """Count posts by user."""
    if supabase is None:
        return 0
    try:
        res = supabase.table("posts").select("id", count="exact").eq("user_id", user_id).execute()
        return res.count if hasattr(res, 'count') else len(res.data)
    except Exception:
        return 0

def load_posts_cached():
    """Load posts with caching."""
    if time.time() - st.session_state._posts_cache_time < 60:
        return st.session_state.posts
    posts = load_posts()
    st.session_state.posts = posts
    st.session_state._posts_cache_time = time.time()
    return posts

def shuffle_feed_posts(posts):
    """Shuffle posts for feed."""
    if not posts:
        return []
    shuffled = posts.copy()
    random.shuffle(shuffled)
    return shuffled

def load_posts():
    """Load all posts (public + friend posts if logged in)."""
    if supabase is None:
        return []
    try:
        # For simplicity, load all public posts and posts from friends (if logged in)
        query = supabase.table("posts").select("*").eq("visibility", "public").order("created_at", desc=True)
        if st.session_state.logged_in and st.session_state.user:
            # Also get private posts from friends (friend list)
            friends = [f["friend_id"] for f in st.session_state.friends]
            if friends:
                private_posts = supabase.table("posts").select("*").eq("visibility", "private").in_("user_id", friends).order("created_at", desc=True).execute()
                if private_posts.data:
                    query = supabase.table("posts").select("*").eq("visibility", "public").order("created_at", desc=True).execute()
                    public_posts = query.data if query.data else []
                    return public_posts + private_posts.data
        res = query.execute()
        return res.data if res.data else []
    except Exception as e:
        st.session_state.last_error = f"load_posts: {e}"
        return []

def load_user_posts(user_id):
    """Load posts by a specific user (respecting privacy)."""
    if supabase is None:
        return []
    try:
        # If viewing own profile, load all; if other, load public only or if friend, private too.
        is_self = st.session_state.logged_in and st.session_state.user and st.session_state.user.id == user_id
        is_friend = any(f["friend_id"] == user_id for f in st.session_state.friends)
        if is_self or is_friend:
            res = supabase.table("posts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        else:
            res = supabase.table("posts").select("*").eq("user_id", user_id).eq("visibility", "public").order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def create_post(user_id, content, media_urls=None, visibility="public"):
    """Create a new post."""
    if supabase is None:
        return None
    try:
        data = {
            "user_id": user_id,
            "content": content,
            "media_url": media_urls[0] if media_urls else None,  # simplify: store first media
            "visibility": visibility,
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("posts").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.session_state.last_error = f"create_post: {e}"
        return None

def update_post(post_id, content):
    """Update post content."""
    if supabase is None:
        return False
    try:
        supabase.table("posts").update({"content": content}).eq("id", post_id).execute()
        return True
    except Exception:
        return False

def toggle_reaction(post_id, user_id):
    """Like/unlike a post."""
    if supabase is None:
        return False
    try:
        # Check if already liked
        res = supabase.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        if res.data:
            # Unlike
            supabase.table("likes").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            return False  # now unliked
        else:
            # Like
            supabase.table("likes").insert({"post_id": post_id, "user_id": user_id}).execute()
            return True  # now liked
    except Exception:
        return False

def share_post(post_id, user_id):
    """Share a post (create a new post referencing original)."""
    if supabase is None:
        return None
    try:
        # Get original post
        orig = supabase.table("posts").select("*").eq("id", post_id).execute()
        if orig.data:
            original = orig.data[0]
            share_content = f"Shared: {original['content']}"
            data = {
                "user_id": user_id,
                "content": share_content,
                "media_url": original.get("media_url"),
                "visibility": original.get("visibility", "public"),
                "created_at": datetime.now().isoformat(),
                "original_post_id": post_id
            }
            res = supabase.table("posts").insert(data).execute()
            return res.data[0] if res.data else None
    except Exception:
        pass
    return None

def load_comments(post_id):
    """Load comments for a post."""
    if supabase is None:
        return []
    try:
        res = supabase.table("comments").select("*").eq("post_id", post_id).order("created_at", asc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def add_comment(post_id, user_id, content):
    """Add a comment to a post."""
    if supabase is None:
        return None
    try:
        data = {
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("comments").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.session_state.last_error = f"add_comment: {e}"
        return None

def delete_comment(comment_id):
    """Delete a comment."""
    if supabase is None:
        return False
    try:
        supabase.table("comments").delete().eq("id", comment_id).execute()
        return True
    except Exception:
        return False

def like_comment(comment_id, user_id):
    """Like a comment."""
    # Similar to toggle_reaction for comments
    if supabase is None:
        return False
    try:
        res = supabase.table("comment_likes").select("id").eq("comment_id", comment_id).eq("user_id", user_id).execute()
        if res.data:
            supabase.table("comment_likes").delete().eq("comment_id", comment_id).eq("user_id", user_id).execute()
            return False
        else:
            supabase.table("comment_likes").insert({"comment_id": comment_id, "user_id": user_id}).execute()
            return True
    except Exception:
        return False

def load_live_sessions():
    """Load all active live sessions."""
    if supabase is None:
        return []
    try:
        res = supabase.table("live_sessions").select("*").eq("status", "live").order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_user_live_sessions(user_id):
    """Get live sessions created by user."""
    if supabase is None:
        return []
    try:
        res = supabase.table("live_sessions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def create_live_session(user_id, title, platform, stream_url=""):
    """Create a new live session."""
    if supabase is None:
        return None
    try:
        data = {
            "user_id": user_id,
            "title": title,
            "platform": platform,
            "stream_url": stream_url,
            "status": "live",
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("live_sessions").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.session_state.last_error = f"create_live_session: {e}"
        return None

def update_live_stream_url(session_id, stream_url):
    """Update stream URL for a live session."""
    if supabase is None:
        return False
    try:
        supabase.table("live_sessions").update({"stream_url": stream_url}).eq("id", session_id).execute()
        return True
    except Exception:
        return False

def end_live_session(session_id):
    """End a live session."""
    if supabase is None:
        return False
    try:
        supabase.table("live_sessions").update({"status": "ended"}).eq("id", session_id).execute()
        return True
    except Exception:
        return False

def get_live_session(session_id):
    """Get details of a live session."""
    if supabase is None:
        return None
    try:
        res = supabase.table("live_sessions").select("*").eq("id", session_id).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def send_gift(session_id, sender_id, amount):
    """Send a gift to a live session."""
    if supabase is None:
        return None
    try:
        data = {
            "session_id": session_id,
            "sender_id": sender_id,
            "amount": amount,
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("gifts").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.session_state.last_error = f"send_gift: {e}"
        return None

def load_gifts_for_session(session_id):
    """Load gifts for a live session."""
    if supabase is None:
        return []
    try:
        res = supabase.table("gifts").select("*").eq("session_id", session_id).order("created_at", asc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def load_notifications(user_id):
    """Load notifications for a user."""
    if supabase is None:
        return []
    try:
        res = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def mark_notification_read(notification_id):
    """Mark a notification as read."""
    if supabase is None:
        return False
    try:
        supabase.table("notifications").update({"read": True}).eq("id", notification_id).execute()
        return True
    except Exception:
        return False

def send_friend_request(from_user, to_user):
    """Send a friend request."""
    if supabase is None:
        return False
    try:
        # Check if already exists
        existing = supabase.table("friend_requests").select("id").or_(
            f"from_user.eq.{from_user},to_user.eq.{to_user}"
        ).eq("status", "pending").execute()
        if existing.data:
            return False
        data = {
            "from_user": from_user,
            "to_user": to_user,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        supabase.table("friend_requests").insert(data).execute()
        return True
    except Exception:
        return False

def respond_friend_request(request_id, accept):
    """Accept or reject a friend request."""
    if supabase is None:
        return False
    try:
        status = "accepted" if accept else "rejected"
        supabase.table("friend_requests").update({"status": status}).eq("id", request_id).execute()
        return True
    except Exception:
        return False

def load_friend_data_cached(user_id):
    """Load friends with caching."""
    # Simple cache in session
    if "friends" in st.session_state and st.session_state.friends:
        return st.session_state.friends
    return load_friend_data(user_id)

def load_friend_data(user_id):
    """Load list of friends (accepted requests)."""
    if supabase is None:
        return []
    try:
        # Get accepted friend requests where user is either from_user or to_user
        res = supabase.table("friend_requests").select("*").or_(
            f"from_user.eq.{user_id},to_user.eq.{user_id}"
        ).eq("status", "accepted").execute()
        friends = []
        if res.data:
            for row in res.data:
                friend_id = row["to_user"] if row["from_user"] == user_id else row["from_user"]
                # Get profile info
                prof = supabase.table("profiles").select("full_name, avatar_url").eq("id", friend_id).execute()
                if prof.data:
                    friends.append({
                        "friend_id": friend_id,
                        "full_name": prof.data[0]["full_name"],
                        "avatar_url": prof.data[0]["avatar_url"]
                    })
        st.session_state.friends = friends
        return friends
    except Exception:
        return []

def search_users_cached(query):
    """Search users with cache."""
    return search_users(query)

def search_users(query):
    """Search for users by full_name."""
    if supabase is None or not query:
        return []
    try:
        res = supabase.table("profiles").select("id, full_name, avatar_url").ilike("full_name", f"%{query}%").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_all_users_cached():
    """Get all users (cached)."""
    return get_all_users()

def get_all_users():
    """Get all profiles."""
    if supabase is None:
        return []
    try:
        res = supabase.table("profiles").select("id, full_name, avatar_url").execute()
        return res.data if res.data else []
    except Exception:
        return []

def send_message(from_user, to_user, message, media_url=None):
    """Send a chat message."""
    if supabase is None:
        return None
    try:
        data = {
            "from_user": from_user,
            "to_user": to_user,
            "message": message,
            "media_url": media_url,
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("messages").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.session_state.last_error = f"send_message: {e}"
        return None

def load_messages(user1, user2):
    """Load messages between two users."""
    if supabase is None:
        return []
    try:
        res = supabase.table("messages").select("*").or_(
            f"and(from_user.eq.{user1},to_user.eq.{user2})"
        ).or_(
            f"and(from_user.eq.{user2},to_user.eq.{user1})"
        ).order("created_at", asc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def start_call(room_id, user_id):
    """Create a call entry."""
    if supabase is None:
        return None
    try:
        data = {
            "room_id": room_id,
            "user1": user_id,
            "status": "ringing",
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("calls").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def end_call(room_id):
    """End a call."""
    if supabase is None:
        return False
    try:
        supabase.table("calls").update({"status": "ended"}).eq("room_id", room_id).execute()
        return True
    except Exception:
        return False

def initiate_call(from_user, to_user):
    """Initiate a call (create room)."""
    room_id = f"room_{from_user}_{to_user}_{int(time.time())}"
    return start_call(room_id, from_user)

def check_call_status(room_id):
    """Check if a call is active."""
    if supabase is None:
        return None
    try:
        res = supabase.table("calls").select("status").eq("room_id", room_id).execute()
        if res.data:
            return res.data[0]["status"]
    except Exception:
        pass
    return None

def ensure_owner_state_table():
    """Create owner_state table if not exists (simulated)."""
    # Supabase doesn't support raw SQL easily; we'll just assume it exists.
    pass

def get_last_seen_signup():
    """Get timestamp of last signup (for owner dashboard)."""
    # Not implemented – placeholder
    return datetime.now().isoformat()

def update_last_seen_signup():
    pass

def get_new_users():
    """Get users created in last 7 days."""
    if supabase is None:
        return []
    try:
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        res = supabase.table("profiles").select("id, full_name, created_at").gte("created_at", week_ago).order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def send_email_notification(to, subject, body):
    """Send email via SMTP."""
    if not SMTP_SERVER or not SMTP_USERNAME or not SMTP_PASSWORD:
        return False
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_FROM or SMTP_USERNAME
        msg["To"] = to
        server = smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT))
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception:
        return False

def create_album(user_id, title, description, visibility="private"):
    """Create a photo album."""
    if supabase is None:
        return None
    try:
        data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "visibility": visibility,
            "created_at": datetime.now().isoformat()
        }
        res = supabase.table("albums").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.session_state.last_error = f"create_album: {e}"
        return None

def upload_album_photos(album_id, files):
    """Upload photos to an album."""
    if supabase is None:
        return []
    urls = []
    try:
        for file in files:
            url = upload_post_media(file)  # reuse
            if url:
                data = {
                    "album_id": album_id,
                    "photo_url": url,
                    "created_at": datetime.now().isoformat()
                }
                supabase.table("album_photos").insert(data).execute()
                urls.append(url)
        return urls
    except Exception:
        return []

def get_user_albums(user_id):
    """Get albums belonging to a user."""
    if supabase is None:
        return []
    try:
        res = supabase.table("albums").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_album_photos(album_id):
    """Get photos in an album."""
    if supabase is None:
        return []
    try:
        res = supabase.table("album_photos").select("*").eq("album_id", album_id).order("created_at", asc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def delete_album(album_id):
    """Delete an album and its photos."""
    if supabase is None:
        return False
    try:
        # Delete photos first
        supabase.table("album_photos").delete().eq("album_id", album_id).execute()
        supabase.table("albums").delete().eq("id", album_id).execute()
        return True
    except Exception:
        return False

def toggle_album_visibility(album_id):
    """Toggle public/private for an album."""
    if supabase is None:
        return False
    try:
        album = supabase.table("albums").select("visibility").eq("id", album_id).execute()
        if album.data:
            current = album.data[0]["visibility"]
            new_val = "public" if current == "private" else "private"
            supabase.table("albums").update({"visibility": new_val}).eq("id", album_id).execute()
            return True
    except Exception:
        pass
    return False

def get_all_albums():
    """Get all public albums (for owner)."""
    if supabase is None:
        return []
    try:
        res = supabase.table("albums").select("*").eq("visibility", "public").order("created_at", desc=True).execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_active_video_calls():
    """Get active calls (for owner)."""
    if supabase is None:
        return []
    try:
        res = supabase.table("calls").select("*").eq("status", "ringing").execute()
        return res.data if res.data else []
    except Exception:
        return []

def get_network_status():
    """Return network status info."""
    return {
        "signal": "Strong",
        "latency": f"{random.randint(20, 80)}ms",
        "quality": "Excellent"
    }

def get_uptime():
    """Get app uptime."""
    return str(timedelta(seconds=int(time.time() - st.session_state.connection_time)))

def sign_up_email(email, password, full_name):
    """Sign up a new user with email."""
    if supabase is None:
        return None, "Supabase not available"
    try:
        # Use Supabase auth signup
        resp = supabase.auth.sign_up({"email": email, "password": password})
        if resp.user:
            # Create profile
            get_or_create_profile(resp.user.id, email, full_name)
            return resp.user, None
        else:
            return None, "Signup failed"
    except Exception as e:
        return None, str(e)

def reset_password_email(email):
    """Send password reset email."""
    if supabase is None:
        return False
    try:
        supabase.auth.reset_password_for_email(email)
        return True
    except Exception:
        return False

def format_phone(phone):
    """Remove non-numeric characters."""
    return re.sub(r'\D', '', phone)

def send_phone_otp(phone):
    """Send OTP to phone (simulated)."""
    # In production, integrate with SMS API
    otp = ''.join(random.choices(string.digits, k=6))
    st.session_state.phone_otp = otp
    st.info(f"📱 OTP sent to {phone}: {otp} (simulated)")
    return True

def verify_phone_otp(phone, otp):
    """Verify OTP."""
    return otp == st.session_state.get("phone_otp")

def logout():
    """Log out the user."""
    set_cookie("sb_refresh_token", "", -1)  # clears both
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.refresh_token = None
    st.session_state.friends = []
    st.session_state.notifications = []
    st.rerun()

def generate_audio(text, lang="en"):
    """Generate TTS audio using edge_tts."""
    try:
        voice = "en-US-JennyNeural" if lang == "en" else "fr-FR-DeniseNeural"
        communicate = edge_tts.Communicate(text, voice)
        audio_data = b""
        for chunk in asyncio.run(communicate.stream()):
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception:
        return None

def play_audio(audio_data):
    """Play audio in Streamlit."""
    if audio_data:
        st.audio(audio_data, format="audio/mp3")

def log_in_email(email, password):
    """Log in with email/password."""
    if supabase is None:
        return None, "Supabase not available"
    try:
        resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if resp.user:
            profile = get_or_create_profile(resp.user.id, email, resp.user.email)
            if profile and profile.get("is_banned"):
                return None, "Account banned"
            # Set session
            st.session_state.logged_in = True
            st.session_state.user = resp.user
            st.session_state.refresh_token = resp.session.refresh_token
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            # Set cookie/localStorage
            set_cookie("sb_refresh_token", resp.session.refresh_token, 30)
            # Load data
            st.session_state.posts = load_posts()
            st.session_state.live_sessions = load_live_sessions()
            load_friend_data(resp.user.id)
            st.session_state.notifications = load_notifications(resp.user.id)
            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
            return resp.user, None
        else:
            return None, "Invalid credentials"
    except Exception as e:
        return None, str(e)

def render_top_icons():
    """Render top navigation icons."""
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
    with col1:
        if st.button("📡 Feed", key="nav_feed"):
            st.session_state.current_page = "feed"
            st.rerun()
    with col2:
        if st.button("👥 Chat", key="nav_chat"):
            st.session_state.current_page = "friends_chat"
            st.rerun()
    with col3:
        if st.button("🛰️ Map", key="nav_map"):
            st.session_state.current_page = "satellite_map"
            st.run()
    with col4:
        if st.button("⚽ World Cup", key="nav_wc"):
            st.session_state.current_page = "worldcup"
            st.rerun()
    with col5:
        if st.button("👤 Profile", key="nav_profile"):
            st.session_state.current_page = "profile"
            st.rerun()
    with col6:
        if st.button("🕊️ Owner", key="nav_owner"):
            st.session_state.current_page = "owner_space"
            st.rerun()
    with col7:
        if st.button("🎬 Movies", key="nav_movies"):
            st.session_state.current_page = "movies"
            st.rerun()
    with col8:
        if st.button("🚪 Logout", key="nav_logout"):
            logout()

def login_interface():
    """Display login/signup page."""
    st.markdown(f"<h1 class='haiti-symbol'>🏠 Lakay se Lakay</h1>", unsafe_allow_html=True)
    st.markdown(f"<div class='owner-name'>🇭🇹 {t('home_subtitle')}</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs([t("login_title"), t("signup_title"), t("forgot_password")])
    with tab1:
        email = st.text_input(t("email"), key="login_email")
        password = st.text_input(t("password"), type="password", key="login_password")
        if st.button(t("login_button"), key="login_btn"):
            if email and password:
                user, err = log_in_email(email, password)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Logged in!")
                    st.rerun()
            else:
                st.warning("Please enter email and password.")
    with tab2:
        new_email = st.text_input(t("email"), key="signup_email")
        new_pass = st.text_input(t("password"), type="password", key="signup_pass")
        full_name = st.text_input(t("full_name"), key="signup_name")
        if st.button(t("signup_button"), key="signup_btn"):
            if new_email and new_pass and full_name:
                user, err = sign_up_email(new_email, new_pass, full_name)
                if err:
                    st.error(err)
                else:
                    st.success("✅ Account created! Please log in.")
            else:
                st.warning("Please fill all fields.")
    with tab3:
        reset_email = st.text_input(t("email"), key="reset_email")
        if st.button(t("send_reset_link"), key="reset_btn"):
            if reset_email:
                if reset_password_email(reset_email):
                    st.success("✅ Reset link sent to your email.")
                else:
                    st.error("Failed to send reset link.")
            else:
                st.warning("Enter your email.")

def display_media_item(url):
    """Display an image or video based on URL."""
    if not url:
        return
    ext = url.split('.')[-1].lower()
    if ext in ['mp4', 'mov', 'avi', 'webm']:
        st.video(url)
    else:
        st.image(url)

def groq_search(query):
    """Search using Groq API (simulated)."""
    if not GROQ_API_KEY:
        st.warning(t("groq_api_key_missing"))
        return []
    # For demo, return dummy results
    return [
        {"title": "Python Programming", "url": "https://example.com/python", "description": "Learn Python basics."},
        {"title": "Haitian History", "url": "https://example.com/haiti", "description": "Explore Haiti's rich history."}
    ]

def render_discover_section():
    """Render discovery section (books/videos)."""
    st.subheader(t("search_groq"))
    query = st.text_input(t("groq_search_placeholder"), key="groq_search_input")
    if st.button("🔍 Search"):
        if query:
            results = groq_search(query)
            st.session_state.groq_search_results = results
    if st.session_state.groq_search_results:
        for item in st.session_state.groq_search_results:
            with st.container():
                st.markdown(f"**{item['title']}**")
                st.write(item['description'])
                st.markdown(f"[{t('open_in_new_tab')}]({item['url']})")
                st.divider()

def render_feed():
    """Render the main feed."""
    st.subheader(t("feed"))
    # Search
    search_term = st.text_input(t("search_posts"), key="feed_search")
    # Create post
    with st.expander(t("create_post")):
        content = st.text_area(t("caption_placeholder"), key="post_content")
        media_files = st.file_uploader(t("add_media"), accept_multiple_files=True, type=["png","jpg","jpeg","gif","mp4","mov","avi"])
        visibility = st.radio(t("visibility"), [t("public"), t("private")], index=0)
        if st.button(t("post")):
            if content or media_files:
                media_urls = []
                for f in media_files:
                    url = upload_post_media(f)
                    if url:
                        media_urls.append(url)
                post = create_post(st.session_state.user.id, content, media_urls, visibility.lower())
                if post:
                    st.success("✅ Post created!")
                    st.session_state.posts = load_posts()
                    st.rerun()
                else:
                    st.error("Failed to create post.")
    # Feed posts
    posts = load_posts_cached()
    if search_term:
        posts = [p for p in posts if search_term.lower() in p.get('content', '').lower()]
    if not posts:
        st.info("No posts yet. Be the first to post!")
    else:
        for post in posts:
            with st.container():
                st.markdown(f"<div class='post-card'>", unsafe_allow_html=True)
                # Post header
                user_id = post['user_id']
                avatar, _ = display_avatar_and_followers(user_id)
                col1, col2 = st.columns([1, 4])
                with col1:
                    if avatar:
                        st.image(avatar, width=50)
                    else:
                        st.write("👤")
                with col2:
                    # Get user name
                    prof = safe_select_profiles("id", user_id)
                    name = prof[0]['full_name'] if prof else "Unknown"
                    st.markdown(f"**{name}**")
                    st.caption(post.get('created_at', ''))
                # Content
                st.markdown(post.get('content', ''))
                if post.get('media_url'):
                    display_media_item(post['media_url'])
                # Actions
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    liked = any(l['user_id'] == st.session_state.user.id for l in post.get('likes', []))
                    if st.button("❤️" if liked else "🤍", key=f"like_{post['id']}"):
                        toggle_reaction(post['id'], st.session_state.user.id)
                        st.rerun()
                with col2:
                    if st.button("💬 Comment", key=f"comment_{post['id']}"):
                        st.session_state.replying_to[post['id']] = not st.session_state.replying_to.get(post['id'], False)
                with col3:
                    if st.button("🔗 Share", key=f"share_{post['id']}"):
                        share_post(post['id'], st.session_state.user.id)
                        st.rerun()
                with col4:
                    if post['user_id'] == st.session_state.user.id:
                        if st.button("🗑️ Delete", key=f"delete_{post['id']}"):
                            delete_post(post['id'])
                            st.rerun()
                # Comments
                if st.session_state.replying_to.get(post['id'], False):
                    with st.expander(t("comments"), expanded=True):
                        comments = load_comments(post['id'])
                        for c in comments:
                            c_user = safe_select_profiles("id", c['user_id'])
                            c_name = c_user[0]['full_name'] if c_user else "Unknown"
                            st.markdown(f"**{c_name}** : {c['content']}")
                            st.caption(c['created_at'])
                        new_comment = st.text_input(t("your_reply"), key=f"new_comment_{post['id']}")
                        if st.button(t("post_reply"), key=f"reply_btn_{post['id']}"):
                            if new_comment:
                                add_comment(post['id'], st.session_state.user.id, new_comment)
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

def render_user_profile(user_id):
    """Render a user's profile."""
    if supabase is None:
        return
    profile = safe_select_profiles("id", user_id)
    if not profile:
        st.error("User not found.")
        return
    prof = profile[0]
    is_self = st.session_state.user and st.session_state.user.id == user_id
    is_friend = any(f["friend_id"] == user_id for f in st.session_state.friends)
    st.markdown(f"<h2>{prof.get('full_name', 'User')}</h2>", unsafe_allow_html=True)
    if prof.get('avatar_url'):
        st.image(prof['avatar_url'], width=150)
    else:
        st.write("👤 No avatar")
    st.write(f"**Bio:** {prof.get('bio', '')}")
    st.write(f"**Location:** {prof.get('location', '')}")
    st.write(f"**Member since:** {prof.get('created_at', '')}")
    if is_self:
        st.write("👤 This is you")
    elif is_friend:
        st.write("🤝 Friends")
    else:
        if st.button("➕ Add Friend", key=f"add_friend_{user_id}"):
            send_friend_request(st.session_state.user.id, user_id)
            st.success("Friend request sent!")
    if is_self or is_friend or not prof.get('is_private'):
        posts = load_user_posts(user_id)
        if posts:
            st.subheader(t("posts_count"))
            for p in posts:
                st.markdown(f"<div class='post-card'>", unsafe_allow_html=True)
                st.write(p.get('content', ''))
                if p.get('media_url'):
                    display_media_item(p['media_url'])
                st.caption(p.get('created_at', ''))
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info(t("private_profile"))

def render_friends_page():
    """Render friends & chat page."""
    st.subheader(t("friends_chat"))
    # Find users
    with st.expander(t("find_users")):
        search_term = st.text_input(t("search_by_name"), key="friend_search")
        if search_term:
            users = search_users(search_term)
            for u in users:
                if u['id'] != st.session_state.user.id:
                    col1, col2, col3 = st.columns([2,1,1])
                    with col1:
                        st.write(u['full_name'])
                    with col2:
                        if st.button(t("view_profile"), key=f"view_{u['id']}"):
                            st.session_state.viewing_profile = u['id']
                    with col3:
                        if st.button(t("add_friend"), key=f"add_{u['id']}"):
                            send_friend_request(st.session_state.user.id, u['id'])
                            st.success("Request sent!")
    # Friend requests
    st.subheader(t("friend_requests"))
    requests = supabase.table("friend_requests").select("*").eq("to_user", st.session_state.user.id).eq("status", "pending").execute()
    if requests.data:
        for req in requests.data:
            from_user = safe_select_profiles("id", req['from_user'])
            name = from_user[0]['full_name'] if from_user else "Unknown"
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(name)
            with col2:
                if st.button(t("accept"), key=f"acc_{req['id']}"):
                    respond_friend_request(req['id'], True)
                    st.rerun()
                if st.button(t("reject"), key=f"rej_{req['id']}"):
                    respond_friend_request(req['id'], False)
                    st.rerun()
    else:
        st.info("No friend requests.")
    # Friends list
    st.subheader(t("your_friends"))
    if st.session_state.friends:
        for f in st.session_state.friends:
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                st.write(f['full_name'])
            with col2:
                if st.button(t("chat"), key=f"chat_{f['friend_id']}"):
                    st.session_state.selected_chat = f['friend_id']
            with col3:
                if st.button(t("call"), key=f"call_{f['friend_id']}"):
                    initiate_call(st.session_state.user.id, f['friend_id'])
                    st.session_state.call_room = f"room_{st.session_state.user.id}_{f['friend_id']}"
                    st.info("Call initiated.")
    else:
        st.info(t("no_friends"))
    # Chat area
    if st.session_state.selected_chat:
        st.subheader("💬 Chat")
        other = st.session_state.selected_chat
        other_prof = safe_select_profiles("id", other)
        other_name = other_prof[0]['full_name'] if other_prof else "User"
        st.write(f"Chatting with {other_name}")
        messages = load_messages(st.session_state.user.id, other)
        for msg in messages:
            if msg['from_user'] == st.session_state.user.id:
                st.markdown(f"**You:** {msg['message']}")
            else:
                st.markdown(f"**{other_name}:** {msg['message']}")
            if msg.get('media_url'):
                display_media_item(msg['media_url'])
            st.caption(msg['created_at'])
        new_msg = st.text_input("Type message...", key="chat_input")
        if st.button(t("send_message")):
            if new_msg:
                send_message(st.session_state.user.id, other, new_msg)
                st.rerun()

def render_map():
    """Satellite map placeholder."""
    st.subheader(t("satellite_map"))
    st.info("🌍 Interactive map coming soon. For now, enjoy this satellite view of Haiti.")
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Haiti_satellite_2010.jpg/800px-Haiti_satellite_2010.jpg", use_container_width=True)

def render_worldcup():
    """World Cup live stream placeholder."""
    st.subheader(t("worldcup"))
    st.info("⚽ Watch live World Cup matches here when available.")
    st.video("https://www.youtube.com/embed/dQw4w9WgXcQ")  # placeholder

def render_profile():
    """Render own profile."""
    if st.session_state.user:
        render_user_profile(st.session_state.user.id)
    # Edit profile
    with st.expander(t("edit_profile")):
        if st.session_state.profile:
            prof = st.session_state.profile
            name = st.text_input(t("full_name"), prof.get('full_name', ''))
            bio = st.text_area(t("bio"), prof.get('bio', ''))
            location = st.text_input(t("location"), prof.get('location', ''))
            moncash = st.text_input(t("moncash_phone"), prof.get('moncash_phone', ''))
            natcash = st.text_input(t("natcash_phone"), prof.get('natcash_phone', ''))
            whatsapp = st.text_input(t("whatsapp_phone"), prof.get('whatsapp_phone', ''))
            unibank_usd = st.text_input(t("unibank_usd_account"), prof.get('unibank_usd', ''))
            unibank_htg = st.text_input(t("unibank_htg_account"), prof.get('unibank_htg', ''))
            cin = st.text_input(t("cin_number"), prof.get('cin', ''))
            avatar = st.file_uploader(t("change_picture"), type=["png","jpg","jpeg"])
            if st.button(t("save_changes")):
                updates = {
                    "full_name": name,
                    "bio": bio,
                    "location": location,
                    "moncash_phone": moncash,
                    "natcash_phone": natcash,
                    "whatsapp_phone": whatsapp,
                    "unibank_usd": unibank_usd,
                    "unibank_htg": unibank_htg,
                    "cin": cin
                }
                if avatar:
                    url = upload_avatar(st.session_state.user.id, avatar)
                    if url:
                        updates["avatar_url"] = url
                if update_profile(st.session_state.user.id, updates):
                    st.success("✅ Profile updated!")
                    st.session_state.profile = get_or_create_profile(st.session_state.user.id, st.session_state.user.email, name)
                    st.rerun()
                else:
                    st.error("Failed to update profile.")

def owner_space():
    """Owner dashboard."""
    if not st.session_state.owner_space_access:
        password = st.text_input("Enter Owner Space Password", type="password")
        if st.button("Unlock"):
            if password == OWNSPACE_PASSWORD:
                st.session_state.owner_space_access = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        return
    st.subheader(t("owner_dashboard"))
    # New users
    st.metric(t("new_users"), len(get_new_users()))
    # Banned users
    banned = safe_select_profiles("is_banned", True)
    st.write(f"🚫 Banned users: {len(banned)}")
    # User management
    with st.expander(t("user_management")):
        user_list = get_all_users()
        for u in user_list:
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                st.write(u['full_name'])
            with col2:
                if u.get('is_banned'):
                    if st.button(t("unban_user"), key=f"unban_{u['id']}"):
                        unban_user(u['id'])
                        st.rerun()
                else:
                    if st.button(t("ban_user"), key=f"ban_{u['id']}"):
                        ban_user(u['id'])
                        st.rerun()
    # Post moderation
    with st.expander(t("post_moderation")):
        all_posts = load_posts()
        for p in all_posts[:10]:
            st.write(p['content'])
            if st.button("🗑️ Delete", key=f"mod_del_{p['id']}"):
                delete_post(p['id'])
                st.rerun()
    # Gifts
    with st.expander(t("gift_management")):
        gifts = supabase.table("gifts").select("*").execute()
        st.write(f"Total gifts: {len(gifts.data) if gifts.data else 0}")
    # Logout owner
    if st.button(t("logout_owner")):
        st.session_state.owner_space_access = False
        st.rerun()

def render_video_call():
    """Video call using Jitsi."""
    st.subheader(t("video_call"))
    st.info(t("demo_note"))
    room = st.text_input(t("room_id"), value=f"lakay_{st.session_state.user.id}_{int(time.time())}")
    if st.button(t("start_video_call")):
        # Redirect to Jitsi
        jitsi_url = f"https://{JITSI_DOMAIN}/{room}"
        st.markdown(f"[{t('open_in_new_tab')}]({jitsi_url})")
        st.components.v1.iframe(f"https://{JITSI_DOMAIN}/{room}", width=800, height=600)

def render_live_page():
    """Live streaming page."""
    st.subheader("🔴 Live Streaming")
    # Check for active live sessions
    live_sessions = load_live_sessions()
    if live_sessions:
        for session in live_sessions:
            if st.button(f"📺 {session['title']}", key=f"live_{session['id']}"):
                st.session_state.viewing_live = session['id']
    # Create live session
    with st.expander(t("go_live")):
        title = st.text_input(t("live_title"))
        platform = st.selectbox(t("select_platform"), ["YouTube", "Facebook", "Twitch", "Other"])
        stream_url = st.text_input(t("set_stream_url"), placeholder=t("paste_url"))
        if st.button(t("create_live_session")):
            if title and stream_url:
                session = create_live_session(st.session_state.user.id, title, platform, stream_url)
                if session:
                    st.success("✅ Live session created! Share the link below.")
                    st.write(f"🔗 {session['shareable_link']}")
                    st.session_state.live_sessions = load_live_sessions()
                    st.rerun()
                else:
                    st.error("Failed to create live session.")
    # View live
    if st.session_state.viewing_live:
        session = get_live_session(st.session_state.viewing_live)
        if session and session['status'] == 'live':
            st.subheader(f"📺 {session['title']}")
            if session['stream_url']:
                st.video(session['stream_url'])
            else:
                st.info("Stream URL not set.")
            # Chat/gifts
            gifts = load_gifts_for_session(session['id'])
            if gifts:
                st.write(t("live_chat_gifts"))
                for g in gifts:
                    st.write(f"🎁 {g['amount']} HTG")
            # Send gift
            amount = st.number_input(t("send_gift"), min_value=1, max_value=1000, value=10)
            if st.button(t("send_gift")):
                send_gift(session['id'], st.session_state.user.id, amount)
                st.success("Gift sent!")
            if st.button(t("end_live_session")):
                end_live_session(session['id'])
                st.session_state.viewing_live = None
                st.rerun()
        else:
            st.info("This session has ended.")
            st.session_state.viewing_live = None

def render_movies():
    """Movies page."""
    st.subheader(t("movies"))
    st.info("🎬 Watch movies and videos here.")
    # Embed a movie player (placeholder)
    st.video("https://www.youtube.com/embed/dQw4w9WgXcQ")

def main_app():
    """Main app after login."""
    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Haiti_satellite_2010.jpg/800px-Haiti_satellite_2010.jpg", use_container_width=True)
        st.markdown(f"**{t('logged_in_as')}** {st.session_state.profile.get('full_name', 'User')}")
        if st.button("🔄 Refresh Feed"):
            st.cache_data.clear()
            st.session_state.posts = load_posts()
            st.rerun()
        st.divider()
        # Language selector
        lang = st.selectbox("🌐 Language", ["en", "fr", "es", "ht"], index=["en","fr","es","ht"].index(st.session_state.language))
        if lang != st.session_state.language:
            st.session_state.language = lang
            st.rerun()
        st.divider()
        # App explanation
        if st.button(t("listen_explanation")):
            audio = generate_audio(t("app_explanation"), lang)
            if audio:
                play_audio(audio)
        # System health
        with st.expander(t("system_health")):
            status = get_network_status()
            st.metric(t("signal"), status['signal'])
            st.metric(t("latency"), status['latency'])
            st.metric(t("quality"), status['quality'])
            st.metric(t("uptime"), get_uptime())
            st.success(t("encrypted"))
        st.divider()
        render_top_icons()
        st.divider()
        # Security badge
        st.markdown(f"<div class='health-text'>{t('security_badge')}</div>", unsafe_allow_html=True)
        st.caption(t("security_caption"))
    # Main content based on page
    if st.session_state.current_page == "feed":
        render_feed()
    elif st.session_state.current_page == "friends_chat":
        render_friends_page()
    elif st.session_state.current_page == "satellite_map":
        render_map()
    elif st.session_state.current_page == "worldcup":
        render_worldcup()
    elif st.session_state.current_page == "profile":
        render_profile()
    elif st.session_state.current_page == "owner_space":
        owner_space()
    elif st.session_state.current_page == "video_call":
        render_video_call()
    elif st.session_state.current_page == "movies":
        render_movies()
    else:
        render_feed()
    # Live section always visible at bottom?
    with st.expander("🔴 Live Streams"):
        render_live_page()

# ====== RESTORE SESSION (MOBILE PERSISTENCE) ======
# This block runs after all functions are defined.
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
                load_friend_data(user.user.id)
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

# ====== ENTRY ======
if __name__ == "__main__":
    if st.session_state.logged_in:
        st.markdown("""
        <div class="home-title">
            <div class="golden-stars">
                <span>✦</span><span>✦</span><span>✦</span><span>✦</span>
                <span>✦</span><span>✦</span><span>✦</span><span>✦</span>
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
