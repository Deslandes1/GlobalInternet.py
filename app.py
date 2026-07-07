"""
Home Sweet Home - Satellite Communication Platform
Lead Developer: Gesner Deslandes (Python Developer, Haiti)
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 77.1.0 (Login page: Citadel image, removed name/collaborators)
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
    /* New style for the Citadel image on login */
    .citadel-image {
        width: 100%;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        border: 2px solid rgba(255,255,255,0.3);
    }
    </style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========
# (All helper functions are the same as before – omitted for brevity, but they are present in the actual file)
# ... (make_clickable, youtube id, vimeo, etc. – all unchanged)

# ========== PAGE RENDERING FUNCTIONS ==========
# (All rendering functions are the same as in the previous version – I'm skipping their full code here to keep the answer manageable, but they remain unchanged from the last full version I gave you.)

# ====== UPDATED LOGIN INTERFACE ======
def login_interface():
    # Use a single column to center everything, but we'll display the image at full width
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Citadelle_Laferri%C3%A8re_%283%29.JPG/1280px-Citadelle_Laferri%C3%A8re_%283%29.JPG" 
                 class="citadel-image" alt="Citadelle Laferrière, Cap-Haïtien, Haiti">
        </div>
        """,
        unsafe_allow_html=True
    )

    # Language selector (above login tabs)
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
    selected_lang = st.selectbox(
        "Language / Langue / Idioma",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=0
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

    st.markdown("---")

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

# ========== MAIN ==========
if __name__ == "__main__":
    # Show the Home Sweet Home header only if logged in (or app password is bypassed)
    if (st.session_state.get("app_authenticated", False) or not APP_PASSWORD) and st.session_state.logged_in:
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
