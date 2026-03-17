"""
GLOBALINTERNATIONAL.PY - Complete International Social Media Platform
Lead Developer: Gesner Deslandes
Version: 36.0.0 (Full Facebook-like features)
"""
import streamlit as st

st.set_page_config(page_title="GlobalInternational", page_icon="🌍", layout="wide")

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
from deep_translator import GoogleTranslator
import plotly.express as px
import folium
from streamlit_folium import folium_static
import geocoder

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

# --- Secrets ---
OWNER_CIN = st.secrets.get("OWNER_CIN", "1248795849")
MONCASH_NUM = st.secrets.get("MONCASH_NUM", "+50947385663")
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

# --- Session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "connection_time" not in st.session_state:
    st.session_state.connection_time = time.time()
if "posts" not in st.session_state:
    st.session_state.posts = []
if "owner_space_access" not in st.session_state:
    st.session_state.owner_space_access = False
if "viewing_live" not in st.session_state:
    st.session_state.viewing_live = None
if "live_sessions" not in st.session_state:
    st.session_state.live_sessions = []
if "notifications" not in st.session_state:
    st.session_state.notifications = []
if "unread_count" not in st.session_state:
    st.session_state.unread_count = 0
if "friend_requests" not in st.session_state:
    st.session_state.friend_requests = []
if "friends" not in st.session_state:
    st.session_state.friends = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None
if "groups" not in st.session_state:
    st.session_state.groups = []
if "current_group" not in st.session_state:
    st.session_state.current_group = None
if "language" not in st.session_state:
    st.session_state.language = "en"
if "saved_posts" not in st.session_state:
    st.session_state.saved_posts = []
if "trending_posts" not in st.session_state:
    st.session_state.trending_posts = []
if "suggested_users" not in st.session_state:
    st.session_state.suggested_users = []
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None

