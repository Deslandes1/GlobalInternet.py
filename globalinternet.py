# ====== FULL app.py (Lakay se Lakay - Mobile Optimized v92.2.1) ======
# Lakay se Lakay - Haitian Social Media Platform
import streamlit as st
import time
from datetime import datetime, timedelta
import requests
from supabase import create_client, Client
import hashlib
import random
import string
import json
import base64
import os
import tempfile
import asyncio
import edge_tts
from PIL import Image
import io
import re

# ====== PAGE CONFIG - MOBILE OPTIMIZED ======
st.set_page_config(
    page_title="Lakay se Lakay",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",   # Important for mobile
)

# ====== KEEP-ALIVE PING ======
try:
    if st.query_params.get("ping") == "1":
        st.markdown("OK")
        st.stop()
except:
    pass

# ====== DEBOUNCE RERUN ======
if "_last_rerun" not in st.session_state:
    st.session_state._last_rerun = 0

def safe_rerun():
    now = time.time()
    if now - st.session_state._last_rerun > 0.8:
        st.session_state._last_rerun = now
        st.rerun()

# ====== SUPABASE ======
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Supabase credentials not found in secrets.")
        return None
    return create_client(url, key)

supabase = init_supabase()

REFRESH_INTERVAL = int(st.secrets.get("REFRESH_TOKEN_INTERVAL", 7200))  # 2 hours

# ====== SESSION STATE ======
keys = ["logged_in", "user", "profile", "refresh_token", "_session_restored", "_last_token_refresh", "current_page"]
for k in keys:
    if k not in st.session_state:
        st.session_state[k] = False if k == "logged_in" else None if k != "_session_restored" else False

if "current_page" not in st.session_state:
    st.session_state.current_page = "feed"

# ====== IMPROVED COOKIE / STORAGE ======
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
        const token = getCookie("sb_refresh_token") || localStorage.getItem("sb_refresh_token");
        if (token) {
            const url = new URL(window.location.href);
            if (!url.searchParams.has('sb_refresh')) {
                url.searchParams.set('sb_refresh', token);
                window.history.replaceState({}, '', url);
            }
        }
        // Mobile keep-alive
        setInterval(() => {
            fetch(window.location.pathname + '?ping=1', {cache: 'no-store'});
        }, 40000);
    })();
    </script>
    """
    st.components.v1.html(js, height=0)

def set_cookie(name, value, days=30):
    js = f"""
    <script>
    function setCookie(n,v,d){{
        let e=""; if(d){{const date=new Date(); date.setTime(date.getTime()+(d*86400000)); e="; expires="+date.toUTCString();}}
        document.cookie = n+"="+v+e+"; path=/; SameSite=Lax";
        try{{localStorage.setItem(n,v);}}catch(e){{}}
    }}
    setCookie("{name}","{value}",{days});
    </script>
    """
    st.components.v1.html(js, height=0)

# Restore session
if not st.session_state._session_restored and supabase:
    st.session_state._session_restored = True
    inject_storage_reader()
    token = st.query_params.get("sb_refresh")
    if token:
        try:
            new_session = supabase.auth.refresh_session(token)
            if new_session and new_session.user:
                st.session_state.logged_in = True
                st.session_state.user = new_session.user
                st.session_state.refresh_token = new_session.session.refresh_token
                set_cookie("sb_refresh_token", new_session.session.refresh_token, 30)
        except:
            pass

# Token refresh
if st.session_state.logged_in and st.session_state.get("refresh_token"):
    if time.time() - st.session_state.get("_last_token_refresh", 0) > REFRESH_INTERVAL:
        try:
            new = supabase.auth.refresh_session(st.session_state.refresh_token)
            if new and new.session:
                st.session_state.refresh_token = new.session.refresh_token
                st.session_state._last_token_refresh = time.time()
                set_cookie("sb_refresh_token", new.session.refresh_token, 30)
        except:
            pass

# ====== LANGUAGE DICTIONARY (YOUR ORIGINAL) ======
# Paste your full LANG dictionary here (from your original code)
# ... [Insert your complete LANG dict and t() function] ...

# ====== ALL YOUR OTHER FUNCTIONS (get_or_create_profile, render_feed, etc.) ======
# Paste the rest of your original functions here (render_feed, render_profile, owner_space, login_interface, main_app, etc.)

# For brevity, I'm showing the critical structure. Replace the comment below with all your original code after the storage section.

# ====== YOUR ORIGINAL CODE CONTINUES HERE ======
# (All your LANG, helper functions, render functions, etc.)

# ====== MAIN APP ======
def login_interface():
    # Your original login code
    st.title("Lakay se Lakay")
    # ... rest of your login UI

def main_app():
    # Your original main_app logic
    if st.session_state.current_page == "feed":
        render_feed()
    elif st.session_state.current_page == "friends_chat":
        render_friends_page()
    # ... add all other pages

    st.sidebar.success("✅ Mobile Optimized Version")

# ====== ENTRY POINT ======
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
