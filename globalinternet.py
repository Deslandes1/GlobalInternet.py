# ====== FULL app.py (no global password, clean login page) ======
# Home Sweet Home - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes (Python Developer, Haiti)
# Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
#                Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
# Version: 77.8.15 (Removed global password protection)
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

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Home Sweet Home", page_icon="🏠", layout="wide")

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

# ====== ENSURE STORAGE BUCKETS EXIST (only called on upload) ======
def ensure_bucket_exists(bucket_name, public=True):
    if supabase is None:
        return False

    supabase_key = st.secrets.get("SUPABASE_KEY")
    supabase_url = st.secrets.get("SUPABASE_URL")
    if not supabase_key or not supabase_url:
        st.error("❌ Supabase credentials missing. Cannot manage buckets.")
        return False

    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }

    check_url = f"{supabase_url}/storage/v1/bucket/{bucket_name}"
    try:
        check_resp = requests.get(check_url, headers=headers)
        if check_resp.status_code == 200:
            return True
        elif check_resp.status_code == 404:
            create_url = f"{supabase_url}/storage/v1/bucket"
            payload = {"name": bucket_name, "public": public}
            create_resp = requests.post(create_url, json=payload, headers=headers)
            if create_resp.status_code == 200:
                st.success(f"✅ Created storage bucket: {bucket_name}")
                return True
            else:
                if "already exists" in create_resp.text:
                    return True
                st.error(f"❌ Failed to create bucket '{bucket_name}': {create_resp.text}\nPlease create it manually in Supabase Dashboard → Storage.")
                return False
        else:
            st.error(f"❌ Error checking bucket '{bucket_name}': {check_resp.text}\nPlease create it manually.")
            return False
    except Exception as e:
        st.error(f"❌ Network error while checking bucket '{bucket_name}': {e}")
        return False

# --- Secrets for owner only ---
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")
MONCASH_NUM = st.secrets.get("MONCASH_NUM", "(509)-47385663")
UNIBANK_ACCOUNT = st.secrets.get("UNIBANK_ACCOUNT", "105-2016-16594727")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "https://your-backend.com")
BACKEND_API_KEY = st.secrets.get("BACKEND_API_KEY", "")
EXCHANGE_RATE_API = st.secrets.get("EXCHANGE_RATE_API", "https://api.exchangerate-api.com/v4/latest/USD")

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