# --- Language dictionary ---
translations = {
    "en": {
        "feed": "Feed",
        "friends": "Friends",
        "map": "Satellite Map",
        "profile": "Profile",
        "owner": "Owner Space",
        "create_post": "Create a post",
        "whats_on_mind": "What's on your mind?",
        "post": "Post",
        "public": "Public",
        "private": "Private",
        "live_now": "🔴 Live Now",
        "join_live": "Join Live",
        "comments": "Comments",
        "write_comment": "Write a comment...",
        "send": "Send",
        "reply": "Reply",
        "like": "Like",
        "share": "Share",
        "save": "Save",
        "report": "Report",
        "block": "Block",
        "follow": "Follow",
        "unfollow": "Unfollow",
        "friend_request": "Friend Request",
        "accept": "Accept",
        "reject": "Reject",
        "message": "Message",
        "search_users": "Search users...",
        "notifications": "Notifications",
        "no_notifications": "No notifications",
        "logout": "Logout",
        "login": "Login",
        "signup": "Sign Up",
        "email": "Email",
        "password": "Password",
        "full_name": "Full Name",
        "phone": "Phone",
        "remember_me": "Remember me",
        "forgot_password": "Forgot Password",
        "send_otp": "Send OTP",
        "verify_otp": "Verify OTP",
        "language": "Language",
    },
    "fr": {
        "feed": "Fil d'actualité",
        "friends": "Amis",
        "map": "Carte satellite",
        "profile": "Profil",
        "owner": "Espace propriétaire",
        "create_post": "Créer une publication",
        "whats_on_mind": "Quoi de neuf ?",
        "post": "Publier",
        "public": "Public",
        "private": "Privé",
        "live_now": "🔴 En direct",
        "join_live": "Rejoindre",
        "comments": "Commentaires",
        "write_comment": "Écrire un commentaire...",
        "send": "Envoyer",
        "reply": "Répondre",
        "like": "J'aime",
        "share": "Partager",
        "save": "Enregistrer",
        "report": "Signaler",
        "block": "Bloquer",
        "follow": "Suivre",
        "unfollow": "Ne plus suivre",
        "friend_request": "Demande d'ami",
        "accept": "Accepter",
        "reject": "Refuser",
        "message": "Message",
        "search_users": "Rechercher des utilisateurs...",
        "notifications": "Notifications",
        "no_notifications": "Aucune notification",
        "logout": "Déconnexion",
        "login": "Connexion",
        "signup": "S'inscrire",
        "email": "E-mail",
        "password": "Mot de passe",
        "full_name": "Nom complet",
        "phone": "Téléphone",
        "remember_me": "Se souvenir de moi",
        "forgot_password": "Mot de passe oublié",
        "send_otp": "Envoyer OTP",
        "verify_otp": "Vérifier OTP",
        "language": "Langue",
    },
    "es": {
        "feed": "Feed",
        "friends": "Amigos",
        "map": "Mapa satelital",
        "profile": "Perfil",
        "owner": "Espacio del propietario",
        "create_post": "Crear publicación",
        "whats_on_mind": "¿Qué estás pensando?",
        "post": "Publicar",
        "public": "Público",
        "private": "Privado",
        "live_now": "🔴 En vivo",
        "join_live": "Unirse",
        "comments": "Comentarios",
        "write_comment": "Escribe un comentario...",
        "send": "Enviar",
        "reply": "Responder",
        "like": "Me gusta",
        "share": "Compartir",
        "save": "Guardar",
        "report": "Reportar",
        "block": "Bloquear",
        "follow": "Seguir",
        "unfollow": "Dejar de seguir",
        "friend_request": "Solicitud de amistad",
        "accept": "Aceptar",
        "reject": "Rechazar",
        "message": "Mensaje",
        "search_users": "Buscar usuarios...",
        "notifications": "Notificaciones",
        "no_notifications": "Sin notificaciones",
        "logout": "Cerrar sesión",
        "login": "Iniciar sesión",
        "signup": "Registrarse",
        "email": "Correo electrónico",
        "password": "Contraseña",
        "full_name": "Nombre completo",
        "phone": "Teléfono",
        "remember_me": "Recordarme",
        "forgot_password": "Olvidé mi contraseña",
        "send_otp": "Enviar OTP",
        "verify_otp": "Verificar OTP",
        "language": "Idioma",
    },
    "ht": {
        "feed": "Fil",
        "friends": "Zanmi",
        "map": "Kat satelit",
        "profile": "Pwofil",
        "owner": "Espace mèt",
        "create_post": "Kreye yon pòs",
        "whats_on_mind": "Kisa kap pase nan tèt ou?",
        "post": "Pibliye",
        "public": "Piblik",
        "private": "Prive",
        "live_now": "🔴 An dirèk",
        "join_live": "Rantre",
        "comments": "Kòmantè",
        "write_comment": "Ekri yon kòmantè...",
        "send": "Voye",
        "reply": "Reponn",
        "like": "Renmen",
        "share": "Pataje",
        "save": "Sere",
        "report": "Rapòte",
        "block": "Bloke",
        "follow": "Swiv",
        "unfollow": "Sispann swiv",
        "friend_request": "Demand zanmi",
        "accept": "Aksepte",
        "reject": "Refize",
        "message": "Mesaj",
        "search_users": "Chèche itilizatè...",
        "notifications": "Notifikasyon",
        "no_notifications": "Pa gen notifikasyon",
        "logout": "Dekonekte",
        "login": "Konekte",
        "signup": "Enskri",
        "email": "Imèl",
        "password": "Modpas",
        "full_name": "Non konplè",
        "phone": "Telefòn",
        "remember_me": "Sonje m",
        "forgot_password": "Bliye modpas",
        "send_otp": "Voye OTP",
        "verify_otp": "Verifye OTP",
        "language": "Lang",
    }
}

def t(key):
    """Translate a key to the current language."""
    return translations.get(st.session_state.language, translations["en"]).get(key, key)

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
                "is_live": False,
                "language": "en"
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
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
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
        st.session_state.last_error = f"Media upload failed: {e}"
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
    if supabase is None:
        return []
    try:
        # Get posts from followed users + public posts
        user_id = st.session_state.user.id if st.session_state.user else None
        if user_id:
            # Get followed users
            followed = supabase.table("follows").select("following_id").eq("follower_id", user_id).execute()
            followed_ids = [f["following_id"] for f in followed.data] if followed.data else []
            followed_ids.append(user_id)  # include own posts
            
            # Build query
            query = supabase.table("posts").select("*, profiles(full_name, avatar_url, is_live)")
            if followed_ids:
                # Posts from followed users or public posts
                query = query.or_(f"user_id.in.{','.join(followed_ids)},is_public.eq.True")
            else:
                query = query.eq("is_public", True)
            posts = query.order("created_at", desc=True).execute()
        else:
            posts = supabase.table("posts").select("*, profiles(full_name, avatar_url, is_live)").eq("is_public", True).order("created_at", desc=True).execute()
        
        # Fetch reactions and comments counts
        for post in posts.data:
            post["media_urls"] = post.get("media_urls", [])
            post["reactions"] = {}
            if user_id:
                # Check if user liked/saved
                post["user_liked"] = False  # placeholder
                # Check if saved
                saved = supabase.table("saved_posts").select("post_id").eq("user_id", user_id).eq("post_id", post["id"]).execute()
                post["saved"] = bool(saved.data)
            # Count comments
            comments = supabase.table("comments").select("id", count="exact").eq("post_id", post["id"]).execute()
            post["comment_count"] = comments.count if hasattr(comments, 'count') else 0
        return posts.data
    except Exception as e:
        st.session_state.last_error = f"Error loading posts: {e}"
        return []

