# ====== FULL app.py - Lakay se Lakay (Mobile Fixed v92.2.2) ======
import streamlit as st
import time
from datetime import datetime
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

# ====== MOBILE OPTIMIZED CONFIG ======
st.set_page_config(
    page_title="Lakay se Lakay",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====== KEEP-ALIVE ======
if st.query_params.get("ping") == "1":
    st.markdown("OK")
    st.stop()

# ====== DEBOUNCE ======
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
        st.error("Supabase credentials missing")
        return None
    return create_client(url, key)

supabase = init_supabase()

REFRESH_INTERVAL = int(st.secrets.get("REFRESH_TOKEN_INTERVAL", 7200))

# ====== SESSION STATE ======
for key in ["logged_in", "user", "profile", "refresh_token", "_session_restored", "_last_token_refresh", "current_page"]:
    if key not in st.session_state:
        st.session_state[key] = False if key == "logged_in" else None if key != "_session_restored" else False

if "current_page" not in st.session_state:
    st.session_state.current_page = "feed"

# ====== STRONG COOKIE + KEEP ALIVE ======
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
        setInterval(() => fetch('?ping=1', {cache:'no-store'}), 40000);
    })();
    </script>
    """
    st.components.v1.html(js, height=0)

def set_cookie(name, value, days=30):
    js = f"""
    <script>
    function setCookie(n,v,d){{
        let e="";if(d){{const date=new Date();date.setTime(date.getTime()+(d*86400000));e="; expires="+date.toUTCString();}}
        document.cookie=n+"="+v+e+"; path=/; SameSite=Lax";
        try{{localStorage.setItem(n,v);}}catch(e){{}}
    }}
    setCookie("{name}","{value}",{days});
    </script>
    """
    st.components.v1.html(js, height=0)

# Restore session
if not st.session_state.get("_session_restored", False):
    st.session_state._session_restored = True
    inject_storage_reader()
    token = st.query_params.get("sb_refresh")
    if token and supabase:
        try:
            session = supabase.auth.refresh_session(token)
            if session and session.user:
                st.session_state.logged_in = True
                st.session_state.user = session.user
                st.session_state.refresh_token = session.session.refresh_token
                set_cookie("sb_refresh_token", session.session.refresh_token, 30)
        except:
            pass

# Token refresh
if st.session_state.get("logged_in") and st.session_state.get("refresh_token") and supabase:
    if time.time() - st.session_state.get("_last_token_refresh", 0) > REFRESH_INTERVAL:
        try:
            new = supabase.auth.refresh_session(st.session_state.refresh_token)
            if new and new.session:
                st.session_state.refresh_token = new.session.refresh_token
                st.session_state._last_token_refresh = time.time()
                set_cookie("sb_refresh_token", new.session.refresh_token, 30)
        except:
            pass

# ====== PASTE YOUR ORIGINAL FULL CODE BELOW THIS LINE ======
# (LANG dictionary, t() function, all helpers, render functions, login_interface, main_app, etc.)

# [YOUR ORIGINAL CODE GOES HERE - EVERYTHING FROM LANG TO THE END]

# ====== ENTRY POINT ======
if __name__ == "__main__":
    if not st.session_state.get("logged_in"):
        login_interface()
    else:
        main_app()
