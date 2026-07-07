"""
Home Sweet Home - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 77.0.0 (Full rewrite with new name, theme, and global password)
"""
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

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Home Sweet Home", page_icon="🏠", layout="wide")

# ====== GLOBAL APP PASSWORD PROTECTION ======
APP_PASSWORD = st.secrets.get("APP_PASSWORD")  # Set in secrets to enable

if APP_PASSWORD:
    if "app_authenticated" not in st.session_state:
        st.session_state.app_authenticated = False

    if not st.session_state.app_authenticated:
        st.markdown(
            """
            <style>
                .stApp { background: linear-gradient(145deg, #E3F2FD, #FFCDD2); }
                .login-box { max-width: 400px; margin: 100px auto; padding: 30px; background: rgba(255,255,255,0.7); border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.1); text-align: center; }
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.container():
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            st.image("https://github.com/Deslandes1/Let-s-Learn-Mathematics-with-Gesner/blob/main/Gesner%20Deslandes.png?raw=true", width=100)
            st.markdown("### 🏠 Home Sweet Home")
            st.markdown("Enter the app password to continue.")
            with st.form("app_password_form"):
                pwd = st.text_input("Password", type="password", placeholder="Enter app password")
                if st.form_submit_button("🔓 Unlock"):
                    if pwd == APP_PASSWORD:
                        st.session_state.app_authenticated = True
                        st.rerun()
                    else:
                        st.error("❌ Invalid password")
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

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

BACKEND_API_URL = st.secrets.get("BACKEND_API_URL", "https://your-backend.com")
BACKEND_API_KEY = st.secrets.get("BACKEND_API_KEY", "")
EXCHANGE_RATE_API = st.secrets.get("EXCHANGE_RATE_API", "https://api.exchangerate-api.com/v4/latest/USD")

# Optional email settings
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

# ====== LANGUAGE DICTIONARY (FULL) ======
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
        "location": "Ubicación",
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
    },
    "pt": {
        "login_title": "Entrar",
        "signup_title": "Cadastrar",
        "forgot_password": "Esqueci a senha",
        "email": "E-mail",
        "password": "Senha",
        "full_name": "Nome completo",
        "remember_me": "Lembrar‑me",
        "login_button": "🚀 Entrar",
        "signup_button": "📝 Cadastrar",
        "send_reset_link": "Enviar link de redefinição",
        "phone_method": "Telefone (OTP)",
        "email_method": "E‑mail",
        "phone_number": "Número de telefone (apenas dígitos, ex: 50947385663)",
        "send_otp": "📲 Enviar OTP",
        "enter_otp": "Digite o código OTP de 6 dígitos",
        "verify_login": "✅ Verificar e entrar",
        "back_resend": "← Voltar / Reenviar OTP",
        "feed": "📡 Feed",
        "friends_chat": "👥 Amigos e chat",
        "satellite_map": "🛰️ Mapa de satélite",
        "profile": "👤 Perfil",
        "owner_space": "🕊️ Espaço do proprietário",
        "logout": "🚪 Sair",
        "system_health": "🛡️ Saúde do sistema",
        "signal": "📡 Sinal",
        "latency": "⏱️ Latência",
        "quality": "📊 Qualidade",
        "uptime": "⏰ Tempo de atividade",
        "encrypted": "🔒 Status: CRIPTOGRAFADO",
        "compensation": "💰 Compensação",
        "logged_in_as": "👤 Conectado como",
        "go_live": "Ir ao vivo",
        "external_platform": "Plataforma externa (YouTube/Facebook/Twitch)",
        "in_app_camera": "Câmera integrada",
        "select_platform": "Selecionar plataforma",
        "live_title": "Título do ao vivo",
        "create_live_session": "Criar sessão ao vivo",
        "you_are_live": "🔴 Você está ao vivo!",
        "end_live_session": "Encerrar sessão ao vivo",
        "set_stream_url": "📹 Definir URL do stream",
        "paste_url": "Cole a URL da sua transmissão ao vivo",
        "update_url": "Atualizar URL",
        "shareable_link": "Link compartilhável",
        "live_chat_gifts": "Chat ao vivo e presentes",
        "send_gift": "🎁 Enviar um presente",
        "add_moncash": "Adicione seu número MonCash no perfil para enviar presentes.",
        "total_gifts": "Total de presentes recebidos",
        "gifts_sent_to": "Os presentes serão enviados para seu MonCash",
        "write_comment": "Escreva um comentário...",
        "send": "Enviar",
        "back_to_feed": "Voltar ao feed",
        "create_post": "Criar uma publicação",
        "caption_placeholder": "Escreva algo... ou cole um link de vídeo",
        "add_media": "Adicionar imagens ou vídeos (opcional)",
        "visibility": "Visibilidade",
        "public": "Público",
        "private": "Privado",
        "post": "🚀 Publicar",
        "delete_post": "🗑️ Excluir",
        "comments": "Comentários",
        "reply": "💬 Responder",
        "post_reply": "Publicar resposta",
        "your_reply": "Sua resposta",
        "clear_error": "Limpar erro",
        "join_live": "Participar ao vivo",
        "watch_stream": "▶ ASSISTIR",
        "start_broadcast": "▶ INICIAR TRANSMISSÃO",
        "stop_broadcast": "■ PARAR TRANSMISSÃO",
        "you_are_broadcaster": "✅ Você é o transmissor. Use os controles abaixo para começar.",
        "you_are_viewer": "👀 Você é espectador. Clique em 'Assistir' para ver o vídeo.",
        "choose_background": "🎨 Filtros de fundo",
        "bg_option": "FND",
        "upload_background": "Ou envie sua própria imagem",
        "background_set": "Fundo definido!",
        "ready_to_start": "Pronto para começar. Clique no botão acima.",
        "camera_access": "📷 Solicitando acesso à câmera...",
        "camera_granted": "✅ Acesso à câmera concedido. Conectando ao servidor peer...",
        "broadcasting": "✅ Transmitindo ao vivo! Seu ID peer",
        "peer_error": "❌ Erro peer",
        "error": "❌ Erro",
        "broadcast_ended": "Transmissão encerrada",
        "initializing": "Inicializando...",
        "connected_requesting": "Conectado. Solicitando stream do transmissor...",
        "calling": "Chamando",
        "received_stream": "Stream recebido",
        "now_watching": "✅ Agora você está assistindo ao vivo",
        "call_error": "❌ Erro na chamada",
        "call_ended": "Chamada encerrada",
        "disconnected": "Desconectado. Por favor, recarregue.",
        "send_message": "Enviar",
        "close_chat": "Fechar chat",
        "active_call": "📞 Chamada ativa",
        "room_id": "ID da sala",
        "share_room": "Compartilhe este ID com a pessoa que você quer chamar.",
        "start_call": "Iniciar nova chamada",
        "end_call": "Encerrar chamada",
        "find_users": "🔍 Encontrar usuários",
        "search_by_name": "Pesquisar por nome",
        "add_friend": "➕ Adicionar amigo",
        "view_profile": "👤 Ver perfil",
        "friend_requests": "📨 Solicitações de amizade recebidas",
        "accept": "✅ Aceitar",
        "reject": "❌ Rejeitar",
        "your_friends": "👥 Seus amigos",
        "no_friends": "Você ainda não tem amigos",
        "chat": "💬 Chat",
        "call": "📞 Chamada",
        "profile_btn": "👤 Perfil",
        "edit_profile": "Editar perfil",
        "save_changes": "💾 Salvar alterações",
        "change_picture": "📸 Trocar foto",
        "bio": "Bio",
        "location": "Localização",
        "moncash_phone": "Número MonCash (para receber presentes)",
        "posts_count": "Publicações",
        "connections": "Conexões",
        "verified": "Verificado",
        "member_since": "Membro desde",
        "dashboard": "💰 Painel",
        "new_users": "📈 Novos usuários",
        "post_moderation": "🛡️ Moderação de publicações",
        "client_payments": "📥 Pagamentos de clientes",
        "gift_management": "🎁 Gestão de presentes",
        "owner_dashboard": "🔐 Painel do proprietário",
        "balance": "Saldo MonCash Business",
        "transfer_funds": "💰 Transferir fundos para sua conta",
        "amount_transfer": "Valor a transferir ($)",
        "transfer": "🚀 Transferir para MonCash",
        "no_gifts": "Ainda não há presentes.",
        "payout_summary": "Resumo de pagamentos",
        "total_gifts_htg": "Total de presentes (HTG)",
        "mark_paid": "Marcar tudo como pago (simulado)",
        "contact_support": "📬 Contato para suporte / pagamentos grandes",
        "logout_owner": "Sair do espaço do proprietário",
        "setup_instructions": "ℹ️ Instruções de configuração (se o upload falhar)",
        "storage_error": "Erro de permissão de armazenamento: configure políticas RLS para o bucket 'avatars'.",
    },
    "ru": {
        "login_title": "Вход",
        "signup_title": "Регистрация",
        "forgot_password": "Забыли пароль",
        "email": "Эл. почта",
        "password": "Пароль",
        "full_name": "Полное имя",
        "remember_me": "Запомнить меня",
        "login_button": "🚀 Войти",
        "signup_button": "📝 Зарегистрироваться",
        "send_reset_link": "Отправить ссылку для сброса",
        "phone_method": "Телефон (OTP)",
        "email_method": "Эл. почта",
        "phone_number": "Номер телефона (только цифры, напр. 50947385663)",
        "send_otp": "📲 Отправить OTP",
        "enter_otp": "Введите 6‑значный код OTP",
        "verify_login": "✅ Проверить и войти",
        "back_resend": "← Назад / Отправить повторно",
        "feed": "📡 Лента",
        "friends_chat": "👥 Друзья и чат",
        "satellite_map": "🛰️ Спутниковая карта",
        "profile": "👤 Профиль",
        "owner_space": "🕊️ Пространство владельца",
        "logout": "🚪 Выйти",
        "system_health": "🛡️ Состояние системы",
        "signal": "📡 Сигнал",
        "latency": "⏱️ Задержка",
        "quality": "📊 Качество",
        "uptime": "⏰ Время работы",
        "encrypted": "🔒 Статус: ЗАШИФРОВАНО",
        "compensation": "💰 Компенсация",
        "logged_in_as": "👤 Вы вошли как",
        "go_live": "Начать прямой эфир",
        "external_platform": "Внешняя платформа (YouTube/Facebook/Twitch)",
        "in_app_camera": "Встроенная камера",
        "select_platform": "Выбрать платформу",
        "live_title": "Название эфира",
        "create_live_session": "Создать сеанс прямого эфира",
        "you_are_live": "🔴 Вы в эфире!",
        "end_live_session": "Завершить эфир",
        "set_stream_url": "📹 Установить URL потока",
        "paste_url": "Вставьте URL вашей трансляции",
        "update_url": "Обновить URL",
        "shareable_link": "Ссылка для поделиться",
        "live_chat_gifts": "Чат и подарки",
        "send_gift": "🎁 Отправить подарок",
        "add_moncash": "Добавьте номер MonCash в профиль, чтобы отправлять подарки.",
        "total_gifts": "Всего получено подарков",
        "gifts_sent_to": "Подарки будут отправлены на ваш MonCash",
        "write_comment": "Напишите комментарий...",
        "send": "Отправить",
        "back_to_feed": "Назад к ленте",
        "create_post": "Создать пост",
        "caption_placeholder": "Напишите что‑нибудь... или вставьте ссылку на видео",
        "add_media": "Добавить изображения или видео (необязательно)",
        "visibility": "Видимость",
        "public": "Публичный",
        "private": "Приватный",
        "post": "🚀 Опубликовать",
        "delete_post": "🗑️ Удалить",
        "comments": "Комментарии",
        "reply": "💬 Ответить",
        "post_reply": "Опубликовать ответ",
        "your_reply": "Ваш ответ",
        "clear_error": "Очистить ошибку",
        "join_live": "Присоединиться к эфиру",
        "watch_stream": "▶ СМОТРЕТЬ",
        "start_broadcast": "▶ НАЧАТЬ ТРАНСЛЯЦИЮ",
        "stop_broadcast": "■ ОСТАНОВИТЬ",
        "you_are_broadcaster": "✅ Вы ведущий. Используйте элементы управления ниже, чтобы начать.",
        "you_are_viewer": "👀 Вы зритель. Нажмите 'Смотреть', чтобы увидеть видео.",
        "choose_background": "🎨 Фоновые фильтры",
        "bg_option": "ФОН",
        "upload_background": "Или загрузите своё изображение",
        "background_set": "Фон установлен!",
        "ready_to_start": "Готов к началу. Нажмите кнопку выше.",
        "camera_access": "📷 Запрос доступа к камере...",
        "camera_granted": "✅ Доступ к камере получен. Подключение к серверу...",
        "broadcasting": "✅ Трансляция идёт! Ваш ID",
        "peer_error": "❌ Ошибка пира",
        "error": "❌ Ошибка",
        "broadcast_ended": "Трансляция завершена",
        "initializing": "Инициализация...",
        "connected_requesting": "Подключено. Запрос потока от ведущего...",
        "calling": "Вызов",
        "received_stream": "Поток получен",
        "now_watching": "✅ Вы смотрите прямой эфир",
        "call_error": "❌ Ошибка вызова",
        "call_ended": "Вызов завершён",
        "disconnected": "Отключено. Пожалуйста, обновите страницу.",
        "send_message": "Отправить",
        "close_chat": "Закрыть чат",
        "active_call": "📞 Активный вызов",
        "room_id": "ID комнаты",
        "share_room": "Поделитесь этим ID с человеком, которому хотите позвонить.",
        "start_call": "Начать новый вызов",
        "end_call": "Завершить вызов",
        "find_users": "🔍 Поиск пользователей",
        "search_by_name": "Поиск по имени",
        "add_friend": "➕ Добавить в друзья",
        "view_profile": "👤 Посмотреть профиль",
        "friend_requests": "📨 Запросы в друзья",
        "accept": "✅ Принять",
        "reject": "❌ Отклонить",
        "your_friends": "👥 Ваши друзья",
        "no_friends": "У вас ещё нет друзей",
        "chat": "💬 Чат",
        "call": "📞 Звонок",
        "profile_btn": "👤 Профиль",
        "edit_profile": "Редактировать профиль",
        "save_changes": "💾 Сохранить",
        "change_picture": "📸 Сменить фото",
        "bio": "О себе",
        "location": "Местоположение",
        "moncash_phone": "Номер MonCash (для получения подарков)",
        "posts_count": "Посты",
        "connections": "Связи",
        "verified": "Подтверждено",
        "member_since": "Участник с",
        "dashboard": "💰 Панель",
        "new_users": "📈 Новые пользователи",
        "post_moderation": "🛡️ Модерация постов",
        "client_payments": "📥 Платежи клиентов",
        "gift_management": "🎁 Управление подарками",
        "owner_dashboard": "🔐 Панель владельца",
        "balance": "Баланс MonCash Business",
        "transfer_funds": "💰 Перевести средства на свой счёт",
        "amount_transfer": "Сумма для перевода ($)",
        "transfer": "🚀 Перевести на MonCash",
        "no_gifts": "Подарков пока нет.",
        "payout_summary": "Сводка выплат",
        "total_gifts_htg": "Всего подарков (HTG)",
        "mark_paid": "Отметить все как оплаченные (симуляция)",
        "contact_support": "📬 Контакты для поддержки / крупных платежей",
        "logout_owner": "Выйти из пространства владельца",
        "setup_instructions": "ℹ️ Инструкции по настройке (если загрузка не удалась)",
        "storage_error": "Ошибка разрешения хранилища: настройте политики RLS для бакета 'avatars'.",
    },
    "ar": {
        "login_title": "تسجيل الدخول",
        "signup_title": "إنشاء حساب",
        "forgot_password": "نسيت كلمة المرور",
        "email": "البريد الإلكتروني",
        "password": "كلمة المرور",
        "full_name": "الاسم الكامل",
        "remember_me": "تذكرني",
        "login_button": "🚀 تسجيل الدخول",
        "signup_button": "📝 إنشاء حساب",
        "send_reset_link": "إرسال رابط إعادة التعيين",
        "phone_method": "الهاتف (OTP)",
        "email_method": "البريد الإلكتروني",
        "phone_number": "رقم الهاتف (أرقام فقط، مثال: 50947385663)",
        "send_otp": "📲 إرسال OTP",
        "enter_otp": "أدخل رمز OTP المكون من 6 أرقام",
        "verify_login": "✅ تحقق وتسجيل الدخول",
        "back_resend": "← رجوع / إعادة إرسال OTP",
        "feed": "📡 التغذية",
        "friends_chat": "👥 الأصدقاء والمحادثة",
        "satellite_map": "🛰️ خريطة الأقمار الصناعية",
        "profile": "👤 الملف الشخصي",
        "owner_space": "🕊️ مساحة المالك",
        "logout": "🚪 تسجيل الخروج",
        "system_health": "🛡️ صحة النظام",
        "signal": "📡 الإشارة",
        "latency": "⏱️ زمن الاستجابة",
        "quality": "📊 الجودة",
        "uptime": "⏰ وقت التشغيل",
        "encrypted": "🔒 الحالة: مشفر",
        "compensation": "💰 التعويض",
        "logged_in_as": "👤 تم تسجيل الدخول باسم",
        "go_live": "بدء البث المباشر",
        "external_platform": "منصة خارجية (YouTube/Facebook/Twitch)",
        "in_app_camera": "الكاميرا المدمجة",
        "select_platform": "اختر المنصة",
        "live_title": "عنوان البث",
        "create_live_session": "إنشاء جلسة بث مباشر",
        "you_are_live": "🔴 أنت على الهواء!",
        "end_live_session": "إنهاء البث",
        "set_stream_url": "📹 تعيين عنوان URL للبث",
        "paste_url": "الصق رابط البث المباشر",
        "update_url": "تحديث الرابط",
        "shareable_link": "رابط قابل للمشاركة",
        "live_chat_gifts": "الدردشة والهدايا",
        "send_gift": "🎁 إرسال هدية",
        "add_moncash": "أضف رقم MonCash في ملفك الشخصي لإرسال الهدايا.",
        "total_gifts": "إجمالي الهدايا المستلمة",
        "gifts_sent_to": "سيتم إرسال الهدايا إلى MonCash الخاص بك",
        "write_comment": "اكتب تعليقاً...",
        "send": "إرسال",
        "back_to_feed": "العودة إلى التغذية",
        "create_post": "إنشاء منشور",
        "caption_placeholder": "اكتب شيئاً... أو الصق رابط فيديو",
        "add_media": "إضافة صور أو فيديو (اختياري)",
        "visibility": "الرؤية",
        "public": "عام",
        "private": "خاص",
        "post": "🚀 نشر",
        "delete_post": "🗑️ حذف",
        "comments": "التعليقات",
        "reply": "💬 رد",
        "post_reply": "نشر الرد",
        "your_reply": "ردك",
        "clear_error": "مسح الخطأ",
        "join_live": "انضم إلى البث",
        "watch_stream": "▶ شاهد البث",
        "start_broadcast": "▶ بدء البث",
        "stop_broadcast": "■ إيقاف البث",
        "you_are_broadcaster": "✅ أنت المذيع. استخدم عناصر التحكم أدناه لبدء البث.",
        "you_are_viewer": "👀 أنت مشاهد. انقر على 'شاهد البث' لمشاهدة الفيديو.",
        "choose_background": "🎨 مرشحات الخلفية",
        "bg_option": "خلفية",
        "upload_background": "أو حمِّل صورتك الخاصة",
        "background_set": "تم تعيين الخلفية!",
        "ready_to_start": "جاهز للبدء. انقر على الزر أعلاه.",
        "camera_access": "📷 طلب الوصول إلى الكاميرا...",
        "camera_granted": "✅ تم منح الوصول إلى الكاميرا. الاتصال بخادم النظير...",
        "broadcasting": "✅ البث المباشر قيد التشغيل! معرف النظير الخاص بك",
        "peer_error": "❌ خطأ في النظير",
        "error": "❌ خطأ",
        "broadcast_ended": "انتهى البث",
        "initializing": "جاري التهيئة...",
        "connected_requesting": "متصل. طلب البث من المذيع...",
        "calling": "جارٍ الاتصال",
        "received_stream": "تم استلام البث",
        "now_watching": "✅ أنت تشاهد البث المباشر الآن",
        "call_error": "❌ خطأ في المكالمة",
        "call_ended": "انتهت المكالمة",
        "disconnected": "تم قطع الاتصال. يرجى التحديث.",
        "send_message": "إرسال",
        "close_chat": "إغلاق الدردشة",
        "active_call": "📞 مكالمة نشطة",
        "room_id": "معرف الغرفة",
        "share_room": "شارك هذا المعرف مع الشخص الذي تريد الاتصال به.",
        "start_call": "بدء مكالمة جديدة",
        "end_call": "إنهاء المكالمة",
        "find_users": "🔍 البحث عن مستخدمين",
        "search_by_name": "البحث بالاسم",
        "add_friend": "➕ إضافة صديق",
        "view_profile": "👤 عرض الملف الشخصي",
        "friend_requests": "📨 طلبات الصداقة المستلمة",
        "accept": "✅ قبول",
        "reject": "❌ رفض",
        "your_friends": "👥 أصدقاؤك",
        "no_friends": "ليس لديك أصدقاء بعد",
        "chat": "💬 دردشة",
        "call": "📞 مكالمة",
        "profile_btn": "👤 ملف شخصي",
        "edit_profile": "تعديل الملف الشخصي",
        "save_changes": "💾 حفظ التغييرات",
        "change_picture": "📸 تغيير الصورة",
        "bio": "نبذة",
        "location": "الموقع",
        "moncash_phone": "رقم MonCash (لاستقبال الهدايا)",
        "posts_count": "المنشورات",
        "connections": "الاتصالات",
        "verified": "موثق",
        "member_since": "عضو منذ",
        "dashboard": "💰 لوحة التحكم",
        "new_users": "📈 مستخدمين جدد",
        "post_moderation": "🛡️ مراقبة المنشورات",
        "client_payments": "📥 مدفوعات العملاء",
        "gift_management": "🎁 إدارة الهدايا",
        "owner_dashboard": "🔐 لوحة تحكم المالك",
        "balance": "رصيد MonCash Business",
        "transfer_funds": "💰 تحويل الأموال إلى حسابك",
        "amount_transfer": "المبلغ المراد تحويله ($)",
        "transfer": "🚀 تحويل إلى MonCash",
        "no_gifts": "لا توجد هدايا بعد.",
        "payout_summary": "ملخص المدفوعات",
        "total_gifts_htg": "إجمالي الهدايا (HTG)",
        "mark_paid": "تحديد الكل كمدفوع (محاكاة)",
        "contact_support": "📬 اتصل بالدعم / المدفوعات الكبيرة",
        "logout_owner": "تسجيل الخروج من مساحة المالك",
        "setup_instructions": "ℹ️ إرشادات الإعداد (إذا فشل الرفع)",
        "storage_error": "خطأ في إذن التخزين: يرجى إعداد سياسات RLS لحاوية 'avatars'.",
    },
    "zh": {
        "login_title": "登录",
        "signup_title": "注册",
        "forgot_password": "忘记密码",
        "email": "邮箱",
        "password": "密码",
        "full_name": "全名",
        "remember_me": "记住我",
        "login_button": "🚀 登录",
        "signup_button": "📝 注册",
        "send_reset_link": "发送重置链接",
        "phone_method": "手机 (OTP)",
        "email_method": "邮箱",
        "phone_number": "手机号码（仅数字，例如 50947385663）",
        "send_otp": "📲 发送验证码",
        "enter_otp": "输入6位验证码",
        "verify_login": "✅ 验证并登录",
        "back_resend": "← 返回 / 重新发送",
        "feed": "📡 动态",
        "friends_chat": "👥 好友与聊天",
        "satellite_map": "🛰️ 卫星地图",
        "profile": "👤 个人资料",
        "owner_space": "🕊️ 所有者空间",
        "logout": "🚪 登出",
        "system_health": "🛡️ 系统健康",
        "signal": "📡 信号",
        "latency": "⏱️ 延迟",
        "quality": "📊 质量",
        "uptime": "⏰ 运行时间",
        "encrypted": "🔒 状态：已加密",
        "compensation": "💰 补偿",
        "logged_in_as": "👤 登录为",
        "go_live": "开始直播",
        "external_platform": "外部平台 (YouTube/Facebook/Twitch)",
        "in_app_camera": "应用内相机",
        "select_platform": "选择平台",
        "live_title": "直播标题",
        "create_live_session": "创建直播会话",
        "you_are_live": "🔴 你正在直播！",
        "end_live_session": "结束直播",
        "set_stream_url": "📹 设置直播流URL",
        "paste_url": "粘贴你的直播流URL",
        "update_url": "更新URL",
        "shareable_link": "可分享链接",
        "live_chat_gifts": "直播聊天与礼物",
        "send_gift": "🎁 发送礼物",
        "add_moncash": "在你的个人资料中添加MonCash号码以发送礼物。",
        "total_gifts": "收到的礼物总数",
        "gifts_sent_to": "礼物将发送到你的MonCash",
        "write_comment": "写评论...",
        "send": "发送",
        "back_to_feed": "返回动态",
        "create_post": "创建帖子",
        "caption_placeholder": "写点什么... 或粘贴视频链接",
        "add_media": "添加图片或视频（可选）",
        "visibility": "可见性",
        "public": "公开",
        "private": "私密",
        "post": "🚀 发布",
        "delete_post": "🗑️ 删除",
        "comments": "评论",
        "reply": "💬 回复",
        "post_reply": "发布回复",
        "your_reply": "你的回复",
        "clear_error": "清除错误",
        "join_live": "加入直播",
        "watch_stream": "▶ 观看直播",
        "start_broadcast": "▶ 开始直播",
        "stop_broadcast": "■ 停止直播",
        "you_are_broadcaster": "✅ 你是主播。使用下面的控件开始直播。",
        "you_are_viewer": "👀 你是观众。点击“观看直播”观看视频。",
        "choose_background": "🎨 背景滤镜",
        "bg_option": "背景",
        "upload_background": "或上传你自己的图片",
        "background_set": "背景已设置！",
        "ready_to_start": "准备开始。点击上面的按钮。",
        "camera_access": "📷 请求相机访问...",
        "camera_granted": "✅ 相机访问已授予。正在连接对等服务器...",
        "broadcasting": "✅ 直播中！你的对等ID",
        "peer_error": "❌ 对等错误",
        "error": "❌ 错误",
        "broadcast_ended": "直播结束",
        "initializing": "初始化...",
        "connected_requesting": "已连接。正在请求主播的流...",
        "calling": "正在呼叫",
        "received_stream": "已接收流",
        "now_watching": "✅ 你现在正在观看直播",
        "call_error": "❌ 呼叫错误",
        "call_ended": "通话结束",
        "disconnected": "已断开。请刷新。",
        "send_message": "发送",
        "close_chat": "关闭聊天",
        "active_call": "📞 进行中的通话",
        "room_id": "房间ID",
        "share_room": "将此ID分享给你想通话的人。",
        "start_call": "开始新通话",
        "end_call": "结束通话",
        "find_users": "🔍 查找用户",
        "search_by_name": "按姓名搜索",
        "add_friend": "➕ 添加好友",
        "view_profile": "👤 查看个人资料",
        "friend_requests": "📨 收到的好友请求",
        "accept": "✅ 接受",
        "reject": "❌ 拒绝",
        "your_friends": "👥 你的好友",
        "no_friends": "你还没有好友",
        "chat": "💬 聊天",
        "call": "📞 通话",
        "profile_btn": "👤 个人资料",
        "edit_profile": "编辑个人资料",
        "save_changes": "💾 保存更改",
        "change_picture": "📸 更换头像",
        "bio": "简介",
        "location": "位置",
        "moncash_phone": "MonCash号码（用于接收礼物）",
        "posts_count": "帖子数",
        "connections": "连接数",
        "verified": "已验证",
        "member_since": "加入于",
        "dashboard": "💰 仪表盘",
        "new_users": "📈 新用户",
        "post_moderation": "🛡️ 帖子审核",
        "client_payments": "📥 客户付款",
        "gift_management": "🎁 礼物管理",
        "owner_dashboard": "🔐 所有者仪表盘",
        "balance": "MonCash商业余额",
        "transfer_funds": "💰 转账到你的账户",
        "amount_transfer": "转账金额 ($)",
        "transfer": "🚀 转到MonCash",
        "no_gifts": "暂无礼物。",
        "payout_summary": "支付摘要",
        "total_gifts_htg": "礼物总额 (HTG)",
        "mark_paid": "全部标记为已支付（模拟）",
        "contact_support": "📬 联系支持 / 大额支付",
        "logout_owner": "登出所有者空间",
        "setup_instructions": "ℹ️ 设置说明（如果上传失败）",
        "storage_error": "存储权限错误：请为'avatars'存储桶设置RLS策略。",
    },
    "hi": {
        "login_title": "लॉग इन",
        "signup_title": "साइन अप",
        "forgot_password": "पासवर्ड भूल गए",
        "email": "ईमेल",
        "password": "पासवर्ड",
        "full_name": "पूरा नाम",
        "remember_me": "मुझे याद रखें",
        "login_button": "🚀 लॉग इन",
        "signup_button": "📝 साइन अप",
        "send_reset_link": "रीसेट लिंक भेजें",
        "phone_method": "फोन (OTP)",
        "email_method": "ईमेल",
        "phone_number": "फोन नंबर (केवल अंक, उदा. 50947385663)",
        "send_otp": "📲 OTP भेजें",
        "enter_otp": "6 अंकों का OTP कोड दर्ज करें",
        "verify_login": "✅ सत्यापित करें और लॉग इन करें",
        "back_resend": "← वापस / OTP पुनः भेजें",
        "feed": "📡 फ़ीड",
        "friends_chat": "👥 मित्र और चैट",
        "satellite_map": "🛰️ उपग्रह मानचित्र",
        "profile": "👤 प्रोफ़ाइल",
        "owner_space": "🕊️ मालिक स्थान",
        "logout": "🚪 लॉग आउट",
        "system_health": "🛡️ सिस्टम स्वास्थ्य",
        "signal": "📡 सिग्नल",
        "latency": "⏱️ विलंबता",
        "quality": "📊 गुणवत्ता",
        "uptime": "⏰ अपटाइम",
        "encrypted": "🔒 स्थिति: एन्क्रिप्टेड",
        "compensation": "💰 मुआवजा",
        "logged_in_as": "👤 के रूप में लॉग इन",
        "go_live": "लाइव जाएं",
        "external_platform": "बाहरी प्लेटफॉर्म (YouTube/Facebook/Twitch)",
        "in_app_camera": "इन-ऐप कैमरा",
        "select_platform": "प्लेटफॉर्म चुनें",
        "live_title": "लाइव शीर्षक",
        "create_live_session": "लाइव सत्र बनाएं",
        "you_are_live": "🔴 आप लाइव हैं!",
        "end_live_session": "लाइव सत्र समाप्त करें",
        "set_stream_url": "📹 स्ट्रीम URL सेट करें",
        "paste_url": "अपना लाइव स्ट्रीम URL चिपकाएं",
        "update_url": "URL अपडेट करें",
        "shareable_link": "साझा करने योग्य लिंक",
        "live_chat_gifts": "लाइव चैट और उपहार",
        "send_gift": "🎁 उपहार भेजें",
        "add_moncash": "उपहार भेजने के लिए अपनी प्रोफ़ाइल में MonCash नंबर जोड़ें।",
        "total_gifts": "कुल प्राप्त उपहार",
        "gifts_sent_to": "उपहार आपके MonCash पर भेजे जाएंगे",
        "write_comment": "टिप्पणी लिखें...",
        "send": "भेजें",
        "back_to_feed": "फ़ीड पर वापस",
        "create_post": "पोस्ट बनाएं",
        "caption_placeholder": "कुछ लिखें... या वीडियो लिंक चिपकाएं",
        "add_media": "चित्र या वीडियो जोड़ें (वैकल्पिक)",
        "visibility": "दृश्यता",
        "public": "सार्वजनिक",
        "private": "निजी",
        "post": "🚀 पोस्ट करें",
        "delete_post": "🗑️ हटाएं",
        "comments": "टिप्पणियाँ",
        "reply": "💬 उत्तर दें",
        "post_reply": "उत्तर पोस्ट करें",
        "your_reply": "आपका उत्तर",
        "clear_error": "त्रुटि साफ़ करें",
        "join_live": "लाइव में शामिल हों",
        "watch_stream": "▶ स्ट्रीम देखें",
        "start_broadcast": "▶ प्रसारण शुरू करें",
        "stop_broadcast": "■ प्रसारण रोकें",
        "you_are_broadcaster": "✅ आप प्रसारक हैं। शुरू करने के लिए नीचे दिए गए नियंत्रण का उपयोग करें।",
        "you_are_viewer": "👀 आप दर्शक हैं। वीडियो देखने के लिए 'स्ट्रीम देखें' पर क्लिक करें।",
        "choose_background": "🎨 पृष्ठभूमि फ़िल्टर",
        "bg_option": "पृष्ठभूमि",
        "upload_background": "या अपनी छवि अपलोड करें",
        "background_set": "पृष्ठभूमि सेट!",
        "ready_to_start": "शुरू करने के लिए तैयार। ऊपर दिए गए बटन पर क्लिक करें।",
        "camera_access": "📷 कैमरा पहुंच का अनुरोध...",
        "camera_granted": "✅ कैमरा पहुंच प्रदान की गई। पीयर सर्वर से कनेक्ट हो रहा है...",
        "broadcasting": "✅ लाइव प्रसारण! आपका पीयर ID",
        "peer_error": "❌ पीयर त्रुटि",
        "error": "❌ त्रुटि",
        "broadcast_ended": "प्रसारण समाप्त",
        "initializing": "प्रारंभ हो रहा है...",
        "connected_requesting": "कनेक्टेड। प्रसारक से स्ट्रीम का अनुरोध...",
        "calling": "कॉलिंग",
        "received_stream": "स्ट्रीम प्राप्त हुई",
        "now_watching": "✅ अब आप लाइव स्ट्रीम देख रहे हैं",
        "call_error": "❌ कॉल त्रुटि",
        "call_ended": "कॉल समाप्त",
        "disconnected": "डिस्कनेक्टेड। कृपया रीफ्रेश करें।",
        "send_message": "भेजें",
        "close_chat": "चैट बंद करें",
        "active_call": "📞 सक्रिय कॉल",
        "room_id": "रूम ID",
        "share_room": "इस ID को उस व्यक्ति के साथ साझा करें जिसे आप कॉल करना चाहते हैं।",
        "start_call": "नई कॉल शुरू करें",
        "end_call": "कॉल समाप्त करें",
        "find_users": "🔍 उपयोगकर्ता खोजें",
        "search_by_name": "नाम से खोजें",
        "add_friend": "➕ मित्र जोड़ें",
        "view_profile": "👤 प्रोफ़ाइल देखें",
        "friend_requests": "📨 प्राप्त मित्र अनुरोध",
        "accept": "✅ स्वीकार करें",
        "reject": "❌ अस्वीकार करें",
        "your_friends": "👥 आपके मित्र",
        "no_friends": "आपके अभी कोई मित्र नहीं है",
        "chat": "💬 चैट",
        "call": "📞 कॉल",
        "profile_btn": "👤 प्रोफ़ाइल",
        "edit_profile": "प्रोफ़ाइल संपादित करें",
        "save_changes": "💾 परिवर्तन सहेजें",
        "change_picture": "📸 चित्र बदलें",
        "bio": "जीवनी",
        "location": "स्थान",
        "moncash_phone": "MonCash फ़ोन नंबर (उपहार प्राप्त करने के लिए)",
        "posts_count": "पोस्ट",
        "connections": "कनेक्शन",
        "verified": "सत्यापित",
        "member_since": "सदस्यता दिनांक",
        "dashboard": "💰 डैशबोर्ड",
        "new_users": "📈 नए उपयोगकर्ता",
        "post_moderation": "🛡️ पोस्ट मॉडरेशन",
        "client_payments": "📥 ग्राहक भुगतान",
        "gift_management": "🎁 उपहार प्रबंधन",
        "owner_dashboard": "🔐 मालिक डैशबोर्ड",
        "balance": "MonCash Business शेष",
        "transfer_funds": "💰 अपने खाते में धनराशि स्थानांतरित करें",
        "amount_transfer": "स्थानांतरित राशि ($)",
        "transfer": "🚀 MonCash में स्थानांतरित करें",
        "no_gifts": "अभी तक कोई उपहार नहीं।",
        "payout_summary": "भुगतान सारांश",
        "total_gifts_htg": "कुल उपहार (HTG)",
        "mark_paid": "सभी को भुगतान के रूप में चिह्नित करें (सिम्युलेटेड)",
        "contact_support": "📬 सहायता / बड़े भुगतान के लिए संपर्क करें",
        "logout_owner": "मालिक स्थान से लॉग आउट करें",
        "setup_instructions": "ℹ️ सेटअप निर्देश (यदि अपलोड विफल होता है)",
        "storage_error": "संग्रहण अनुमति त्रुटि: कृपया 'avatars' बकेट के लिए RLS नीतियां सेट करें।",
    },
}

def t(key):
    """Translate a key using the current language."""
    return LANG.get(st.session_state.language, LANG["en"]).get(key, key)

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

# --- Token refresh function ---
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

# ====== UI STYLING (Light Blue/Red) ======
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
    </style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========
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
        if '/videos/' in url or '/clip/' in url:
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

def embed_video_from_url(url):
    youtube_id = get_youtube_id(url)
    if youtube_id:
        embed_html = f"""
        <iframe width="100%" height="400" src="https://www.youtube.com/embed/{youtube_id}" 
                frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    vimeo_id = get_vimeo_id(url)
    if vimeo_id:
        embed_html = f"""
        <iframe src="https://player.vimeo.com/video/{vimeo_id}" width="100%" height="400" 
                frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>
        <p style="font-size:0.8rem; color:green;">🎥 Vimeo {t('now_watching')}</p>
        """
        st.components.v1.html(embed_html, height=430)
        return True
    dailymotion_id = get_dailymotion_id(url)
    if dailymotion_id:
        embed_html = f"""
        <iframe frameborder="0" width="100%" height="400" 
                src="https://www.dailymotion.com/embed/video/{dailymotion_id}" 
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
        <div class="fb-video" data-href="{fb_url}" data-width="100%" data-allowfullscreen="true"></div>
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
        embed_html = f"""
        <iframe src="https://player.twitch.tv/?video={twitch_url.split('/')[-1]}&parent={parent}" 
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

@st.cache_data(ttl=60, show_spinner=False)
def load_posts_cached(user_id=None, author_id=None):
    if supabase is None:
        return []
    try:
        select_cols = "*, profiles!posts_user_id_fkey(full_name, avatar_url, is_live)"
        if author_id is not None:
            resp = supabase.table("posts").select(select_cols).eq("user_id", author_id).eq("is_public", True).order("created_at", desc=True).execute()
            posts = resp.data
        elif user_id is not None:
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

def load_comments(post_id):
    if supabase is None:
        return []
    try:
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

def load_live_sessions():
    if supabase is None:
        return []
    try:
        try:
            response = supabase.table("live_sessions").select(
                "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url, moncash_phone)"
            ).eq("is_live", True).order("started_at", desc=True).execute()
            return response.data
        except Exception as e:
            if "column 'stream_method' does not exist" in str(e):
                response = supabase.table("live_sessions").select(
                    "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url, moncash_phone)"
                ).eq("is_live", True).order("started_at", desc=True).execute()
                for s in response.data:
                    s['stream_method'] = 'external'
                return response.data
            else:
                raise e
    except Exception as e:
        st.session_state.last_error = f"Error loading live sessions: {e}"
        return []

def get_live_session(session_id):
    if supabase is None:
        return None
    try:
        response = supabase.table("live_sessions").select(
            "*, profiles!live_sessions_user_id_fkey(full_name, avatar_url, moncash_phone)"
        ).eq("id", session_id).single().execute()
        if response.data and 'stream_method' not in response.data:
            response.data['stream_method'] = 'external'
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

def log_in_email(email, password, remember=False):
    if supabase is None:
        st.error("Login unavailable (Supabase not configured).")
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
        if "Invalid login credentials" in error_str:
            st.error("Invalid email or password.")
        elif "Email not confirmed" in error_str:
            st.error("Please confirm your email address before logging in. Check your inbox for a confirmation link.")
        else:
            st.error(f"Login failed: {error_str}")

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

# ========== PAGE RENDERING FUNCTIONS ==========

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
                    channel = stream_url.split("/")[-1]
                    embed_url = f"https://player.twitch.tv/?channel={channel}&parent={st.request.host}"
                    st.components.v1.html(f'<iframe src="{embed_url}" height="400" width="100%" frameborder="0" scrolling="no" allowfullscreen></iframe>', height=410)
                else:
                    st.video(stream_url)
            else:
                st.info("The streamer has not provided a video URL yet.")
        else:
            if is_broadcaster:
                st.markdown(f"### {t('choose_background')} (Your background)")
                with st.expander(t('choose_background'), expanded=False):
                    bg_options = [
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg1.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg2.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg3.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg4.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg5.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg6.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg7.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg8.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg9.jpg",
                        "https://yourproject.supabase.co/storage/v1/object/public/backgrounds/bg10.jpg",
                    ]
                    col_bg = st.columns(5)
                    for i, url in enumerate(bg_options[:10]):
                        with col_bg[i % 5]:
                            if st.button(f"{t('bg_option')} {i+1}", key=f"bg_{session_id}_{i}"):
                                st.session_state[f"bg_{session_id}_{st.session_state.user.id}"] = url
                                st.success(t("background_set"))
                                st.rerun()
                    uploaded_bg = st.file_uploader(t("upload_background"), type=["png", "jpg", "jpeg"], key=f"bg_upload_broadcaster")
                    if uploaded_bg:
                        bytes_data = uploaded_bg.getvalue()
                        b64 = base64.b64encode(bytes_data).decode()
                        mime = uploaded_bg.type
                        data_url = f"data:{mime};base64,{b64}"
                        st.session_state[f"bg_{session_id}_{st.session_state.user.id}"] = data_url
                        st.success(t("background_set"))
                        st.rerun()

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

                st.markdown("### Your Broadcast")
                broadcaster_html = f"""
                <div style="background: #1e2a3a; padding: 30px; border-radius: 20px; text-align: center; color: white;">
                    <div style="font-size: 24px; margin-bottom: 20px;">🎥 {t('you_are_broadcaster')}</div>
                    <div style="background: #000; width: 100%; max-width: 600px; margin: 0 auto; border-radius: 16px; overflow: hidden; border: 3px solid #00a8ff;">
                        <canvas id="broadcasterCanvas" width="640" height="360" style="width: 100%; aspect-ratio: 16/9; background: #111; display: block;"></canvas>
                    </div>
                    <div style="margin-top: 30px;">
                        <button id="startBtn" style="background: #00a8ff; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer; box-shadow: 0 8px 20px rgba(0,168,255,0.4);">{t('start_broadcast')}</button>
                        <button id="stopBtn" style="background: #ff4444; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer; display: none; margin-left: 20px;">{t('stop_broadcast')}</button>
                    </div>
                    <p id="broadcasterStatus" style="margin-top: 20px; font-size: 18px; color: #ccc;">{t('ready_to_start')}</p>
                    <div id="debug" style="margin-top: 10px; font-size: 12px; text-align: left; background: rgba(0,0,0,0.7); padding: 5px; border-radius: 5px; display: none;"></div>
                </div>
                <script src="https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/selfie_segmentation.js"></script>
                <script>
                (function() {{
                    if (!window.broadcasterState) window.broadcasterState = {{}};
                    const state = window.broadcasterState;
                    const sessionId = "{session_id}";
                    const userId = "{st.session_state.user.id}";
                    const startBtn = document.getElementById('startBtn');
                    const stopBtn = document.getElementById('stopBtn');
                    const statusEl = document.getElementById('broadcasterStatus');
                    const canvas = document.getElementById('broadcasterCanvas');
                    const ctx = canvas.getContext('2d');
                    const debugEl = document.getElementById('debug');
                    
                    function log(msg) {{
                        console.log(msg);
                        debugEl.style.display = 'block';
                        debugEl.innerHTML += '<div>' + new Date().toLocaleTimeString() + ': ' + msg + '</div>';
                        const lines = debugEl.innerHTML.split('</div>');
                        if (lines.length > 10) debugEl.innerHTML = lines.slice(-10).join('</div>');
                    }}
                    
                    const bgUrl = "{st.session_state.get(f'bg_{session_id}_{st.session_state.user.id}', '')}";
                    let backgroundImage = null;
                    if (bgUrl) {{
                        log('Loading background from: ' + bgUrl.substring(0, 100));
                        backgroundImage = new Image();
                        backgroundImage.crossOrigin = "Anonymous";
                        backgroundImage.src = bgUrl;
                        backgroundImage.onerror = (e) => {{
                            log('Failed to load background image: ' + e);
                            statusEl.textContent = 'Background image failed to load. Using default color.';
                            backgroundImage = null;
                        }};
                        backgroundImage.onload = () => {{
                            log('Background loaded successfully');
                            canvas.width = 640;
                            canvas.height = 360;
                        }};
                    }} else {{
                        log('No background selected, using blue color');
                    }}
                    
                    let selfieSegmentation = state.selfieSegmentation;
                    if (!selfieSegmentation) {{
                        log('Creating SelfieSegmentation instance');
                        selfieSegmentation = new SelfieSegmentation({{
                            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/${{file}}`
                        }});
                        selfieSegmentation.setOptions({{
                            modelSelection: 1,
                            minDetectionConfidence: 0.5,
                            minTrackingConfidence: 0.5
                        }});
                        selfieSegmentation.onResults(onResults);
                        state.selfieSegmentation = selfieSegmentation;
                        log('SelfieSegmentation initialized');
                    }}
                    
                    let isProcessing = false;
                    function onResults(results) {{
                        if (!results.segmentationMask) {{
                            log('No segmentation mask received');
                            return;
                        }}
                        try {{
                            if (backgroundImage) {{
                                ctx.drawImage(backgroundImage, 0, 0, canvas.width, canvas.height);
                            }} else {{
                                ctx.fillStyle = '#00a8ff';
                                ctx.fillRect(0, 0, canvas.width, canvas.height);
                            }}
                            ctx.save();
                            ctx.globalCompositeOperation = 'destination-out';
                            ctx.drawImage(results.segmentationMask, 0, 0, canvas.width, canvas.height);
                            ctx.globalCompositeOperation = 'source-over';
                            ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
                            ctx.restore();
                            if (!isProcessing) {{
                                log('Frame processed');
                                isProcessing = false;
                            }}
                        }} catch (err) {{
                            log('Error in onResults: ' + err);
                        }}
                    }}
                    
                    if (state.localStream && state.peer && state.call) {{
                        log('Broadcast already running');
                        startBtn.style.display = 'none';
                        stopBtn.style.display = 'inline-block';
                        statusEl.textContent = `{t('broadcasting')}: ${{state.peer.id}}`;
                        if (state.videoElement) {{
                            const processFrame = async () => {{
                                if (!state.videoElement || state.videoElement.readyState < 2) {{
                                    requestAnimationFrame(processFrame);
                                    return;
                                }}
                                isProcessing = true;
                                await selfieSegmentation.send({{image: state.videoElement}});
                                requestAnimationFrame(processFrame);
                            }};
                            processFrame();
                        }}
                        return;
                    }}
                    
                    startBtn.onclick = async () => {{
                        try {{
                            log('Requesting camera access');
                            statusEl.textContent = '{t('camera_access')}';
                            state.localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                            log('Camera stream obtained');
                            
                            state.videoElement = document.createElement('video');
                            state.videoElement.srcObject = state.localStream;
                            state.videoElement.autoplay = true;
                            state.videoElement.width = 640;
                            state.videoElement.height = 360;
                            state.videoElement.onloadeddata = () => {{
                                log('Video element ready');
                                const processFrame = async () => {{
                                    if (!state.videoElement || state.videoElement.readyState < 2) {{
                                        requestAnimationFrame(processFrame);
                                        return;
                                    }}
                                    isProcessing = true;
                                    await selfieSegmentation.send({{image: state.videoElement}});
                                    requestAnimationFrame(processFrame);
                                }};
                                processFrame();
                            }};
                            statusEl.textContent = '{t('camera_granted')}';
                            
                            state.peer = new Peer(`broadcaster-${{sessionId}}`, {{ 
                                host: '0.peerjs.com',
                                port: 443,
                                secure: true,
                                config: {{
                                    'iceServers': [
                                        {{ urls: 'stun:stun.l.google.com:19302' }},
                                        {{ urls: 'stun:stun1.l.google.com:19302' }}
                                    ]
                                }}
                            }});
                            
                            state.peer.on('open', (id) => {{
                                log('Peer opened with ID: ' + id);
                                statusEl.textContent = `{t('broadcasting')}: ${{id}}`;
                                startBtn.style.display = 'none';
                                stopBtn.style.display = 'inline-block';
                            }});
                            
                            state.peer.on('call', (call) => {{
                                if (!state.localStream) return;
                                log('Incoming call from ' + call.peer);
                                call.answer(state.localStream);
                                if (!state.participants) state.participants = [];
                                state.participants.push(call);
                                call.on('stream', (remoteStream) => {{
                                    const participantId = call.peer;
                                    let videoEl = document.getElementById(`participant_${{participantId}}`);
                                    if (!videoEl) {{
                                        videoEl = document.createElement('video');
                                        videoEl.id = `participant_${{participantId}}`;
                                        videoEl.autoplay = true;
                                        videoEl.style.width = '200px';
                                        videoEl.style.margin = '10px';
                                        document.getElementById('participantsContainer').appendChild(videoEl);
                                    }}
                                    videoEl.srcObject = remoteStream;
                                    log('Added participant video: ' + participantId);
                                }});
                                call.on('close', () => {{
                                    const participantId = call.peer;
                                    const videoEl = document.getElementById(`participant_${{participantId}}`);
                                    if (videoEl) videoEl.remove();
                                    log('Removed participant: ' + participantId);
                                }});
                            }});
                            
                            state.peer.on('error', (err) => {{
                                log('Peer error: ' + err);
                                statusEl.textContent = '{t('peer_error')}: ' + err;
                            }});
                        }} catch (err) {{
                            log('Error starting broadcast: ' + err);
                            statusEl.textContent = '{t('error')}: ' + err.message;
                        }}
                    }};
                    
                    stopBtn.onclick = () => {{
                        log('Stopping broadcast');
                        if (state.participants) {{
                            state.participants.forEach(call => call.close());
                        }}
                        if (state.peer) state.peer.destroy();
                        if (state.localStream) state.localStream.getTracks().forEach(track => track.stop());
                        state.localStream = null;
                        state.peer = null;
                        state.participants = [];
                        startBtn.style.display = 'inline-block';
                        stopBtn.style.display = 'none';
                        statusEl.textContent = '{t('broadcast_ended')}';
                        log('Broadcast ended');
                    }};
                }})();
                </script>
                """
                st.markdown("<div id='participantsContainer' style='display: flex; flex-wrap: wrap; justify-content: center; margin-top: 20px;'></div>", unsafe_allow_html=True)
                st.components.v1.html(broadcaster_html, height=750)

            else:
                try:
                    part = supabase.table("live_participants").select("status, background_url").eq("session_id", session_id).eq("user_id", st.session_state.user.id).execute()
                    participant = part.data[0] if part.data else None
                except Exception as e:
                    participant = None
                    st.error(f"Error checking participation: {e}")

                if not participant or participant["status"] == "pending":
                    st.info("You have not joined this live session yet.")
                    if st.button("Request to Join"):
                        try:
                            supabase.table("live_participants").insert({
                                "session_id": session_id,
                                "user_id": st.session_state.user.id,
                                "status": "pending"
                            }).execute()
                            supabase.table("notifications").insert({
                                "user_id": session["user_id"],
                                "type": "live_join_request",
                                "message": f"{st.session_state.profile['full_name']} requests to join your live session: {session['title']}",
                                "read": False
                            }).execute()
                            st.success("Request sent! Please wait for the broadcaster to accept.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to send request: {e}")
                elif participant["status"] == "accepted":
                    st.success("You are an active participant! You can now share your video and audio.")
                    with st.expander("Your Video Controls", expanded=True):
                        col_mic, col_bg = st.columns(2)
                        with col_mic:
                            if st.button("🎤 Mute / Unmute Mic", key=f"toggle_mic_{session_id}"):
                                st.warning("Mute toggling will be implemented client-side via PeerJS.")
                        with col_bg:
                            pass

                    bg_url = participant.get("background_url") or st.session_state.get(f"bg_{session_id}_{st.session_state.user.id}", "")
                    participant_html = f"""
                    <div style="background: #1e2a3a; padding: 30px; border-radius: 20px; text-align: center; color: white;">
                        <div style="font-size: 24px; margin-bottom: 20px;">🎤 You are a participant</div>
                        <div style="background: #000; width: 100%; max-width: 600px; margin: 0 auto; border-radius: 16px; overflow: hidden; border: 3px solid #00a8ff;">
                            <canvas id="participantCanvas" width="640" height="360" style="width: 100%; aspect-ratio: 16/9; background: #111; display: block;"></canvas>
                        </div>
                        <div style="margin-top: 30px;">
                            <button id="connectBtn" style="background: #00a8ff; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer;">{t('start_broadcast')}</button>
                            <button id="disconnectBtn" style="background: #ff4444; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer; display: none; margin-left: 20px;">{t('stop_broadcast')}</button>
                        </div>
                        <p id="participantStatus" style="margin-top: 20px; font-size: 18px; color: #ccc;">{t('ready_to_start')}</p>
                    </div>
                    <script src="https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js"></script>
                    <script src="https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/selfie_segmentation.js"></script>
                    <script>
                    (function() {{
                        if (!window.participantState) window.participantState = {{}};
                        const state = window.participantState;
                        const sessionId = "{session_id}";
                        const userId = "{st.session_state.user.id}";
                        const broadcasterId = `broadcaster-${{sessionId}}`;
                        const canvas = document.getElementById('participantCanvas');
                        const ctx = canvas.getContext('2d');
                        const connectBtn = document.getElementById('connectBtn');
                        const disconnectBtn = document.getElementById('disconnectBtn');
                        const statusEl = document.getElementById('participantStatus');
                        const bgUrl = "{bg_url}";
                        let backgroundImage = null;
                        if (bgUrl) {{
                            backgroundImage = new Image();
                            backgroundImage.crossOrigin = "Anonymous";
                            backgroundImage.src = bgUrl;
                            backgroundImage.onerror = (e) => {{
                                console.error('Participant background load failed:', e);
                                statusEl.textContent = 'Background image failed to load. Using default.';
                                backgroundImage = null;
                            }};
                            backgroundImage.onload = () => {{
                                canvas.width = 640;
                                canvas.height = 360;
                            }};
                        }}
                        let selfieSegmentation = state.selfieSegmentation;
                        if (!selfieSegmentation) {{
                            selfieSegmentation = new SelfieSegmentation({{
                                locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/selfie_segmentation/${{file}}`
                            }});
                            selfieSegmentation.setOptions({{
                                modelSelection: 1,
                                minDetectionConfidence: 0.5,
                                minTrackingConfidence: 0.5
                            }});
                            selfieSegmentation.onResults(onResults);
                            state.selfieSegmentation = selfieSegmentation;
                        }}
                        function onResults(results) {{
                            if (!results.segmentationMask) return;
                            if (backgroundImage) {{
                                ctx.drawImage(backgroundImage, 0, 0, canvas.width, canvas.height);
                            }} else {{
                                ctx.fillStyle = '#00a8ff';
                                ctx.fillRect(0, 0, canvas.width, canvas.height);
                            }}
                            ctx.save();
                            ctx.globalCompositeOperation = 'destination-out';
                            ctx.drawImage(results.segmentationMask, 0, 0, canvas.width, canvas.height);
                            ctx.globalCompositeOperation = 'source-over';
                            ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
                            ctx.restore();
                        }}
                        if (state.localStream && state.peer && state.call) {{
                            connectBtn.style.display = 'none';
                            disconnectBtn.style.display = 'inline-block';
                            statusEl.textContent = 'Connected to broadcaster';
                            if (state.videoElement) {{
                                const processFrame = async () => {{
                                    await selfieSegmentation.send({{image: state.videoElement}});
                                    requestAnimationFrame(processFrame);
                                }};
                                processFrame();
                            }}
                            return;
                        }}
                        connectBtn.onclick = async () => {{
                            try {{
                                statusEl.textContent = '{t('camera_access')}';
                                state.localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                                state.videoElement = document.createElement('video');
                                state.videoElement.srcObject = state.localStream;
                                state.videoElement.autoplay = true;
                                state.videoElement.width = 640;
                                state.videoElement.height = 360;
                                state.videoElement.onloadeddata = () => {{
                                    const processFrame = async () => {{
                                        await selfieSegmentation.send({{image: state.videoElement}});
                                        requestAnimationFrame(processFrame);
                                    }};
                                    processFrame();
                                }};
                                statusEl.textContent = '{t('camera_granted')}';
                                state.peer = new Peer({{ 
                                    host: '0.peerjs.com',
                                    port: 443,
                                    secure: true,
                                    config: {{
                                        'iceServers': [
                                            {{ urls: 'stun:stun.l.google.com:19302' }},
                                            {{ urls: 'stun:stun1.l.google.com:19302' }}
                                        ]
                                    }}
                                }});
                                state.peer.on('open', (id) => {{
                                    statusEl.textContent = 'Calling broadcaster...';
                                    state.call = state.peer.call(broadcasterId, state.localStream);
                                    state.call.on('stream', (remoteStream) => {{
                                        console.log('Broadcaster stream received');
                                    }});
                                    state.call.on('close', () => {{
                                        statusEl.textContent = '{t('call_ended')}';
                                        connectBtn.style.display = 'inline-block';
                                        disconnectBtn.style.display = 'none';
                                    }});
                                    connectBtn.style.display = 'none';
                                    disconnectBtn.style.display = 'inline-block';
                                    statusEl.textContent = 'Connected to broadcaster';
                                }});
                                state.peer.on('error', (err) => {{
                                    statusEl.textContent = '{t('peer_error')}: ' + err;
                                }});
                            }} catch (err) {{
                                statusEl.textContent = '{t('error')}: ' + err.message;
                            }}
                        }};
                        disconnectBtn.onclick = () => {{
                            if (state.call) state.call.close();
                            if (state.peer) state.peer.destroy();
                            if (state.localStream) state.localStream.getTracks().forEach(track => track.stop());
                            state.localStream = null;
                            state.peer = null;
                            state.call = null;
                            connectBtn.style.display = 'inline-block';
                            disconnectBtn.style.display = 'none';
                            statusEl.textContent = '{t('broadcast_ended')}';
                        }};
                    }})();
                    </script>
                    """
                    st.components.v1.html(participant_html, height=750)
                elif participant["status"] == "muted":
                    st.warning("Your microphone has been muted by the broadcaster. You can still watch but cannot speak.")
                    viewer_html = f"""
                    <div style="background: #1e2a3a; padding: 30px; border-radius: 20px; text-align: center; color: white;">
                        <div style="font-size: 24px;">👀 {t('you_are_viewer')} (Muted)</div>
                        <div style="margin-top: 20px;">
                            <button id="watchBtn" style="background: #00a8ff; color: white; border: none; border-radius: 60px; padding: 18px 50px; font-size: 24px; font-weight: bold; cursor: pointer;">{t('watch_stream')}</button>
                        </div>
                        <p id="status" style="margin-top: 20px; font-size: 18px; color: #ccc;">{t('ready_to_start')}</p>
                    </div>
                    <script src="https://unpkg.com/peerjs@1.5.4/dist/peerjs.min.js"></script>
                    <script>
                    (function() {{
                        const sessionId = "{session_id}";
                        const watchBtn = document.getElementById('watchBtn');
                        const statusEl = document.getElementById('status');
                        watchBtn.onclick = () => {{
                            statusEl.textContent = '{t('initializing')}';
                            const peer = new Peer({{
                                host: '0.peerjs.com',
                                port: 443,
                                secure: true
                            }});
                            peer.on('open', (id) => {{
                                const call = peer.call(`broadcaster-${{sessionId}}`, null);
                                call.on('stream', (remoteStream) => {{
                                    const video = document.createElement('video');
                                    video.autoplay = true;
                                    video.style.width = '100%';
                                    video.style.maxHeight = '60vh';
                                    video.style.borderRadius = '12px';
                                    document.body.appendChild(video);
                                    video.srcObject = remoteStream;
                                    statusEl.textContent = '{t('now_watching')}';
                                    watchBtn.style.display = 'none';
                                }});
                                call.on('error', (err) => {{
                                    statusEl.textContent = '{t('call_error')}: ' + err;
                                }});
                            }});
                        }};
                    }})();
                    </script>
                    """
                    st.components.v1.html(viewer_html, height=500)

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
                        if media["type"] == "image":
                            st.image(media["url"], use_column_width=True)
                        elif media["type"] == "video":
                            st.video(media["url"])
                    st.divider()

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
                        if media["type"] == "image":
                            st.image(media["url"], use_column_width=True)
                        elif media["type"] == "video":
                            st.video(media["url"])

                if post['content']:
                    clickable_content = make_clickable(post['content'])
                    st.markdown(f"<div class='post-card'>{clickable_content}</div>", unsafe_allow_html=True)

                if post['content']:
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
            posts = supabase.table("posts").select(
                "*, profiles!posts_user_id_fkey(full_name, avatar_url, id)"
            ).order("created_at", desc=True).execute()
            all_posts = posts.data
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

def main_app():
    with st.sidebar:
        if st.session_state.logged_in:
            st.success("✅ Logged in")
            if st.session_state.refresh_token:
                st.info("🔑 Refresh token present")
            else:
                st.warning("⚠️ No refresh token")
        else:
            st.info("🔓 Not logged in")
            try:
                cookie_token = st.query_params.get("cookie_sb_refresh_token", [None])[0]
                if cookie_token:
                    st.info("🍪 Refresh token found in cookie")
                else:
                    st.info("🍪 No refresh token cookie")
            except:
                pass
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
                                session_id = create_live_session(
                                    title, 
                                    platform, 
                                    method='external' if platform != 'inapp' else 'inapp'
                                )
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

        pages = {
            t("feed"): render_feed,
            t("friends_chat"): render_friends_page,
            t("satellite_map"): render_map,
            t("profile"): render_profile,
            t("owner_space"): owner_space
        }
        choice = st.selectbox(t("feed"), list(pages.keys()))
    pages[choice]()

def login_interface():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center;'><span class='haiti-symbol' style='font-size:6rem;'>🇭🇹</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #0a2a44;'>🏠 Home Sweet Home</h1>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name' style='font-size:1.8rem;'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators' style='font-size:1rem;'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes · Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        lang_options = {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "pt": "Português",
            "ru": "Русский",
            "ar": "العربية",
            "zh": "中文",
            "hi": "हिन्दी"
        }
        selected_lang = st.selectbox("Language / Langue / Idioma", options=list(lang_options.keys()), format_func=lambda x: lang_options[x], index=0)
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()

        auth_method = st.radio(t("login_title"), [t("email_method"), t("phone_method")], horizontal=True)

        if auth_method == t("email_method"):
            tab1, tab2, tab3 = st.tabs([t("login_title"), t("signup_title"), t("forgot_password")])
            with tab1:
                with st.form("login_email"):
                    email = st.text_input(t("email"))
                    password = st.text_input(t("password"), type="password")
                    remember = st.checkbox(t("remember_me"))
                    if st.form_submit_button(t("login_button"), use_container_width=True):
                        if email and password:
                            log_in_email(email, password, remember)
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

if __name__ == "__main__":
    if st.session_state.get("app_authenticated", False) or not APP_PASSWORD:
        st.markdown("""
        <div class="home-title">
            <h1>🏠 Home Sweet Home</h1>
            <p>Your satellite communication & social platform</p>
        </div>
        """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