def create_post(user_id, content, media_files, is_public):
    if supabase is None:
        st.session_state.last_error = "Supabase not configured."
        return False
    try:
        # Extract hashtags
        hashtags = [word for word in content.split() if word.startswith("#")]
        media_urls = []
        if media_files:
            for f in media_files:
                media_info = upload_post_media(user_id, f)
                if media_info:
                    media_urls.append(media_info)
        post = {
            "user_id": user_id,
            "content": content,
            "is_public": is_public,
            "likes_count": 0,
            "shares_count": 0,
            "hashtags": hashtags,
            "media_urls": media_urls,
            "created_at": datetime.now().isoformat()
        }
        result = supabase.table("posts").insert(post).execute()
        if result.data:
            st.session_state.posts = load_posts()
            st.success("✅ Post published!")
            return True
        else:
            st.session_state.last_error = "Post insertion failed."
            return False
    except Exception as e:
        st.session_state.last_error = f"Error creating post: {e}"
        return False

def toggle_reaction(post_id, user_id, emoji):
    if supabase is None:
        return False
    try:
        # Check if reaction exists
        check = supabase.table("reactions").select("id").eq("post_id", post_id).eq("user_id", user_id).eq("emoji", emoji).execute()
        if check.data:
            supabase.table("reactions").delete().eq("post_id", post_id).eq("user_id", user_id).eq("emoji", emoji).execute()
        else:
            supabase.table("reactions").insert({"post_id": post_id, "user_id": user_id, "emoji": emoji}).execute()
            # Create notification for post owner
            post = supabase.table("posts").select("user_id").eq("id", post_id).single().execute()
            if post.data and post.data["user_id"] != user_id:
                sender_name = st.session_state.profile["full_name"]
                supabase.table("notifications").insert({
                    "user_id": post.data["user_id"],
                    "type": "reaction",
                    "related_id": post_id,
                    "message": f"{sender_name} reacted with {emoji} to your post",
                    "read": False
                }).execute()
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error toggling reaction: {e}"
        return False