# ====== LANGUAGE DICTIONARY (4 LANGUAGES: EN, FR, ES, HT) ======
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
        "phone_method": "Phone (OTP)",
        "email_method": "Email",
        "phone_number": "Phone number (digits only, e.g., 50947385663)",
        "send_otp": "📲 Send OTP",
        "enter_otp": "Enter 6-digit OTP code",
        "verify_login": "✅ Verify & Login",
        "back_resend": "← Back / Resend OTP",
        "feed": "📡 Feed",
        "friends_chat": "👥 Friends & Chat",
        "satellite_map": "🛰️ Satellite Map",
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
        "total_gifts": "Total Gifts Received",
        "gifts_sent_to": "Gifts will be sent to your MonCash",
        "write_comment": "Write a comment...",
        "send": "Send",
        "back_to_feed": "Back to Feed",
        "create_post": "Create a post",
        "caption_placeholder": "Write something... or paste a video link",
        "add_media": "Add images or videos (optional)",
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
        # Home page translations
        "home_title": "🏠 Home Sweet Home",
        "home_haiti": "HAITI",
        "home_subtitle": "Your Haitian social media platform"
    },
    "fr": {
        "login_title": "Connexion",
        "signup_title": "S'inscrire",
        "forgot_password": "Mot de passe oublié",
        "email": "Email",
        "password": "Mot de passe",
        "full_name": "Nom complet",
        "remember_me": "Se souvenir de moi",
        "login_button": "🚀 Connexion",
        "signup_button": "📝 Inscription",
        "send_reset_link": "Envoyer le lien de réinitialisation",
        "phone_method": "Téléphone (OTP)",
        "email_method": "Email",
        "phone_number": "Numéro de téléphone (chiffres uniquement, ex: 50947385663)",
        "send_otp": "📲 Envoyer OTP",
        "enter_otp": "Entrez le code OTP à 6 chiffres",
        "verify_login": "✅ Vérifier et se connecter",
        "back_resend": "← Retour / Renvoyer OTP",
        "feed": "📡 Fil d'actualité",
        "friends_chat": "👥 Amis et Chat",
        "satellite_map": "🛰️ Carte satellite",
        "profile": "👤 Profil",
        "owner_space": "🕊️ Espace propriétaire",
        "logout": "🚪 Déconnexion",
        "system_health": "🛡️ État du système",
        "signal": "📡 Signal",
        "latency": "⏱️ Latence",
        "quality": "📊 Qualité",
        "uptime": "⏰ Temps de fonctionnement",
        "encrypted": "🔒 Statut : CHIFFRÉ",
        "compensation": "💰 Compensation",
        "logged_in_as": "👤 Connecté en tant que",
        "go_live": "Passer en direct",
        "external_platform": "Plateforme externe (YouTube/Facebook/Twitch)",
        "in_app_camera": "Caméra intégrée",
        "select_platform": "Choisir la plateforme",
        "live_title": "Titre du direct",
        "create_live_session": "Créer une session en direct",
        "you_are_live": "🔴 Vous êtes en direct !",
        "end_live_session": "Terminer le direct",
        "set_stream_url": "📹 Définir l'URL du flux",
        "paste_url": "Collez l'URL de votre flux en direct",
        "update_url": "Mettre à jour l'URL",
        "shareable_link": "Lien partageable",
        "live_chat_gifts": "Chat en direct et cadeaux",
        "send_gift": "🎁 Envoyer un cadeau",
        "add_moncash": "Ajoutez votre numéro MonCash dans votre profil pour envoyer des cadeaux.",
        "total_gifts": "Total des cadeaux reçus",
        "gifts_sent_to": "Les cadeaux seront envoyés à votre MonCash",
        "write_comment": "Écrire un commentaire...",
        "send": "Envoyer",
        "back_to_feed": "Retour au fil",
        "create_post": "Créer une publication",
        "caption_placeholder": "Écrivez quelque chose... ou collez un lien vidéo",
        "add_media": "Ajouter des images ou vidéos (optionnel)",
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
        "join_live": "Rejoindre le direct",
        "watch_stream": "▶ REGARDER LE DIRECT",
        "start_broadcast": "▶ COMMENCER LA DIFFUSION",
        "stop_broadcast": "■ ARRÊTER LA DIFFUSION",
        "you_are_broadcaster": "✅ Vous êtes le diffuseur. Utilisez les commandes ci‑dessous pour commencer.",
        "you_are_viewer": "👀 Vous êtes spectateur. Cliquez sur 'Regarder le direct' pour voir la vidéo.",
        "choose_background": "🎨 Filtres d'arrière‑plan",
        "bg_option": "AR",
        "upload_background": "Ou téléchargez votre propre image",
        "background_set": "Arrière‑plan défini !",
        "ready_to_start": "Prêt à commencer. Cliquez sur le bouton ci‑dessus.",
        "camera_access": "📷 Demande d'accès à la caméra...",
        "camera_granted": "✅ Accès à la caméra accordé. Connexion au serveur peer...",
        "broadcasting": "✅ Diffusion en direct ! Votre ID peer",
        "peer_error": "❌ Erreur peer",
        "error": "❌ Erreur",
        "broadcast_ended": "Diffusion terminée",
        "initializing": "Initialisation...",
        "connected_requesting": "Connecté. Demande du flux au diffuseur...",
        "calling": "Appel en cours",
        "received_stream": "Flux reçu",
        "now_watching": "✅ Vous regardez maintenant le direct",
        "call_error": "❌ Erreur d'appel",
        "call_ended": "Appel terminé",
        "disconnected": "Déconnecté. Veuillez rafraîchir.",
        "send_message": "Envoyer",
        "close_chat": "Fermer le chat",
        "active_call": "📞 Appel en cours",
        "room_id": "ID de la salle",
        "share_room": "Partagez cet ID avec la personne que vous voulez appeler.",
        "start_call": "Commencer un nouvel appel",
        "end_call": "Terminer l'appel",
        "find_users": "🔍 Trouver des utilisateurs",
        "search_by_name": "Rechercher par nom",
        "add_friend": "➕ Ajouter un ami",
        "view_profile": "👤 Voir le profil",
        "friend_requests": "📨 Demandes d'amis reçues",
        "accept": "✅ Accepter",
        "reject": "❌ Refuser",
        "your_friends": "👥 Vos amis",
        "no_friends": "Vous n'avez pas encore d'amis",
        "chat": "💬 Chat",
        "call": "📞 Appel",
        "profile_btn": "👤 Profil",
        "edit_profile": "Modifier le profil",
        "save_changes": "💾 Enregistrer les modifications",
        "change_picture": "📸 Changer la photo",
        "bio": "Bio",
        "location": "Localisation",
        "moncash_phone": "Numéro MonCash (pour recevoir des cadeaux)",
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
        "transfer": "🚀 Transférer vers MonCash",
        "no_gifts": "Pas encore de cadeaux.",
        "payout_summary": "Récapitulatif des paiements",
        "total_gifts_htg": "Total des cadeaux (HTG)",
        "mark_paid": "Marquer tout comme payé (simulé)",
        "contact_support": "📬 Contact pour assistance / paiements importants",
        "logout_owner": "Déconnexion de l'espace propriétaire",
        "setup_instructions": "ℹ️ Instructions de configuration (si l'upload échoue)",
        "storage_error": "Erreur de permission de stockage : veuillez configurer les politiques RLS pour le bucket 'avatars'.",
        "listen_explanation": "🔊 Écouter l'explication de l'application",
        "voice_lang": "🌐 Langue de la voix",
        "app_explanation": "Cette application a été construite par Gesner Deslandes, ingénieur en chef chez GlobalInternet.py. Téléphone : (509) 4738-5663. Email : deslandes78@gmail.com. Contactez Gesner si vous souhaitez créer un site web ou un logiciel. Cette application est une plateforme de médias sociaux haïtienne qui vous permet de vous connecter avec des amis, partager des publications, passer en direct, envoyer des cadeaux et discuter en temps réel. Elle utilise Supabase pour les données, prend en charge la diffusion en direct avec des filtres d'arrière-plan et comprend une carte satellite pour le divertissement. Elle est conçue pour être un espace moderne, sécurisé et amusant pour les utilisateurs haïtiens afin d'interagir en ligne. Toutes les fonctionnalités sont construites avec Python et Streamlit. Et en plus, lorsqu'il y a un match de la Coupe du Monde, vous pouvez le regarder en direct directement sur la plateforme !",
        "network_error": "⚠️ Impossible de se connecter au serveur d'authentification. Veuillez vérifier votre connexion internet et réessayer. Si le problème persiste, contactez le support.",
        "debug_hint": "Si vous êtes administrateur, activez 'Afficher les infos de débogage' ci-dessous pour voir l'erreur brute.",
        "show_debug": "Afficher les infos de débogage",
        "home_title": "🏠 Home Sweet Home",
        "home_haiti": "HAITI",
        "home_subtitle": "Your Haitian social media platform"
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
        "send_reset_link": "Enviar enlace de restablecimiento",
        "phone_method": "Teléfono (OTP)",
        "email_method": "Correo",
        "phone_number": "Número de teléfono (solo dígitos, ej: 50947385663)",
        "send_otp": "📲 Enviar OTP",
        "enter_otp": "Ingrese el código OTP de 6 dígitos",
        "verify_login": "✅ Verificar e iniciar sesión",
        "back_resend": "← Atrás / Reenviar OTP",
        "feed": "📡 Feed",
        "friends_chat": "👥 Amigos y chat",
        "satellite_map": "🛰️ Mapa satelital",
        "profile": "👤 Perfil",
        "owner_space": "🕊️ Espacio del propietario",
        "logout": "🚪 Cerrar sesión",
        "system_health": "🛡️ Estado del sistema",
        "signal": "📡 Señal",
        "latency": "⏱️ Latencia",
        "quality": "📊 Calidad",
        "uptime": "⏰ Tiempo activo",
        "encrypted": "🔒 Estado: ENCRIPTADO",
        "compensation": "💰 Compensación",
        "logged_in_as": "👤 Conectado como",
        "go_live": "Ir en vivo",
        "external_platform": "Plataforma externa (YouTube/Facebook/Twitch)",
        "in_app_camera": "Cámara integrada",
        "select_platform": "Seleccionar plataforma",
        "live_title": "Título del directo",
        "create_live_session": "Crear sesión en vivo",
        "you_are_live": "🔴 ¡Estás en vivo!",
        "end_live_session": "Finalizar sesión en vivo",
        "set_stream_url": "📹 Configurar URL del stream",
        "paste_url": "Pega la URL de tu transmisión en vivo",
        "update_url": "Actualizar URL",
        "shareable_link": "Enlace compartible",
        "live_chat_gifts": "Chat en vivo y regalos",
        "send_gift": "🎁 Enviar un regalo",
        "add_moncash": "Agrega tu número de MonCash en tu perfil para enviar regalos.",
        "total_gifts": "Total de regalos recibidos",
        "gifts_sent_to": "Los regalos se enviarán a tu MonCash",
        "write_comment": "Escribe un comentario...",
        "send": "Enviar",
        "back_to_feed": "Volver al feed",
        "create_post": "Crear una publicación",
        "caption_placeholder": "Escribe algo... o pega un enlace de video",
        "add_media": "Agregar imágenes o videos (opcional)",
        "visibility": "Visibilidad",
        "public": "Público",
        "private": "Privado",
        "post": "🚀 Publicar",
        "delete_post": "🗑️ Eliminar",
        "comments": "Comentarios",
        "reply": "💬 Responder",
        "post_reply": "Publicar respuesta",
        "your_reply": "Tu respuesta",
        "clear_error": "Limpiar error",
        "join_live": "Unirse al directo",
        "watch_stream": "▶ VER TRANSMISIÓN",
        "start_broadcast": "▶ INICIAR TRANSMISIÓN",
        "stop_broadcast": "■ DETENER TRANSMISIÓN",
        "you_are_broadcaster": "✅ Eres el transmisor. Usa los controles a continuación para comenzar.",
        "you_are_viewer": "👀 Eres espectador. Haz clic en 'Ver transmisión' para ver el video.",
        "choose_background": "🎨 Filtros de fondo",
        "bg_option": "FDO",
        "upload_background": "O sube tu propia imagen",
        "background_set": "¡Fondo establecido!",
        "ready_to_start": "Listo para comenzar. Haz clic en el botón de arriba.",
        "camera_access": "📷 Solicitando acceso a la cámara...",
        "camera_granted": "✅ Acceso a la cámara concedido. Conectando al servidor peer...",
        "broadcasting": "✅ ¡Transmitiendo en vivo! Tu ID peer",
        "peer_error": "❌ Error peer",
        "error": "❌ Error",
        "broadcast_ended": "Transmisión finalizada",
        "initializing": "Inicializando...",
        "connected_requesting": "Conectado. Solicitando transmisión al emisor...",
        "calling": "Llamando",
        "received_stream": "Flujo recibido",
        "now_watching": "✅ Ahora estás viendo la transmisión en vivo",
        "call_error": "❌ Error de llamada",
        "call_ended": "Llamada finalizada",
        "disconnected": "Desconectado. Por favor refresca.",
        "send_message": "Enviar",
        "close_chat": "Cerrar chat",
        "active_call": "📞 Llamada activa",
        "room_id": "ID de sala",
        "share_room": "Comparte este ID con la persona a la que quieres llamar.",
        "start_call": "Iniciar nueva llamada",
        "end_call": "Finalizar llamada",
        "find_users": "🔍 Buscar usuarios",
        "search_by_name": "Buscar por nombre",
        "add_friend": "➕ Agregar amigo",
        "view_profile": "👤 Ver perfil",
        "friend_requests": "📨 Solicitudes de amistad recibidas",
        "accept": "✅ Aceptar",
        "reject": "❌ Rechazar",
        "your_friends": "👥 Tus amigos",
        "no_friends": "Aún no tienes amigos",
        "chat": "💬 Chat",
        "call": "📞 Llamada",
        "profile_btn": "👤 Perfil",
        "edit_profile": "Editar perfil",
        "save_changes": "💾 Guardar cambios",
        "change_picture": "📸 Cambiar foto",
        "bio": "Biografía",
        "location": "Localización",
        "moncash_phone": "Número MonCash (para recibir regalos)",
        "posts_count": "Publicaciones",
        "connections": "Conexiones",
        "verified": "Verificado",
        "member_since": "Miembro desde",
        "dashboard": "💰 Panel",
        "new_users": "📈 Nuevos usuarios",
        "post_moderation": "🛡️ Moderación de publicaciones",
        "client_payments": "📥 Pagos de clientes",
        "gift_management": "🎁 Gestión de regalos",
        "owner_dashboard": "🔐 Panel del propietario",
        "balance": "Saldo MonCash Business",
        "transfer_funds": "💰 Transferir fondos a tu cuenta",
        "amount_transfer": "Monto a transferir ($)",
        "transfer": "🚀 Transferir a MonCash",
        "no_gifts": "Aún no hay regalos.",
        "payout_summary": "Resumen de pagos",
        "total_gifts_htg": "Total de regalos (HTG)",
        "mark_paid": "Marcar todo como pagado (simulado)",
        "contact_support": "📬 Contacto para soporte / pagos grandes",
        "logout_owner": "Cerrar sesión del espacio propietario",
        "setup_instructions": "ℹ️ Instrucciones de configuración (si falla la subida)",
        "storage_error": "Error de permiso de almacenamiento: configure políticas RLS para el bucket 'avatars'.",
        "listen_explanation": "🔊 Escuchar explicación de la aplicación",
        "voice_lang": "🌐 Idioma de la voz",
        "app_explanation": "Esta aplicación fue construida por Gesner Deslandes, Ingeniero Jefe en GlobalInternet.py. Teléfono: (509) 4738-5663. Correo: deslandes78@gmail.com. Póngase en contacto con Gesner si desea crear un sitio web o software. Esta aplicación es una plataforma de redes sociales haitiana que le permite conectarse con amigos, compartir publicaciones, transmitir en vivo, enviar regalos y chatear en tiempo real. Utiliza Supabase para los datos, admite transmisión en vivo con filtros de fondo e incluye un mapa satelital para diversión. Está diseñada para ser un espacio moderno, seguro y divertido para que los usuarios haitianos interactúen en línea. Todas las características están construidas con Python y Streamlit. ¡Además, cuando haya un partido del Mundial, podrás verlo en vivo aquí mismo en la plataforma!",
        "network_error": "⚠️ No se puede conectar al servidor de autenticación. Verifique su conexión a internet e intente de nuevo. Si el problema persiste, contacte al soporte.",
        "debug_hint": "Si es administrador, active 'Mostrar información de depuración' a continuación para ver el error sin procesar.",
        "show_debug": "Mostrar información de depuración",
        "home_title": "🏠 Home Sweet Home",
        "home_haiti": "HAITI",
        "home_subtitle": "Your Haitian social media platform"
    },
    "ht": {
        "login_title": "Konekte",
        "signup_title": "Enskri",
        "forgot_password": "Bliye modpas",
        "email": "Imèl",
        "password": "Modpas",
        "full_name": "Non konplè",
        "remember_me": "Sonje m",
        "login_button": "🚀 Konekte",
        "signup_button": "📝 Enskri",
        "send_reset_link": "Voye lyen reyinisyalizasyon",
        "phone_method": "Telefòn (OTP)",
        "email_method": "Imèl",
        "phone_number": "Nimewo telefòn (chif sèlman, egzanp: 50947385663)",
        "send_otp": "📲 Voye OTP",
        "enter_otp": "Antre kòd OTP 6 chif",
        "verify_login": "✅ Verifye epi konekte",
        "back_resend": "← Retounen / Reseye OTP",
        "feed": "📡 Feed",
        "friends_chat": "👥 Zanmi ak chat",
        "satellite_map": "🛰️ Kat satelit",
        "profile": "👤 Pwofil",
        "owner_space": "🕊️ Espas Pwopriyetè",
        "logout": "🚪 Dekonekte",
        "system_health": "🛡️ Sante sistèm",
        "signal": "📡 Siyal",
        "latency": "⏱️ Latansi",
        "quality": "📊 Kalite",
        "uptime": "⏰ Tan fonksyònman",
        "encrypted": "🔒 Estati: CHIFRE",
        "compensation": "💰 Konpansasyon",
        "logged_in_as": "👤 Konekte kòm",
        "go_live": "Ale an dirèk",
        "external_platform": "Platfòm ekstèn (YouTube/Facebook/Twitch)",
        "in_app_camera": "Kamera entegre",
        "select_platform": "Chwazi platfòm",
        "live_title": "Tit dirèk",
        "create_live_session": "Kreye sesyon dirèk",
        "you_are_live": "🔴 Ou an dirèk!",
        "end_live_session": "Fèmen sesyon dirèk",
        "set_stream_url": "📹 Mete URL stream",
        "paste_url": "Kole URL stream dirèk ou",
        "update_url": "Mete ajou URL",
        "shareable_link": "Lyen pataj",
        "live_chat_gifts": "Chat dirèk ak kado",
        "send_gift": "🎁 Voye yon kado",
        "add_moncash": "Ajoute nimewo MonCash ou nan pwofil ou pou voye kado.",
        "total_gifts": "Total kado resevwa",
        "gifts_sent_to": "Kado yo pral voye nan MonCash ou",
        "write_comment": "Ekri yon kòmantè...",
        "send": "Voye",
        "back_to_feed": "Retounen nan feed",
        "create_post": "Kreye yon pòs",
        "caption_placeholder": "Ekri yon bagay... oswa kole yon lyen videyo",
        "add_media": "Ajoute imaj oswa videyo (opsyonèl)",
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
        "start_broadcast": "▶ KÒMANSE DIFIZYON",
        "stop_broadcast": "■ STOP DIFIZYON",
        "you_are_broadcaster": "✅ Ou se difizè. Sèvi ak kontwòl anba a pou kòmanse.",
        "you_are_viewer": "👀 Ou se yon telespektatè. Klike sou 'Gade Stream' pou wè videyo a.",
        "choose_background": "🎨 Filtre background",
        "bg_option": "BG",
        "upload_background": "Oswa telechaje pwòp imaj ou",
        "background_set": "Background mete!",
        "ready_to_start": "Pare pou kòmanse. Klike sou bouton an pi wo a.",
        "camera_access": "📷 Mande aksè kamera...",
        "camera_granted": "✅ Aksè kamera akòde. Konekte ak sèvè peer...",
        "broadcasting": "✅ Difizyon an dirèk! ID peer ou",
        "peer_error": "❌ Erè peer",
        "error": "❌ Erè",
        "broadcast_ended": "Difizyon fini",
        "initializing": "Inisyalizasyon...",
        "connected_requesting": "Konekte. Mande stream nan men difizè...",
        "calling": "Ap rele",
        "received_stream": "Resevwa stream",
        "now_watching": "✅ Koulye a w ap gade stream an dirèk",
        "call_error": "❌ Erè apèl",
        "call_ended": "Apèl fini",
        "disconnected": "Dekonekte. Tanpri rafrechi.",
        "send_message": "Voye",
        "close_chat": "Fèmen chat",
        "active_call": "📞 Apèl aktif",
        "room_id": "ID sal",
        "share_room": "Pataje ID sal sa a ak moun ou vle rele.",
        "start_call": "Kòmanse yon nouvo apèl",
        "end_call": "Fèmen apèl",
        "find_users": "🔍 Chèche itilizatè",
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
        "save_changes": "💾 Sove chanjman",
        "change_picture": "📸 Chanje foto",
        "bio": "Biwo",
        "location": "Kote",
        "moncash_phone": "Nimewo MonCash (pou resevwa kado)",
        "posts_count": "Pòs",
        "connections": "Koneksyon",
        "verified": "Verifye",
        "member_since": "Manm depi",
        "dashboard": "💰 Tablo",
        "new_users": "📈 Nouvo itilizatè",
        "post_moderation": "🛡️ Moderasyon pòs",
        "client_payments": "📥 Peman kliyan",
        "gift_management": "🎁 Jesyon kado",
        "owner_dashboard": "🔐 Tablo pwopriyetè",
        "balance": "Balan MonCash Business",
        "transfer_funds": "💰 Transfere lajan nan kont ou",
        "amount_transfer": "Montan pou transfere ($)",
        "transfer": "🚀 Transfere nan MonCash mwen",
        "no_gifts": "Pokono kado.",
        "payout_summary": "Rezime peman",
        "total_gifts_htg": "Total kado (HTG)",
        "mark_paid": "Make tout kòm peye (simile)",
        "contact_support": "📬 Kontakte sipò / gwo peman",
        "logout_owner": "Dekonekte Espas Pwopriyetè",
        "setup_instructions": "ℹ️ Enstriksyon konfigirasyon (si telechajman echwe)",
        "storage_error": "Erè pèmisyon depo: Tanpri mete politik RLS pou bucket 'avatars'.",
        "listen_explanation": "🔊 Koute eksplikasyon aplikasyon an",
        "voice_lang": "🌐 Lang vwa",
        "app_explanation": "Aplikasyon sa a te bati pa Gesner Deslandes, Enjenyè an Chèf nan GlobalInternet.py. Telefòn: (509) 4738-5663. Imèl: deslandes78@gmail.com. Kontakte Gesner si ou vle bati yon sit wèb oswa lojisyèl. Aplikasyon sa a se yon platfòm medya sosyal ayisyen ki pèmèt ou konekte ak zanmi, pataje pòs, ale an dirèk, voye kado, ak chat an tan reyèl. Li itilize Supabase pou done, sipòte difizyon an dirèk ak filt background, epi li gen yon kat satelit pou amizman. Li fèt pou yon espas modèn, sekirize ak amizan pou itilizatè ayisyen yo ka entèaktif sou entènèt. Tout fonksyonalite yo bati ak Python ak Streamlit. Anplis de sa, lè gen yon match Mondyal la, ou ka gade l an dirèk sou platfòm nan!",
        "network_error": "⚠️ Pa ka konekte ak sèvè otantifikasyon an. Tanpri tcheke koneksyon entènèt ou epi eseye ankò. Si pwoblèm nan kontinye, kontakte sipò.",
        "debug_hint": "Si w se administratè, aktive 'Montre enfòmasyon debogaj' anba a pou wè erè a.",
        "show_debug": "Montre enfòmasyon debogaj",
        "home_title": "Lakay Se Lakay",
        "home_haiti": "Ayiti",
        "home_subtitle": "Nouvo rezo Sosyal Ayisyen"
    },
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
            profile = get_or_create_profile(new_session.user.id, new_session.user.email or new_session.user.phone)
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

