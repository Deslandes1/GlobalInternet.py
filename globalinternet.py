# ====== FULL app.py (Lakay se Lakay - Mobile Optimized + Strong Session Persistence) ======
# Lakay se Lakay - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes
# Version: 92.2.0 (Mobile + Strong Persistence Fix)

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

# ====== PAGE CONFIG - MOBILE OPTIMIZED ======
st.set_page_config(
    page_title="Lakay se Lakay",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",  # Better on mobile
    menu_items={"Get Help": None, "Report a bug": None, "About": None}
)

# ====== KEEP-ALIVE + MOBILE PING ======
try:
    query_params = st.query_params
    if "ping" in query_params and query_params["ping"] == "1":
        st.markdown("OK")
        st.stop()
except:
    pass

# ====== DEBOUNCE RERUN ======
if "_last_rerun" not in st.session_state:
    st.session_state._last_rerun = 0

def safe_rerun():
    now = time.time()
    if now - st.session_state._last_rerun > 0.8:  # Slightly more tolerant on mobile
        st.session_state._last_rerun = now
        st.rerun()

# --- Supabase ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Supabase credentials missing in secrets.")
        return None
    return create_client(url, key)

supabase = init_supabase()

# ====== SECRETS ======
REFRESH_INTERVAL = int(st.secrets.get("REFRESH_TOKEN_INTERVAL", 7200))  # 2 hours default (more reliable on mobile)
OWNER_CIN = st.secrets.get("OWNER_CIN")
# ... (keep all your other secrets as-is)

# ====== SESSION STATE ======
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
# ... (keep all your existing session_state initializations)

if "_session_restored" not in st.session_state:
    st.session_state._session_restored = False
if "_last_token_refresh" not in st.session_state:
    st.session_state._last_token_refresh = 0
if "_last_ping" not in st.session_state:
    st.session_state._last_ping = 0

# ====== IMPROVED COOKIE + LOCALSTORAGE (Mobile Robust) ======
def inject_storage_reader():
    js = """
    <script>
    (function() {
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }

        function setCookie(name, value, days) {
            let expires = "";
            if (days) {
                const date = new Date();
                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                expires = "; expires=" + date.toUTCString();
            }
            document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
            try { localStorage.setItem(name, value); } catch(e) {}
        }

        const refreshToken = getCookie("sb_refresh_token") || localStorage.getItem("sb_refresh_token");

        if (refreshToken) {
            const url = new URL(window.location.href);
            if (!url.searchParams.has('cookie_sb_refresh_token')) {
                url.searchParams.set('cookie_sb_refresh_token', refreshToken);
                window.history.replaceState({}, '', url);
            }
            // Force cookie refresh
            setCookie("sb_refresh_token", refreshToken, 30);
        }

        // Periodic ping for mobile keep-alive
        setInterval(() => {
            fetch(window.location.href + (window.location.search ? '&' : '?') + 'ping=1', {cache: 'no-store', mode: 'no-cors'});
        }, 45000); // every 45 seconds
    })();
    </script>
    """
    st.components.v1.html(js, height=0)

# ====== REFRESH SESSION ======
def refresh_supabase_session():
    if not supabase or not st.session_state.get("refresh_token"):
        return False
    try:
        new_session = supabase.auth.refresh_session(st.session_state.refresh_token)
        if new_session and new_session.user:
            st.session_state.user = new_session.user
            st.session_state.refresh_token = new_session.session.refresh_token
            # Update cookie
            set_cookie("sb_refresh_token", new_session.session.refresh_token, 30)
            st.session_state._last_token_refresh = time.time()
            return True
    except:
        return False
    return False

# ====== RESTORE SESSION ON LOAD ======
if not st.session_state._session_restored and supabase:
    st.session_state._session_restored = True
    inject_storage_reader()

    refresh_token = None
    try:
        if "cookie_sb_refresh_token" in st.query_params:
            refresh_token = st.query_params["cookie_sb_refresh_token"]
    except:
        pass

    if not refresh_token:
        try:
            refresh_token = st.query_params.get("cookie_sb_refresh_token")
        except:
            pass

    if refresh_token:
        try:
            new_session = supabase.auth.refresh_session(refresh_token)
            if new_session and new_session.user:
                profile = get_or_create_profile(...)  # keep your existing function
                if profile and not profile.get("is_banned"):
                    st.session_state.logged_in = True
                    st.session_state.user = new_session.user
                    st.session_state.refresh_token = new_session.session.refresh_token
                    st.session_state.profile = profile
                    st.session_state.connection_time = time.time()
                    set_cookie("sb_refresh_token", new_session.session.refresh_token, 30)
                    st.success("✅ Session restored successfully")
        except:
            pass

# ====== TOKEN REFRESH (Mobile Friendly) ======
if st.session_state.logged_in and supabase and st.session_state.get("refresh_token"):
    if time.time() - st.session_state._last_token_refresh > REFRESH_INTERVAL:
        refresh_supabase_session()

# ====== COOKIE HELPER ======
def set_cookie(name, value, days=30):
    js = f"""
    <script>
    function setCookie(name, value, days) {{
        let expires = "";
        if (days) {{
            let date = new Date();
            date.setTime(date.getTime() + (days*24*60*60*1000));
            expires = "; expires=" + date.toUTCString();
        }}
        document.cookie = name + "=" + (value || "") + expires + "; path=/; SameSite=Lax";
        try {{ localStorage.setItem(name, value); }} catch(e) {{}}
    }}
    setCookie("{name}", "{value}", {days});
    </script>
    """
    st.components.v1.html(js, height=0)

# Keep all your existing functions (LANG, helpers, render functions, etc.)

# At the very end, before if __name__ == "__main__":
if st.session_state.logged_in:
    # Extra mobile keep-alive
    if time.time() - st.session_state.get("_last_ping", 0) > 30:
        st.session_state._last_ping = time.time()
        inject_storage_reader()

# ====== MAIN APP CALL ======
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