def add_comment(post_id, user_id, content, parent_id=None):
    if supabase is None:
        return False
    try:
        comment = {
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "parent_id": parent_id,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("comments").insert(comment).execute()
        # Notify post owner
        post = supabase.table("posts").select("user_id").eq("id", post_id).single().execute()
        if post.data and post.data["user_id"] != user_id:
            sender_name = st.session_state.profile["full_name"]
            supabase.table("notifications").insert({
                "user_id": post.data["user_id"],
                "type": "comment",
                "related_id": post_id,
                "message": f"{sender_name} commented on your post",
                "read": False
            }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error adding comment: {e}"
        return False

def load_comments(post_id):
    if supabase is None:
        return []
    try:
        comments = supabase.table("comments").select("*, profiles(full_name, avatar_url)").eq("post_id", post_id).order("created_at").execute()
        return comments.data
    except Exception as e:
        st.session_state.last_error = f"Error loading comments: {e}"
        return []

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
        supabase.table("posts").insert(post).execute()
        # Notify original poster
        original = supabase.table("posts").select("user_id").eq("id", original_post_id).single().execute()
        if original.data and original.data["user_id"] != user_id:
            sender_name = st.session_state.profile["full_name"]
            supabase.table("notifications").insert({
                "user_id": original.data["user_id"],
                "type": "share",
                "related_id": original_post_id,
                "message": f"{sender_name} shared your post",
                "read": False
            }).execute()
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error sharing post: {e}"
        return False

def save_post(user_id, post_id):
    if supabase is None:
        return False
    try:
        supabase.table("saved_posts").insert({"user_id": user_id, "post_id": post_id}).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error saving post: {e}"
        return False

def unsave_post(user_id, post_id):
    if supabase is None:
        return False
    try:
        supabase.table("saved_posts").delete().eq("user_id", user_id).eq("post_id", post_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error unsaving post: {e}"
        return False

def follow_user(follower_id, following_id):
    if supabase is None:
        return False
    try:
        supabase.table("follows").insert({"follower_id": follower_id, "following_id": following_id}).execute()
        # Notify
        follower_name = st.session_state.profile["full_name"]
        supabase.table("notifications").insert({
            "user_id": following_id,
            "type": "follow",
            "message": f"{follower_name} started following you",
            "read": False
        }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error following user: {e}"
        return False

def unfollow_user(follower_id, following_id):
    if supabase is None:
        return False
    try:
        supabase.table("follows").delete().eq("follower_id", follower_id).eq("following_id", following_id).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error unfollowing user: {e}"
        return False

def is_following(follower_id, following_id):
    if supabase is None:
        return False
    try:
        result = supabase.table("follows").select("follower_id").eq("follower_id", follower_id).eq("following_id", following_id).execute()
        return bool(result.data)
    except:
        return False

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
        # Check if already exists
        existing = supabase.table("friend_requests").select("id").or_(
            f"and(sender_id.eq.{sender_id},receiver_id.eq.{receiver_id})",
            f"and(sender_id.eq.{receiver_id},receiver_id.eq.{sender_id})"
        ).execute()
        if existing.data:
            return False, "Friend request already exists"
        data = {"sender_id": sender_id, "receiver_id": receiver_id, "status": "pending"}
        supabase.table("friend_requests").insert(data).execute()
        # Notify
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
            # Notify sender
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

def load_friend_data(user_id):
    if supabase is None:
        return [], [], []
    try:
        # Pending requests received
        pending = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "pending").execute()
        # Friends
        sent = supabase.table("friend_requests").select("*, receiver:receiver_id(full_name, avatar_url)").eq("sender_id", user_id).eq("status", "accepted").execute()
        received = supabase.table("friend_requests").select("*, sender:sender_id(full_name, avatar_url)").eq("receiver_id", user_id).eq("status", "accepted").execute()
        friends = []
        for r in sent.data:
            friends.append({"id": r["receiver"]["id"], "full_name": r["receiver"]["full_name"], "avatar_url": r["receiver"].get("avatar_url")})
        for r in received.data:
            friends.append({"id": r["sender"]["id"], "full_name": r["sender"]["full_name"], "avatar_url": r["sender"].get("avatar_url")})
        return pending.data, friends, []
    except Exception as e:
        st.session_state.last_error = f"Error loading friend data: {e}"
        return [], [], []

def search_users(query, current_user_id):
    if supabase is None:
        return []
    try:
        result = supabase.table("profiles").select("id, full_name, avatar_url").neq("id", current_user_id).ilike("full_name", f"%{query}%").limit(20).execute()
        return result.data
    except Exception as e:
        st.session_state.last_error = f"Search failed: {e}"
        return []

def send_message(sender_id, receiver_id, content):
    if supabase is None:
        return False
    try:
        supabase.table("messages").insert({
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "content": content,
            "read": False,
            "created_at": datetime.now().isoformat()
        }).execute()
        # Notify
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
        msgs = supabase.table("messages").select("*").or_(
            f"and(sender_id.eq.{user_id},receiver_id.eq.{other_id})",
            f"and(sender_id.eq.{other_id},receiver_id.eq.{user_id})"
        ).order("created_at").execute()
        # Mark as read
        supabase.table("messages").update({"read": True}).eq("sender_id", other_id).eq("receiver_id", user_id).execute()
        return msgs.data
    except Exception as e:
        st.session_state.last_error = f"Error loading messages: {e}"
        return []

def create_group(name, description, created_by, is_public=True):
    if supabase is None:
        return None
    try:
        group = supabase.table("groups").insert({
            "name": name,
            "description": description,
            "created_by": created_by,
            "is_public": is_public
        }).execute()
        if group.data:
            # Add creator as admin
            supabase.table("group_members").insert({
                "group_id": group.data[0]["id"],
                "user_id": created_by,
                "role": "admin"
            }).execute()
            return group.data[0]["id"]
        return None
    except Exception as e:
        st.session_state.last_error = f"Error creating group: {e}"
        return None

def join_group(group_id, user_id):
    if supabase is None:
        return False
    try:
        supabase.table("group_members").insert({
            "group_id": group_id,
            "user_id": user_id,
            "role": "member"
        }).execute()
        return True
    except Exception as e:
        st.session_state.last_error = f"Error joining group: {e}"
        return False

def load_groups(user_id):
    if supabase is None:
        return []
    try:
        # Public groups + groups user is member of
        public = supabase.table("groups").select("*").eq("is_public", True).execute()
        member = supabase.table("group_members").select("group_id").eq("user_id", user_id).execute()
        member_ids = [m["group_id"] for m in member.data] if member.data else []
        private = supabase.table("groups").select("*").in_("id", member_ids).execute() if member_ids else []
        # Combine and deduplicate
        groups = {g["id"]: g for g in public.data + private.data}.values()
        return list(groups)
    except Exception as e:
        st.session_state.last_error = f"Error loading groups: {e}"
        return []

def translate_text(text, dest_lang):
    try:
        translator = GoogleTranslator(source='auto', target=dest_lang)
        return translator.translate(text)
    except:
        return text

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

# --- Authentication functions (simplified) ---
def sign_up_email(email, password, full_name):
    if supabase is None:
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
        return
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if user.user:
            st.session_state.logged_in = True
            st.session_state.user = user.user
            profile = get_or_create_profile(user.user.id, email)
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.session_state.language = profile.get("language", "en")
            st.session_state.posts = load_posts()
            pending, friends, _ = load_friend_data(user.user.id)
            st.session_state.friend_requests = pending
            st.session_state.friends = friends
            st.session_state.notifications = load_notifications(user.user.id)
            st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n["read"])
            if remember and user.session:
                set_cookie("sb_refresh_token", user.session.refresh_token, 30)
            st.rerun()
    except Exception as e:
        st.session_state.last_error = f"Login failed: {e}"

def logout():
    set_cookie("sb_refresh_token", "", -1)
    if supabase:
        supabase.auth.sign_out()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Cookie helpers (simplified) ---
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

# --- Pages ---
def render_feed():
    st.header("🌐 " + t("feed"))
    if st.session_state.last_error:
        st.error(st.session_state.last_error)
        if st.button("Clear error"):
            st.session_state.last_error = None
            st.rerun()

    # Post composer
    with st.expander(t("create_post"), expanded=True):
        with st.form("new_post"):
            content = st.text_area(t("whats_on_mind"), height=100)
            media_files = st.file_uploader("Add images/videos", type=["png","jpg","jpeg","gif","mp4","mov","avi"], accept_multiple_files=True)
            visibility = st.radio("Visibility", [t("public"), t("private")], horizontal=True, index=0)
            is_public = (visibility == t("public"))
            if st.form_submit_button(t("post")):
                if content or media_files:
                    create_post(st.session_state.user.id, content, media_files, is_public)
                    st.rerun()
                else:
                    st.warning("Please add content or media.")

    # Live sessions
    if st.session_state.live_sessions:
        st.markdown("### " + t("live_now"))
        for live in st.session_state.live_sessions:
            cols = st.columns([1,4,1])
            with cols[0]:
                if live["profiles"]["avatar_url"]:
                    st.image(live["profiles"]["avatar_url"], width=40)
                else:
                    st.markdown("👤")
            with cols[1]:
                st.markdown(f"**{live['profiles']['full_name']}**: {live['title']}")
            with cols[2]:
                if st.button(t("join_live"), key=f"join_{live['id']}"):
                    st.session_state.viewing_live = live["id"]
                    st.rerun()
            st.divider()

    # Posts
    for post in st.session_state.posts:
        with st.container():
            cols = st.columns([1,5,2,1])
            with cols[0]:
                if post["profiles"]["avatar_url"]:
                    st.image(post["profiles"]["avatar_url"], width=40)
                else:
                    st.markdown("👤")
            with cols[1]:
                st.markdown(f"**{post['profiles']['full_name']}**")
                if not post["is_public"]:
                    st.markdown(f"<span class='private-badge'>{t('private')}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.caption(post["created_at"][:16])
            with cols[3]:
                if st.session_state.user and post["user_id"] == st.session_state.user.id:
                    if st.button("🗑️", key=f"del_{post['id']}"):
                        st.session_state.delete_confirm = (post["id"], post["content"][:30])
                        st.rerun()

            if post["content"]:
                # Translate if needed
                display_content = post["content"]
                if st.session_state.language != "en":
                    display_content = translate_text(post["content"], st.session_state.language)
                st.markdown(f"<div class='post-card'>{display_content}</div>", unsafe_allow_html=True)

            # Media
            for media in post.get("media_urls", []):
                if media["type"] == "image":
                    st.image(media["url"], use_column_width=True)
                elif media["type"] == "video":
                    st.video(media["url"])

            # Actions
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            with col1:
                if st.button(f"👍 {post.get('likes_count',0)}", key=f"like_{post['id']}"):
                    toggle_reaction(post["id"], st.session_state.user.id, "👍")
                    st.rerun()
            with col2:
                if st.button(f"💬 {post.get('comment_count',0)}", key=f"comment_{post['id']}"):
                    st.session_state[f"show_comments_{post['id']}"] = not st.session_state.get(f"show_comments_{post['id']}", False)
                    st.rerun()
            with col3:
                if st.button(t("share"), key=f"share_{post['id']}"):
                    share_post(post["id"], st.session_state.user.id)
                    st.rerun()
            with col4:
                if post.get("saved", False):
                    if st.button("📌 " + t("saved"), key=f"unsave_{post['id']}"):
                        unsave_post(st.session_state.user.id, post["id"])
                        st.rerun()
                else:
                    if st.button(t("save"), key=f"save_{post['id']}"):
                        save_post(st.session_state.user.id, post["id"])
                        st.rerun()
            with col5:
                if post["user_id"] != st.session_state.user.id:
                    if is_following(st.session_state.user.id, post["user_id"]):
                        if st.button(t("unfollow"), key=f"unfollow_{post['user_id']}"):
                            unfollow_user(st.session_state.user.id, post["user_id"])
                            st.rerun()
                    else:
                        if st.button(t("follow"), key=f"follow_{post['user_id']}"):
                            follow_user(st.session_state.user.id, post["user_id"])
                            st.rerun()
            with col6:
                if post["user_id"] != st.session_state.user.id:
                    if st.button("🚩", key=f"report_{post['id']}"):
                        st.session_state[f"report_{post['id']}"] = True
                        st.rerun()

            # Comments section
            if st.session_state.get(f"show_comments_{post['id']}", False):
                st.markdown("#### " + t("comments"))
                with st.form(f"new_comment_{post['id']}", clear_on_submit=True):
                    comment = st.text_input(t("write_comment"))
                    if st.form_submit_button(t("send")):
                        if comment:
                            add_comment(post["id"], st.session_state.user.id, comment)
                            st.rerun()
                comments = load_comments(post["id"])
                for c in comments:
                    st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}  \n*{c['created_at'][:16]}*")
                st.divider()

    # Delete confirmation
    if st.session_state.delete_confirm:
        post_id, _ = st.session_state.delete_confirm
        st.warning("Are you sure you want to delete this post?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete"):
                delete_post(post_id)
                st.session_state.posts = load_posts()
                st.session_state.delete_confirm = None
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.delete_confirm = None
                st.rerun()

def render_friends_page():
    st.header("👥 " + t("friends"))
    
    # Notifications
    with st.expander(f"🔔 {t('notifications')} ({st.session_state.unread_count} unread)", expanded=True):
        if not st.session_state.notifications:
            st.info(t("no_notifications"))
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

    # Pending friend requests
    st.subheader("📨 " + t("friend_request") + " " + t("received"))
    if not st.session_state.friend_requests:
        st.info("No pending requests")
    else:
        for req in st.session_state.friend_requests:
            cols = st.columns([2,1,1])
            with cols[0]:
                st.markdown(f"**{req['sender']['full_name']}**")
            with cols[1]:
                if st.button(t("accept"), key=f"accept_{req['id']}"):
                    success, msg = respond_friend_request(req['id'], True)
                    if success:
                        pending, friends, _ = load_friend_data(st.session_state.user.id)
                        st.session_state.friend_requests = pending
                        st.session_state.friends = friends
                        st.rerun()
                    else:
                        st.error(msg)
            with cols[2]:
                if st.button(t("reject"), key=f"reject_{req['id']}"):
                    success, msg = respond_friend_request(req['id'], False)
                    if success:
                        pending, friends, _ = load_friend_data(st.session_state.user.id)
                        st.session_state.friend_requests = pending
                        st.rerun()
                    else:
                        st.error(msg)
            st.divider()

    # Search users
    st.subheader("🔍 " + t("search_users"))
    query = st.text_input("")
    if query:
        results = search_users(query, st.session_state.user.id)
        if results:
            for user in results:
                cols = st.columns([3,1,1])
                with cols[0]:
                    st.markdown(f"**{user['full_name']}**")
                with cols[1]:
                    if st.button(t("friend_request"), key=f"req_{user['id']}"):
                        success, msg = send_friend_request(st.session_state.user.id, user['id'])
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                with cols[2]:
                    if st.button(t("message"), key=f"msg_{user['id']}"):
                        st.session_state.selected_chat = user['id']
                        st.rerun()
                st.divider()

    # Friends list
    st.subheader("👥 " + t("friends"))
    if not st.session_state.friends:
        st.info("You have no friends yet")
    else:
        for friend in st.session_state.friends:
            cols = st.columns([1,4,1])
            with cols[0]:
                if friend.get('avatar_url'):
                    st.image(friend['avatar_url'], width=30)
                else:
                    st.markdown("👤")
            with cols[1]:
                st.markdown(f"**{friend['full_name']}**")
            with cols[2]:
                if st.button(t("message"), key=f"msg_f_{friend['id']}"):
                    st.session_state.selected_chat = friend['id']
                    st.rerun()
            st.divider()

    # Messaging
    if st.session_state.selected_chat:
        st.subheader("💬 " + t("message"))
        other_id = st.session_state.selected_chat
        # Get other user's name
        other = supabase.table("profiles").select("full_name").eq("id", other_id).single().execute()
        other_name = other.data["full_name"] if other.data else "User"
        st.write(f"Chat with **{other_name}**")
        messages = load_messages(st.session_state.user.id, other_id)
        for msg in messages:
            if msg["sender_id"] == st.session_state.user.id:
                st.markdown(f"<div style='text-align:right; background:#e0f7fa; padding:5px; border-radius:10px; margin:5px;'><b>You:</b> {msg['content']}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; background:#f1f8e9; padding:5px; border-radius:10px; margin:5px;'><b>{other_name}:</b> {msg['content']}<br><small>{msg['created_at'][:16]}</small></div>", unsafe_allow_html=True)
        with st.form("send_message"):
            msg_content = st.text_input("Type a message...")
            if st.form_submit_button(t("send")):
                if msg_content:
                    send_message(st.session_state.user.id, other_id, msg_content)
                    st.rerun()
        if st.button("Close chat"):
            st.session_state.selected_chat = None
            st.rerun()

def render_map():
    st.header("🛰️ " + t("map"))
    # Sample satellite positions
    sats = {
        "Starlink-1": {"lat": 32.77, "lon": -96.79, "status": "Active"},
        "Starlink-2": {"lat": 35.68, "lon": 139.69, "status": "Active"},
        "Starlink-3": {"lat": 51.50, "lon": -0.12, "status": "Active"},
        "Starlink-4": {"lat": 18.53, "lon": -72.33, "status": "Priority"}
    }
    # Create map
    m = folium.Map(location=[20, 0], zoom_start=2)
    for name, data in sats.items():
        folium.Marker(
            [data["lat"], data["lon"]],
            popup=f"{name}: {data['status']}",
            icon=folium.Icon(color="red" if data["status"]=="Priority" else "blue")
        ).add_to(m)
    folium_static(m)

def render_profile():
    st.header("👤 " + t("profile"))
    if st.session_state.profile is None:
        return
    profile = st.session_state.profile

    col1, col2 = st.columns([1,2])
    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=200)
        else:
            st.image("https://via.placeholder.com/200", width=200)
        uploaded = st.file_uploader("📸 Change picture", type=["png","jpg","jpeg"], label_visibility="collapsed")
        if uploaded:
            url = upload_avatar(st.session_state.user.id, uploaded)
            if url:
                profile["avatar_url"] = url
                update_profile(profile)
                st.rerun()

    with col2:
        with st.form("edit_profile"):
            full_name = st.text_input(t("full_name"), value=profile.get("full_name", ""))
            bio = st.text_area("Bio", value=profile.get("bio", ""), height=100)
            location = st.text_input("Location", value=profile.get("location", ""))
            lang = st.selectbox(t("language"), ["en", "fr", "es", "ht"], index=["en","fr","es","ht"].index(profile.get("language","en")))
            if st.form_submit_button("💾 Save"):
                profile.update({"full_name": full_name, "bio": bio, "location": location, "language": lang})
                if update_profile(profile):
                    st.session_state.language = lang
                    st.success("Profile updated!")
                    st.rerun()

    st.divider()
    cola, colb, colc, cold = st.columns(4)
    with cola:
        st.metric("Posts", len(st.session_state.posts))
    with colb:
        st.metric("Friends", len(st.session_state.friends))
    with colc:
        st.metric("Followers", 0)  # placeholder
    with cold:
        st.metric("Following", 0)  # placeholder

def owner_space():
    st.header("🕊️ " + t("owner"))
    if not st.session_state.owner_space_access:
        with st.form("owner_login"):
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Access"):
                if pwd == OWNSPACE_PASSWORD:
                    st.session_state.owner_space_access = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return

    st.subheader("🔐 Owner Dashboard")
    st.write(f"CIN: {OWNER_CIN}")
    st.write(f"MonCash: {MONCASH_NUM}")
    if st.button("Logout from Owner Space"):
        st.session_state.owner_space_access = False
        st.rerun()

def main_app():
    with st.sidebar:
        st.markdown("<div class='haiti-symbol'>🌍</div>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name'>GlobalInternational</div>", unsafe_allow_html=True)
        st.divider()

        if st.session_state.unread_count > 0:
            st.sidebar.markdown(f"🔔 **{t('notifications')}** <span class='notification-badge'>{st.session_state.unread_count}</span>", unsafe_allow_html=True)

        # Language selector
        lang = st.selectbox(t("language"), ["en", "fr", "es", "ht"], index=["en","fr","es","ht"].index(st.session_state.language))
        if lang != st.session_state.language:
            st.session_state.language = lang
            st.rerun()

        lat, sig, qual = get_network_status()
        st.markdown("### 🛡️ System Health")
        st.markdown(f"""
        <div class='health-text'>
        📡 Signal: {sig}<br>
        ⏱️ Latency: {lat}ms<br>
        📊 Quality: {qual}%<br>
        ⏰ Uptime: {get_uptime()}
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        if st.session_state.profile:
            st.markdown(f"👤 **{st.session_state.profile.get('full_name', 'User')}**")
        if st.button("🚪 " + t("logout")):
            logout()
        st.divider()

        pages = {
            t("feed"): render_feed,
            t("friends"): render_friends_page,
            t("map"): render_map,
            t("profile"): render_profile,
            t("owner"): owner_space
        }
        choice = st.selectbox(t("menu"), list(pages.keys()))
    pages[choice]()

def login_interface():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>GlobalInternational</h1>", unsafe_allow_html=True)
        st.markdown("---")

        auth_method = st.radio("Method", ["Email"], horizontal=True)
        if auth_method == "Email":
            tab1, tab2 = st.tabs([t("login"), t("signup")])
            with tab1:
                with st.form("login"):
                    email = st.text_input(t("email"))
                    password = st.text_input(t("password"), type="password")
                    remember = st.checkbox(t("remember_me"))
                    if st.form_submit_button(t("login")):
                        if email and password:
                            log_in_email(email, password, remember)
                        else:
                            st.warning("Enter email and password")
            with tab2:
                with st.form("signup"):
                    full_name = st.text_input(t("full_name"))
                    email = st.text_input(t("email"))
                    password = st.text_input(t("password"), type="password")
                    if st.form_submit_button(t("signup")):
                        if full_name and email and password:
                            sign_up_email(email, password, full_name)
                        else:
                            st.warning("Fill all fields")

if __name__ == "__main__":
    # Inject cookie reader
    if not st.session_state.logged_in:
        inject_cookie_reader()
        refresh_token = get_cookie("sb_refresh_token")
        if refresh_token and supabase:
            try:
                user = supabase.auth.get_user(refresh_token)
                if user.user:
                    st.session_state.logged_in = True
                    st.session_state.user = user.user
                    profile = get_or_create_profile(user.user.id, user.user.email or user.user.phone)
                    st.session_state.profile = profile
                    st.session_state.connection_time = time.time()
                    st.session_state.language = profile.get("language", "en")
                    st.session_state.posts = load_posts()
                    pending, friends, _ = load_friend_data(user.user.id)
                    st.session_state.friend_requests = pending
                    st.session_state.friends = friends
                    st.session_state.notifications = load_notifications(user.user.id)
                    st.session_state.unread_count = sum(1 for n in st.session_state.notifications if not n["read"])
            except Exception as e:
                st.session_state.last_error = str(e)

    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