if st.session_state.logged_in and supabase and st.session_state.refresh_token:
    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        if new_session and new_session.user:
            st.session_state.user = new_session.user
            st.session_state.refresh_token = new_session.session.refresh_token
    except Exception:
        pass

# ====== UI STYLING ======
st.markdown("""
    <style>
    .stApp [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #E3F2FD 0%, #FFCDD2 100%);
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
        padding: 8px 20px;
        font-weight: 600;
        box-shadow: 0 8px 16px rgba(0,128,255,0.2);
        transition: all 0.2s;
        font-size: 0.9rem;
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
    @media (max-width: 768px) {
        .stButton > button {
            padding: 6px 12px;
            font-size: 0.8rem;
        }
        .post-card {
            padding: 12px 15px;
        }
        .stMetric {
            padding: 12px;
        }
        .haiti-symbol {
            font-size: 3rem;
        }
        .owner-name {
            font-size: 1.2rem;
        }
        .collaborators {
            font-size: 0.8rem;
            padding: 6px 10px;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: unset !important;
        }
        .row-widget.stRadio > div {
            flex-direction: column;
        }
    }
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
    .home-title {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #BBDEFB, #FFCDD2);
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .home-title h1 {
        margin: 0;
        font-size: 2.8rem;
        color: #0a2a44;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .home-title p {
        margin: 0.3rem 0 0;
        opacity: 0.85;
        color: #1e2a3a;
        font-size: 1.1rem;
    }
    .dove-symbol {
        font-size: 4rem;
        color: #ffffff;
        text-shadow: 0 0 20px rgba(0,0,0,0.1);
        display: block;
        margin: 0 auto;
    }
    </style>
""", unsafe_allow_html=True)

# ====== HELPER FUNCTIONS ======
def make_clickable(text):
    url_pattern = r'(https?://[^\s]+)'
    return re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', text)

def get_youtube_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([\w-]+)',
        r'(?:youtu\.be\/)([\w-]+)',
        r'(?:youtube\.com\/embed\/)([\w-]+)',
        r'(?:youtube\.com\/v\/)([\w-]+)',
        r'(?:youtube\.com\/shorts\/)([\w-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_vimeo_id(url):
    match = re.search(r'(?:vimeo\.com\/)(\d+)', url)
    return match.group(1) if match else None

def get_dailymotion_id(url):
    match = re.search(r'(?:dailymotion\.com\/video\/)([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None

def get_facebook_video_url(url):
    if 'facebook.com' in url and ('/video' in url or '/watch' in url or 'videos' in url):
        return url
    return None

def get_tiktok_id(url):
    match = re.search(r'(?:tiktok\.com\/@[\w.-]+\/video\/)(\d+)', url)
    if match:
        return match.group(1)
    match = re.search(r'(?:vm\.tiktok\.com\/)([\w]+)', url)
    if match:
        return match.group(1)
    return None

def get_twitch_url(url):
    if 'twitch.tv' in url:
        return url
    return None

def get_instagram_url(url):
    if 'instagram.com' in url and ('/p/' in url or '/reel/' in url):
        return url
    return None

def get_streamable_id(url):
    match = re.search(r'(?:streamable\.com\/)([a-zA-Z0-9]+)', url)
    return match.group(1) if match else None

def is_direct_video_url(url):
    video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv', '.mpg', '.mpeg', '.m4v']
    return any(url.lower().endswith(ext) for ext in video_extensions)

# ====== UPDATED: Enhanced embed_video_from_url with Twitch live support ======
def embed_video_from_url(url):
    youtube_id = get_youtube_id(url)
    if youtube_id:
        embed_html = f"""
        <iframe width="100%" height="400" src="https://www.youtube.com/embed/{youtube_id}?autoplay=1" 
                frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    vimeo_id = get_vimeo_id(url)
    if vimeo_id:
        embed_html = f"""
        <iframe src="https://player.vimeo.com/video/{vimeo_id}?autoplay=1" width="100%" height="400" 
                frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 Vimeo {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    dailymotion_id = get_dailymotion_id(url)
    if dailymotion_id:
        embed_html = f"""
        <iframe frameborder="0" width="100%" height="400" 
                src="https://www.dailymotion.com/embed/video/{dailymotion_id}?autoplay=1" 
                allowfullscreen allow="autoplay"></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 Dailymotion {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    fb_url = get_facebook_video_url(url)
    if fb_url:
        embed_html = f"""
        <div id="fb-root"></div>
        <script async defer src="https://connect.facebook.net/en_US/sdk.js#xfbml=1&version=v3.2"></script>
        <div class="fb-video" data-href="{fb_url}" data-width="100%" data-allowfullscreen="true" data-autoplay="true"></div>
        <p style="font-size:0.8rem; color:green;">🎥 Facebook {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=470)
        return True
    tiktok_id = get_tiktok_id(url)
    if tiktok_id:
        if tiktok_id.isdigit():
            embed_html = f"""
            <blockquote class="tiktok-embed" cite="https://www.tiktok.com/@username/video/{tiktok_id}" data-video-id="{tiktok_id}" style="max-width: 605px;min-width: 325px;" > 
            <section> <a target="_blank" title="TikTok" href="https://www.tiktok.com/@username/video/{tiktok_id}">View on TikTok</a> </section> </blockquote> 
            <script async src="https://www.tiktok.com/embed.js"></script>
            <p style="font-size:0.8rem; color:green;">🎥 TikTok {t('now_watching')}</p>
            """
        else:
            embed_html = f"""
            <iframe width="100%" height="600" src="{url}" frameborder="0" allowfullscreen></iframe>
            <p style="font-size:0.8rem; color:green;">🎥 TikTok {t('now_watching')}</p>
            """
        st.components.v1.html(embed_html, height=650)
        return True
    twitch_url = get_twitch_url(url)
    if twitch_url:
        try:
            parent = st.request.host if hasattr(st, 'request') else 'localhost'
        except:
            parent = 'localhost'
        if '/videos/' in twitch_url or '/clip/' in twitch_url:
            video_id = twitch_url.split('/')[-1].split('?')[0]
            embed_url = f"https://player.twitch.tv/?video={video_id}&parent={parent}&autoplay=true"
        else:
            channel = twitch_url.split('/')[-1].split('?')[0]
            embed_url = f"https://player.twitch.tv/?channel={channel}&parent={parent}&autoplay=true"
        embed_html = f"""
        <iframe src="{embed_url}" 
                height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 Twitch {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    insta_url = get_instagram_url(url)
    if insta_url:
        embed_html = f"""
        <iframe width="100%" height="600" src="{url}embed" frameborder="0" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 Instagram {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=630)
        return True
    streamable_id = get_streamable_id(url)
    if streamable_id:
        embed_html = f"""
        <iframe width="100%" height="400" src="https://streamable.com/e/{streamable_id}" 
                frameborder="0" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 Streamable {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    if is_direct_video_url(url):
        st.video(url)
        st.markdown(f"<p style='font-size:0.8rem; color:green;'>🎥 {t('now_watching')}</p>", unsafe_allow_html=True)
        return True
    return False

# ---- Profile & Auth ----
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
                "moncash_phone": None,
                "join_date": datetime.now().isoformat()
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
    if not ensure_bucket_exists("avatars"):
        st.error("❌ Cannot upload: 'avatars' bucket missing. Please create it manually in Supabase Dashboard → Storage.")
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
            st.error(t("storage_error"))
        else:
            st.session_state.last_error = f"Avatar upload failed: {e}"
        return None

def upload_post_media(user_id, file):
    if supabase is None:
        return None
    if not ensure_bucket_exists("post_media"):
        st.error("❌ Cannot upload: 'post_media' bucket missing. Please create it manually in Supabase Dashboard → Storage.")
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
            st.error(t("storage_error").replace("avatars", "post_media"))
        else:
            st.session_state.last_error = f"Media upload failed: {e}"
        return None

def upload_chat_media(user_id, file):
    if supabase is None:
        return None
    if not ensure_bucket_exists("chat_media"):
        st.error("❌ Cannot upload: 'chat_media' bucket missing. Please create it manually in Supabase Dashboard → Storage.")
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
            st.error(t("storage_error").replace("avatars", "chat_media"))
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

def send_gift(session_id, sender_id, recipient_id, amount, currency):
    if supabase is None:
        return False, "Supabase not configured"
    try:
        rate = st.session_state.exchange_rate
        if currency == "USD":
            amount_htg = amount * rate
        else:
            amount_htg = amount
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
        payment_success = True
        if payment_success:
            supabase.table("live_gifts").update({"status": "completed"}).eq("id", gift_id).execute()
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
    if supabase is None:
        return []
    try:
        resp = supabase.table("live_gifts").select("*").eq("session_id", session_id).eq("status", "completed").order("created_at").execute()
        gifts = resp.data or []
        for g in gifts:
            g['sender'] = {'full_name': g.get('sender_name', 'Someone'), 'avatar_url': None}
        return gifts
    except Exception as e:
        error_str = str(e)
        if "permission denied" in error_str.lower() and "users" in error_str.lower():
            st.session_state.last_error = (
                "Permission denied while loading gifts. This is likely due to a Row Level Security (RLS) policy "
                "that references the `users` table. Please check your Supabase policies on the `live_gifts` table "
                "and ensure the anon role has the necessary permissions, or modify the policy to avoid using the `users` table."
            )
        else:
            st.session_state.last_error = f"Error loading gifts: {e}"
        return []

def accept_participant(session_id, participant_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_participants").update({"status": "accepted"}).eq("id", participant_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error accepting participant: {e}"
        return False

def reject_participant(participant_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_participants").delete().eq("id", participant_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error rejecting participant: {e}"
        return False

def mute_participant(session_id, participant_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_participants").update({"status": "muted"}).eq("id", participant_id).execute()
        supabase.table("notifications").insert({
            "user_id": participant_id,
            "type": "live_mute",
            "message": "The broadcaster has muted your microphone.",
            "read": False
        }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error muting participant: {e}"
        return False

def unmute_participant(session_id, participant_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_participants").update({"status": "accepted"}).eq("id", participant_id).execute()
        supabase.table("notifications").insert({
            "user_id": participant_id,
            "type": "live_unmute",
            "message": "The broadcaster has unmuted your microphone.",
            "read": False
        }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error unmuting participant: {e}"
        return False

def remove_participant(participant_id):
    if supabase is None:
        return False
    try:
        supabase.table("live_participants").delete().eq("id", participant_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error removing participant: {e}"
        return False

# ---- Posts ----
@st.cache_data(ttl=60, show_spinner=False)
def load_posts_cached(user_id=None, author_id=None):
    if supabase is None:
        return []
    try:
        query = supabase.table("posts").select("*")
        if author_id is not None:
            query = query.eq("user_id", author_id).eq("is_public", True)
        elif user_id is not None:
            public_resp = supabase.table("posts").select("*").eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            private_resp = supabase.table("posts").select("*").eq("is_public", False).eq("user_id", user_id).order("created_at", desc=True).execute()
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
            resp = supabase.table("posts").select("*").eq("is_public", True).order("created_at", desc=True).limit(50).execute()
            posts = resp.data

        user_ids = {p["user_id"] for p in posts}
        profiles = {}
        if user_ids:
            profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, is_live").in_("id", list(user_ids)).execute()
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p

        for post in posts:
            p = profiles.get(post["user_id"], {})
            post["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "is_live": p.get("is_live", False),
            }
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
            for f in media_files:
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
        post_data = {
            "content": content,
            "media_urls": media_urls,
            "updated_at": datetime.now().isoformat()
        }
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
            profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url").in_("id", list(user_ids)).execute()
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p

        for c in comments:
            p = profiles.get(c["user_id"], {})
            c["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
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
            profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone").in_("id", list(user_ids)).execute()
            for p in profiles_resp.data or []:
                profiles[p["id"]] = p

        for s in sessions:
            p = profiles.get(s["user_id"], {})
            s["profiles"] = {
                "full_name": p.get("full_name", "Unknown"),
                "avatar_url": p.get("avatar_url"),
                "moncash_phone": p.get("moncash_phone"),
            }
            if "stream_method" not in s:
                s["stream_method"] = "external"
        return sessions
    except Exception as e:
        st.session_state.last_error = f"Error loading live sessions: {e}"
        return []

def create_live_session(title, platform, method='external'):
    if supabase is None or st.session_state.user is None:
        st.session_state.last_error = "Cannot start live session."
        return None
    try:
        try:
            supabase.table("live_sessions").select("stream_method").limit(1).execute()
        except Exception as e:
            if "column 'stream_method' does not exist" in str(e):
                st.warning("Adding missing 'stream_method' column to live_sessions table...")
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

def get_live_session(session_id):
    if supabase is None:
        return None
    try:
        response = supabase.table("live_sessions").select("*").eq("id", session_id).single().execute()
        session = response.data
        if not session:
            return None

        profile_resp = supabase.table("profiles").select("id, full_name, avatar_url, moncash_phone").eq("id", session["user_id"]).single().execute()
        profile = profile_resp.data or {}
        session["profiles"] = {
            "full_name": profile.get("full_name", "Unknown"),
            "avatar_url": profile.get("avatar_url"),
            "moncash_phone": profile.get("moncash_phone"),
        }
        if "stream_method" not in session:
            session["stream_method"] = "external"
        return session
    except Exception as e:
        st.session_state.last_error = f"Error fetching live session: {e}"
        return None

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

    pending_resp = supabase.table("friend_requests").select(
        "id, sender_id, receiver_id, status, created_at"
    ).eq("receiver_id", user_id).eq("status", "pending").execute()
    pending_raw = pending_resp.data or []

    sent_resp = supabase.table("friend_requests").select(
        "id, sender_id, receiver_id, status, created_at"
    ).eq("sender_id", user_id).eq("status", "accepted").execute()
    received_resp = supabase.table("friend_requests").select(
        "id, sender_id, receiver_id, status, created_at"
    ).eq("receiver_id", user_id).eq("status", "accepted").execute()
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
        profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url").in_("id", list(user_ids)).execute()
        for p in profiles_resp.data or []:
            profiles[p["id"]] = p

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
            },
            "receiver_id": req["receiver_id"],
            "status": req["status"],
        })
    st.session_state.friend_requests = pending_requests

    friends = []
    seen = set()
    for req in accepted_raw:
        if req["sender_id"] == user_id:
            other_id = req["receiver_id"]
        else:
            other_id = req["sender_id"]
        if other_id in seen:
            continue
        seen.add(other_id)
        other = profiles.get(other_id, {})
        friends.append({
            "id": other_id,
            "full_name": other.get("full_name", "Unknown"),
            "avatar_url": other.get("avatar_url"),
        })
    st.session_state.friends = friends

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

def start_call(room_id=None):
    if not room_id:
        room_id = hashlib.md5(f"{st.session_state.user.id}_{time.time()}".encode()).hexdigest()[:10]
    st.session_state.call_room = room_id
    st.session_state.in_call = True

def end_call():
    st.session_state.in_call = False
    st.session_state.call_room = None

# ---- Owner Space helpers ----
def ensure_owner_state_table():
    if supabase is None:
        return False
    try:
        try:
            supabase.table("owner_state").select("id").limit(1).execute()
            return True
        except Exception as e:
            if "Could not find the table" in str(e):
                st.session_state.last_error = "The 'owner_state' table is missing. Please run the SQL in your Supabase SQL editor to enable owner notifications."
                return False
            else:
                st.session_state.last_error = f"Error checking owner_state: {e}"
                return False
    except Exception as e:
        st.session_state.last_error = f"Error ensuring owner_state: {e}"
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
    except Exception as e:
        st.session_state.last_error = f"Error getting last seen signup: {e}"
        return datetime(2020, 1, 1)

def update_last_seen_signup():
    if supabase is None:
        return
    try:
        if not ensure_owner_state_table():
            return
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
        error_str = str(e)
        if "permission denied" in error_str.lower() and "users" in error_str.lower():
            st.session_state.last_error = (
                "Permission denied while fetching new users. This may be due to a policy on the `profiles` table "
                "that references the `users` table. Please review your RLS policies and grant the necessary permissions."
            )
        else:
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
        user = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}}
        })
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

# ====== LOGIN FUNCTION WITH DEBUG OPTION ======
def log_in_email(email, password, remember=False, show_debug=False):
    if supabase is None:
        st.error("❌ Authentication service is not configured. Please contact the administrator.")
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

# ====== LOGIN INTERFACE ======
def login_interface():
    st.markdown(
        """
        <div style="text-align: center; padding: 20px 0;">
            <span class="dove-symbol">🕊️</span>
            <h2 style="color: #0a2a44; margin-top: -5px;">Welcome to Home Sweet Home</h2>
            <p style="color: #1e2a3a; opacity: 0.8;">A space of hope, connection, and community</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    show_debug = st.checkbox(t("show_debug"), value=False)

    auth_method = st.radio(t("login_title"), [t("email_method"), t("phone_method")], horizontal=True)

    if auth_method == t("email_method"):
        tab1, tab2, tab3 = st.tabs([t("login_title"), t("signup_title"), t("forgot_password")])
        with tab1:
            with st.form("login_email"):
                email = st.text_input(t("email"))
                password = st.text_input(t("password"), type="password")
                remember = st.checkbox(t("remember_me"))
                login_clicked = st.form_submit_button(t("login_button"), use_container_width=True)

                if login_clicked:
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
    else:
        st.info("Phone users: You will receive a 6‑digit OTP each time you log in.")
        if not st.session_state.phone_otp_sent:
            with st.form("phone_request"):
                phone = st.text_input(t("phone_number"))
                remember = st.checkbox(t("remember_me"))
                if st.form_submit_button(t("send_otp"), use_container_width=True):
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
                otp = st.text_input(t("enter_otp"))
                if st.form_submit_button(t("verify_login"), use_container_width=True):
                    if otp:
                        remember = st.session_state.get("phone_remember", False)
                        verify_phone_otp(st.session_state.temp_phone, otp, remember)
                    else:
                        st.warning("Please enter the OTP")
            if st.button(t("back_resend")):
                st.session_state.phone_otp_sent = False
                st.session_state.temp_phone = ""
                st.rerun()

# ========== SOCIAL MEDIA RENDER FUNCTIONS ==========

def display_media_item(media):
    try:
        if media["type"] == "image":
            st.image(media["url"], use_column_width=True)
        elif media["type"] == "video":
            video_html = f"""
            <video controls style="width:100%; max-height:60vh; border-radius:12px;" preload="metadata">
                <source src="{media['url']}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            """
            st.markdown(video_html, unsafe_allow_html=True)
            st.markdown(f"[📹 Open video directly]({media['url']})", unsafe_allow_html=True)
        else:
            st.markdown(f"[Media file]({media['url']})")
    except Exception as e:
        st.error(f"Error displaying media: {e}")
        st.markdown(f"[Click to open media]({media['url']})")

def render_feed():
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

    st.markdown(f"### {t('create_post')}")
    with st.form("new_post", clear_on_submit=True):
        col_avatar, col_input = st.columns([1, 8])
        with col_avatar:
            if st.session_state.profile and st.session_state.profile.get("avatar_url"):
                st.image(st.session_state.profile["avatar_url"], width=50)
            else:
                st.markdown("👤", unsafe_allow_html=True)
        with col_input:
            content = st.text_area(
                t("caption_placeholder"),
                height=150,
                placeholder=t("caption_placeholder"),
                label_visibility="collapsed"
            )
        media_files = st.file_uploader(
            t("add_media"),
            type=["png", "jpg", "jpeg", "gif", "mp4", "mov", "avi"],
            accept_multiple_files=True
        )
        st.caption("⚠️ File size limit: 200MB (Streamlit Cloud). For larger videos, use a link (YouTube, etc.).")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            visibility = st.radio(t("visibility"), [t("public"), t("private")], horizontal=True, index=0)
            is_public = (visibility == t("public"))
        with col3:
            posted = st.form_submit_button(t("post"), use_container_width=True)

        if posted:
            if not content and not media_files:
                st.warning("Please add a caption or media.")
            else:
                if create_post(st.session_state.user.id, content, media_files, is_public):
                    st.rerun()
    st.divider()

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
                    if st.button(t("join_live"), key=f"join_{live['id']}"):
                        st.session_state.viewing_live = live["id"]
                        st.rerun()
                st.divider()
    st.divider()

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
                col_a, col_b, col_c, col_d, col_e = st.columns([1, 4, 2, 1, 1])
                with col_a:
                    avatar = post.get("profiles", {}).get("avatar_url")
                    if avatar:
                        st.image(avatar, width=40)
                    else:
                        st.markdown("👤")
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

                emojis = ["👍", "👎", "❤️", "😂", "😮", "😢", "👏"]
                reaction_counts = post.get("reactions", {})
                summary = " ".join([f"{emoji} {count}" for emoji, count in list(reaction_counts.items())[:3]])
                col_react, col_comments, col_shares = st.columns([2, 1, 1])
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
                    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
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
                        colr1, colr2, colr3, colr4 = st.columns([4, 1, 1, 1])
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

def render_friends_page():
    st.header(t("friends_chat"))

    with st.expander(t("setup_instructions")):
        st.markdown("""
        **If you get "new row violates row-level security policy" when uploading files:**

        1. Go to your Supabase Dashboard → Storage.
        2. For each bucket (`avatars`, `post_media`, `chat_media`), click on the bucket → "Policies".
        3. Add a new policy:
           - Policy name: `Allow authenticated uploads`
           - Allowed operations: `INSERT`
           - Target roles: `authenticated`
           - USING expression: `(auth.role() = 'authenticated')`
        4. Also add a policy for SELECT (reading) if needed:
           - Policy name: `Allow public read`
           - Allowed operations: `SELECT`
           - USING expression: `true`
        """)

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
        st.info(t("no_friends"))
    else:
        for req in st.session_state.friend_requests:
            cols = st.columns([2,1,1])
            with cols[0]:
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
            cols = st.columns([1,4,1,1,1])
            with cols[0]:
                if friend.get('avatar_url'):
                    st.image(friend['avatar_url'], width=30)
                else:
                    st.markdown("👤")
            with cols[1]:
                st.markdown(f"**{friend['full_name']}**")
            with cols[2]:
                if st.button(t("chat"), key=f"chat_{friend['id']}"):
                    st.session_state.selected_chat = friend['id']
                    st.rerun()
            with cols[3]:
                if st.button(t("call"), key=f"call_{friend['id']}"):
                    room = hashlib.md5(f"{st.session_state.user.id}_{friend['id']}_{time.time()}".encode()).hexdigest()[:10]
                    send_message(st.session_state.user.id, friend['id'], f"📞 Join my call: room={room}")
                    start_call(room)
                    st.rerun()
            with cols[4]:
                if st.button(t("profile_btn"), key=f"profile_{friend['id']}"):
                    st.session_state.viewing_profile = friend['id']
                    st.rerun()
            st.divider()

    if st.session_state.selected_chat:
        st.subheader(t("chat"))
        other_id = st.session_state.selected_chat
        other = supabase.table("profiles").select("full_name").eq("id", other_id).single().execute()
        if other.data:
            other_name = other.data["full_name"]
        else:
            other_name = "User"
        st.write(f"{t('chat')} with **{other_name}**")

        messages = load_messages(st.session_state.user.id, other_id)
        for msg in messages:
            if msg["sender_id"] == st.session_state.user.id:
                if msg.get("media_url"):
                    try:
                        if msg.get("media_type") == "image":
                            st.image(msg["media_url"], width=300)
                        elif msg.get("media_type") == "video":
                            st.video(msg["media_url"])
                        else:
                            st.markdown(f"[Media file]({msg['media_url']})")
                    except Exception as e:
                        st.error(f"Error displaying media: {e}")
                        st.markdown(f"[Click to open media]({msg['media_url']})")
                    
                    col1, col2, col3 = st.columns([6,1,1])
                    with col2:
                        if st.button("📤 Share to Feed", key=f"share_own_{msg['id']}"):
                            with st.popover("Create post"):
                                with st.form(f"share_own_form_{msg['id']}"):
                                    caption = st.text_area("Add a caption (optional)")
                                    if st.form_submit_button(t("post")):
                                        media_info = [{"url": msg["media_url"], "type": msg["media_type"]}]
                                        create_post(
                                            st.session_state.user.id,
                                            caption or "",
                                            existing_media_urls=media_info,
                                            is_public=True
                                        )
                                        st.rerun()
                    with col3:
                        st.markdown(f"""
                        <button onclick="navigator.clipboard.writeText('{msg['media_url']}')">🔗 Copy Link</button>
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
                            st.video(msg["media_url"])
                        else:
                            st.markdown(f"[Media file]({msg['media_url']})")
                    except Exception as e:
                        st.error(f"Error displaying media: {e}")
                        st.markdown(f"[Click to open media]({msg['media_url']})")
                    
                    col1, col2, col3 = st.columns([6,1,1])
                    with col2:
                        if st.button("📤 Share to Feed", key=f"share_{msg['id']}"):
                            with st.popover("Create post"):
                                with st.form(f"share_form_{msg['id']}"):
                                    caption = st.text_area("Add a caption (optional)")
                                    if st.form_submit_button(t("post")):
                                        media_info = [{"url": msg["media_url"], "type": msg["media_type"]}]
                                        create_post(
                                            st.session_state.user.id,
                                            caption or "",
                                            existing_media_urls=media_info,
                                            is_public=True
                                        )
                                        st.rerun()
                    with col3:
                        st.markdown(f"""
                        <button onclick="navigator.clipboard.writeText('{msg['media_url']}')">🔗 Copy Link</button>
                        """, unsafe_allow_html=True)
                if msg.get("content"):
                    clickable_content = make_clickable(msg["content"])
                    st.markdown(f"<div style='text-align:left; background:#f1f8e9; padding:5px; border-radius:10px; margin:5px;'><b>{other_name}:</b> {clickable_content}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)

        with st.form("send_message", clear_on_submit=True):
            msg_content = st.text_input(t("send_message"))
            uploaded_file = st.file_uploader(t("add_media"), type=["png","jpg","jpeg","gif","mp4","mov","avi"])
            st.caption("⚠️ File size limit: 200MB (configurable). For larger files, consider external hosting.")
            col1, col2 = st.columns([1,5])
            with col1:
                sent = st.form_submit_button(t("send"))
            if sent:
                if msg_content or uploaded_file:
                    send_message(st.session_state.user.id, other_id, msg_content or "", media_file=uploaded_file)
                    st.rerun()
        if st.button(t("close_chat")):
            st.session_state.selected_chat = None
            st.rerun()
        st.divider()

    if st.session_state.in_call and st.session_state.call_room:
        st.subheader(t("active_call"))
        st.markdown(f"{t('room_id')}: `{st.session_state.call_room}`")
        st.markdown(t("share_room"))
        jitsi_url = f"https://meet.jit.si/{st.session_state.call_room}#config.startWithAudioMuted=false&config.startWithVideoMuted=false"
        st.components.v1.html(f"""
            <iframe src="{jitsi_url}" width="100%" height="500" allow="camera; microphone; fullscreen"></iframe>
        """, height=520)
        if st.button(t("end_call")):
            end_call()
            st.rerun()
    else:
        if st.button(t("start_call")):
            start_call()
            st.rerun()

def render_user_profile(user_id):
    if supabase is None:
        st.error("Database not connected.")
        if st.button(t("back_to_feed")):
            st.session_state.viewing_profile = None
            st.rerun()
        return

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
    col1, col2 = st.columns([1, 2])
    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=150)
        else:
            st.markdown("👤", unsafe_allow_html=True)
        st.markdown(f"**{t('bio')}:** {profile.get('bio', 'No bio')}")
        st.markdown(f"**{t('location')}:** {profile.get('location', 'Unknown')}")
        st.markdown(f"**{t('moncash_phone')}:** {profile.get('moncash_phone', 'Not set')}")
        st.markdown(f"**{t('member_since')}:** {profile.get('join_date', '')[:10]}")
        if st.button(t("chat")):
            st.session_state.selected_chat = user_id
            st.session_state.viewing_profile = None
            st.rerun()
        if st.button(t("back_to_feed")):
            st.session_state.viewing_profile = None
            st.rerun()
    with col2:
        st.subheader(t("feed"))
        posts = load_user_posts(user_id)
        if not posts:
            st.info("This user has no public posts.")
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

def render_map():
    st.header(t("satellite_map"))
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
    st.header(t("profile"))
    if st.session_state.profile is None:
        return
    profile = st.session_state.profile

    col1, col2 = st.columns([1, 2])
    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=200, caption="Profile Picture")
        else:
            st.image("https://via.placeholder.com/200", width=200, caption="No picture")
        uploaded = st.file_uploader(t("change_picture"), type=["png","jpg","jpeg"], label_visibility="collapsed")
        if uploaded:
            url = upload_avatar(st.session_state.user.id, uploaded)
            if url:
                profile["avatar_url"] = url
                update_profile(profile)
                st.success("Avatar updated successfully!")
                st.rerun()
    with col2:
        with st.form("edit_profile"):
            st.markdown("#### Account Information")
            full_name = st.text_input(t("full_name"), value=profile.get("full_name", ""))
            bio = st.text_area(t("bio"), value=profile.get("bio", ""), height=100)
            location = st.text_input(t("location"), value=profile.get("location", ""))
            moncash_phone = st.text_input(t("moncash_phone"), value=profile.get("moncash_phone", ""))
            if st.form_submit_button(t("save_changes"), use_container_width=True):
                profile.update({"full_name": full_name, "bio": bio, "location": location, "moncash_phone": moncash_phone})
                if update_profile(profile):
                    st.success(t("profile"))
                    st.rerun()

    st.divider()
    cola, colb, colc, cold = st.columns(4)
    with cola:
        st.metric(t("posts_count"), len(st.session_state.posts))
    with colb:
        st.metric(t("connections"), profile.get("connections", 0))
    with colc:
        st.metric(t("verified"), "✅" if profile.get("verified", False) else "❌")
    with cold:
        st.metric(t("member_since"), profile.get("join_date", "2024")[:10])

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
            except Exception as e:
                st.warning(f"Error checking participant status: {e}")

            if participant_status == "accepted":
                with st.expander(t("choose_background"), expanded=False):
                    uploaded_bg = st.file_uploader(t("upload_background"), type=["png", "jpg", "jpeg"], key=f"bg_upload_{session_id}")
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

    col1, col2 = st.columns([2, 1])
    with col1:
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
                    channel = stream_url.split("/")[-1].split("?")[0]
                    embed_url = f"https://player.twitch.tv/?channel={channel}&parent={st.request.host}&autoplay=true"
                    st.components.v1.html(f'<iframe src="{embed_url}" height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>', height=410)
                else:
                    st.video(stream_url)
            else:
                st.info("The streamer has not provided a video URL yet.")
        else:
            if is_broadcaster:
                st.success(t("you_are_broadcaster"))
                st.subheader("🎤 Participant Requests")
                try:
                    pending = supabase.table("live_participants").select("*, profiles!live_participants_user_id_fkey(full_name, avatar_url)").eq("session_id", session_id).eq("status", "pending").execute()
                    pending_list = pending.data or []
                except Exception as e:
                    st.error(f"Error loading requests: {e}")
                    pending_list = []

                if pending_list:
                    for req in pending_list:
                        cols = st.columns([3,1,1])
                        with cols[0]:
                            st.markdown(f"**{req['profiles']['full_name']}** wants to join")
                        with cols[1]:
                            if st.button("✅ Accept", key=f"accept_{req['id']}"):
                                supabase.table("live_participants").update({"status": "accepted"}).eq("id", req["id"]).execute()
                                supabase.table("notifications").insert({
                                    "user_id": req["user_id"],
                                    "type": "live_join_accepted",
                                    "message": f"You have been accepted to join the live stream: {session['title']}",
                                    "read": False
                                }).execute()
                                st.rerun()
                        with cols[2]:
                            if st.button("❌ Reject", key=f"reject_{req['id']}"):
                                supabase.table("live_participants").delete().eq("id", req["id"]).execute()
                                st.rerun()
                else:
                    st.info("No pending requests")

                st.subheader("🎤 Active Participants")
                try:
                    accepted = supabase.table("live_participants").select("*, profiles!live_participants_user_id_fkey(full_name, avatar_url)").eq("session_id", session_id).eq("status", "accepted").execute()
                    accepted_list = accepted.data or []
                except Exception as e:
                    st.error(f"Error loading participants: {e}")
                    accepted_list = []

                if accepted_list:
                    for part in accepted_list:
                        cols = st.columns([2,1,1,1])
                        with cols[0]:
                            st.markdown(f"**{part['profiles']['full_name']}**")
                        with cols[1]:
                            if st.button("🔊 Mute", key=f"mute_{part['id']}"):
                                supabase.table("live_participants").update({"status": "muted"}).eq("id", part["id"]).execute()
                                supabase.table("notifications").insert({
                                    "user_id": part["user_id"],
                                    "type": "live_mute",
                                    "message": f"The broadcaster has muted your microphone in {session['title']}",
                                    "read": False
                                }).execute()
                                st.rerun()
                        with cols[2]:
                            if st.button("🔊 Unmute", key=f"unmute_{part['id']}"):
                                supabase.table("live_participants").update({"status": "accepted"}).eq("id", part["id"]).execute()
                                supabase.table("notifications").insert({
                                    "user_id": part["user_id"],
                                    "type": "live_unmute",
                                    "message": f"The broadcaster has unmuted your microphone in {session['title']}",
                                    "read": False
                                }).execute()
                                st.rerun()
                        with cols[3]:
                            if st.button("❌ Remove", key=f"remove_{part['id']}"):
                                supabase.table("live_participants").delete().eq("id", part["id"]).execute()
                                st.rerun()
                else:
                    st.info("No participants yet")
            else:
                st.info(t("you_are_viewer"))

        try:
            base_url = st.request.url.split('?')[0]
        except:
            base_url = "https://home-sweet-home.streamlit.app"
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
            if session["profiles"]["moncash_phone"]:
                st.info(f"{t('gifts_sent_to')}: {session['profiles']['moncash_phone']}")
            else:
                st.warning(t("add_moncash"))

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

def owner_space():
    st.header(t("owner_space"))
    
    if not st.session_state.owner_space_access:
        with st.form("owner_space_login"):
            pwd = st.text_input("Enter Owner Space Password", type="password")
            if st.form_submit_button(t("login_button")):
                if pwd == OWNSPACE_PASSWORD:
                    st.session_state.owner_space_access = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return

    last_seen = get_last_seen_signup()
    new_users = get_new_users(last_seen)
    if new_users:
        send_email_notification(new_users)
        update_last_seen_signup()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([t("dashboard"), t("new_users"), t("post_moderation"), t("client_payments"), t("gift_management")])

    with tab1:
        st.subheader(t("owner_dashboard"))
        real_balance = None
        if BACKEND_API_URL and BACKEND_API_URL != "https://your-backend.com":
            try:
                headers = {"X-API-Key": BACKEND_API_KEY}
                resp = requests.get(f"{BACKEND_API_URL}/api/balance", headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    real_balance = data.get("balance", 0.0)
                else:
                    st.warning("Could not fetch real balance from backend.")
            except Exception as e:
                st.warning(f"Backend unreachable: {e}")
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
            amount = st.number_input(
                t("amount_transfer"),
                min_value=1.0,
                max_value=float(real_balance),
                value=min(10.0, float(real_balance)),
                step=10.0,
                format="%.2f"
            )
            if st.button(t("transfer"), use_container_width=True):
                if amount <= 0:
                    st.error("Enter a valid amount.")
                else:
                    with st.spinner("Processing transfer..."):
                        try:
                            headers = {"X-API-Key": BACKEND_API_KEY, "Content-Type": "application/json"}
                            payload = {
                                "amount": amount,
                                "recipient_phone": MONCASH_NUM
                            }
                            resp = requests.post(f"{BACKEND_API_URL}/api/transfer", headers=headers, json=payload, timeout=10)
                            if resp.status_code == 200:
                                data = resp.json()
                                st.success(f"✅ Transfer initiated! Transaction ID: {data.get('transaction_id')}")
                            else:
                                st.error(f"Transfer failed: {resp.text}")
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("To enable real transfers, set up your backend and configure the secrets.")

    with tab2:
        st.subheader(t("new_users"))
        st.markdown("All recent user signups. Click refresh to update, and download the report at any time.")
        
        try:
            with st.spinner("Loading user data..."):
                response = supabase.table("profiles").select(
                    "id, full_name, avatar_url, join_date, location, bio"
                ).order("join_date", desc=True).limit(100).execute()
                recent_users = response.data if response.data else []
        except Exception as e:
            st.error(f"Failed to load user data: {e}")
            recent_users = []
        
        if recent_users:
            display_data = []
            for u in recent_users:
                display_data.append({
                    "Full Name": u.get('full_name', 'N/A'),
                    "User ID": u['id'],
                    "Joined": u.get('join_date', '')[:16] if u.get('join_date') else 'Unknown',
                    "Location": u.get('location', 'Not set'),
                    "Bio": u.get('bio', '')[:50] + ('...' if len(u.get('bio', '')) > 50 else '')
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

    with tab3:
        st.subheader(t("post_moderation"))
        st.markdown("Review all posts (public & private) and take action if needed.")
        try:
            posts = supabase.table("posts").select("*").order("created_at", desc=True).execute()
            all_posts = posts.data or []
            user_ids = {p["user_id"] for p in all_posts}
            profiles = {}
            if user_ids:
                profiles_resp = supabase.table("profiles").select("id, full_name, avatar_url").in_("id", list(user_ids)).execute()
                for p in profiles_resp.data or []:
                    profiles[p["id"]] = p
            for p in all_posts:
                prof = profiles.get(p["user_id"], {})
                p["profiles"] = {
                    "full_name": prof.get("full_name", "Unknown"),
                    "avatar_url": prof.get("avatar_url"),
                    "id": p["user_id"]
                }
        except Exception as e:
            st.error(f"Failed to load posts: {e}")
            all_posts = []

        if not all_posts:
            st.info("No posts found.")
        else:
            if "warn_post_id" not in st.session_state:
                st.session_state.warn_post_id = None
            for post in all_posts:
                with st.container():
                    cols = st.columns([2, 4, 2, 1, 1])
                    with cols[0]:
                        st.markdown(f"**User:** {post['profiles']['full_name']}")
                    with cols[1]:
                        content = post.get('content', '')[:100] + "..." if post.get('content') and len(post['content']) > 100 else post.get('content', '')
                        st.markdown(f"**Content:** {content}")
                    with cols[2]:
                        st.markdown(f"**Visibility:** {'Public' if post.get('is_public', True) else 'Private'}")
                        st.caption(post['created_at'][:16])
                    with cols[3]:
                        if st.button(t("delete_post"), key=f"del_{post['id']}"):
                            if delete_post(post['id']):
                                st.success("Post deleted.")
                                st.rerun()
                            else:
                                st.error("Delete failed.")
                    with cols[4]:
                        if st.button("⚠️ Warn", key=f"warn_{post['id']}"):
                            st.session_state.warn_post_id = post['id']
                            st.rerun()

                    if st.session_state.warn_post_id == post['id']:
                        with st.form(key=f"warn_form_{post['id']}"):
                            default_msg = f"Your post '{post.get('content','')[:50]}...' contains sensitive content and has been removed. Please review our community guidelines."
                            warn_msg = st.text_area("Warning message", value=default_msg, height=100)
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Send Warning"):
                                    success = send_message(
                                        st.session_state.user.id,
                                        post['user_id'],
                                        f"[MODERATION] {warn_msg}"
                                    )
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

    with tab4:
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

    with tab5:
        st.subheader(t("gift_management"))
        st.markdown("View all completed gifts and process payouts to streamers.")

        if supabase is None:
            st.warning("Supabase not connected.")
            return

        try:
            gifts = supabase.table("live_gifts").select("*").eq("status", "completed").order("created_at", desc=True).execute()
            gifts_data = gifts.data if gifts.data else []
        except Exception as e:
            st.error(f"Failed to load gifts: {e}")
            gifts_data = []

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

    st.divider()
    st.markdown(f"### {t('contact_support')}")
    st.markdown("Email: `deslandes78@gmail.com`  \nWhatsApp: `+50947385663`")

    if st.button(t("logout_owner")):
        st.session_state.owner_space_access = False
        st.rerun()

# ========== MAIN APP ==========
def main_app():
    with st.sidebar:
        if st.session_state.logged_in:
            st.success("✅ Logged in")
        else:
            st.info("🔓 Not logged in")
        st.divider()

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

        lang_options = {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "ht": "Kreyòl Ayisyen"
        }
        selected_lang = st.selectbox(
            t("voice_lang"),
            options=list(lang_options.keys()),
            format_func=lambda x: lang_options[x],
            index=list(lang_options.keys()).index(st.session_state.language)
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

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
                        if st.button("📺 YouTube", key="yt"):
                            platform = "YouTube"
                    with col2:
                        if st.button("📘 Facebook", key="fb"):
                            platform = "Facebook"
                    with col3:
                        if st.button("🎮 Twitch", key="tw"):
                            platform = "Twitch"
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
                                    if platform == 'inapp':
                                        st.success(t("you_are_live"))
                                    else:
                                        st.success(t("you_are_live"))
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
                voice_map = {
                    "en": "en-US-JennyNeural",
                    "fr": "fr-FR-DeniseNeural",
                    "es": "es-ES-ElviraNeural",
                    "ht": "ht-HT-FabriceNeural"
                }
                voice = voice_map.get(st.session_state.language, "en-US-JennyNeural")
                text = t("app_explanation")
                audio_file = generate_audio(text, voice)
                if audio_file:
                    play_audio(audio_file)
                else:
                    st.error("Failed to generate audio.")

        st.divider()

        page_keys = ["feed", "friends_chat", "satellite_map", "profile", "owner_space"]
        page_titles = {key: t(key) for key in page_keys}
        if "current_page" not in st.session_state:
            st.session_state.current_page = "feed"
        if st.session_state.current_page not in page_keys:
            st.session_state.current_page = "feed"

        selected_title = st.selectbox(
            "Navigate",
            options=[page_titles[key] for key in page_keys],
            index=page_keys.index(st.session_state.current_page),
        )
        selected_key = next(key for key, title in page_titles.items() if title == selected_title)
        st.session_state.current_page = selected_key

        st.divider()
        st.markdown("### 🕊️ Owner Space")
        if st.session_state.owner_space_access:
            st.success("✅ Access granted")
            if st.button("🔑 Go to Owner Dashboard", use_container_width=True):
                st.session_state.current_page = "owner_space"
                st.rerun()
        else:
            with st.form("owner_sidebar_form"):
                pwd = st.text_input("Password", type="password", placeholder="Enter owner password")
                if st.form_submit_button("🔓 Unlock Owner Space", use_container_width=True):
                    if pwd == OWNSPACE_PASSWORD:
                        st.session_state.owner_space_access = True
                        st.rerun()
                    else:
                        st.error("Invalid password")

    page_functions = {
        "feed": render_feed,
        "friends_chat": render_friends_page,
        "satellite_map": render_map,
        "profile": render_profile,
        "owner_space": owner_space
    }
    page_functions.get(st.session_state.current_page, render_feed)()

# ========== ENTRY ==========
if __name__ == "__main__":
    # If the user is logged in, show the home title and the main app
    if st.session_state.logged_in:
        st.markdown(f"""
        <div class="home-title">
            <h1>{t('home_title')}</h1>
            <div style="text-align:center; font-size:2.5rem; font-weight:bold; 
                 background: linear-gradient(135deg, #00209F 0%, #00209F 50%, #D21034 50%, #D21034 100%); 
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                 display: inline-block; padding: 0 20px; margin: 0.2rem 0;">{t('home_haiti')}</div>
            <p>{t('home_subtitle')}</p>
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
