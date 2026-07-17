# ====== FULL app.py (Lakay se Lakay - Session Persistence Fix) ======
# Lakay se Lakay - Haitian Social Media Platform
# Lead Developer: Gesner Deslandes (Python Developer, Haiti)
# Version: 92.2.2 (Mobile + Strong Session Persistence)

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

# ====== MOBILE OPTIMIZATIONS ======
st.set_page_config(
    page_title="Lakay se Lakay", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="collapsed"   # Better on mobile
)

# ====== KEEP-ALIVE PING ======
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
    if now - st.session_state._last_rerun > 0.8:
        st.session_state._last_rerun = now
        st.rerun()

# ====== STRONG COOKIE + LOCALSTORAGE FOR MOBILE ======
def inject_storage_reader():
    js = """
    <script>
    (function() {
        function getCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i<ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }
        var refreshToken = getCookie("sb_refresh_token") || localStorage.getItem("sb_refresh_token");
        if (refreshToken) {
            var url = new URL(window.location.href);
            if (!url.searchParams.has('sb_refresh')) {
                url.searchParams.set('sb_refresh', refreshToken);
                window.history.replaceState({}, '', url);
            }
        }
        // Keep alive for mobile
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
    function setCookie(name, value, days) {{
        var expires = "";
        if (days) {{
            var date = new Date();
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

# --- Rest of your original code continues unchanged ---
# ====== DEBOUNCE RERUN ======
# (Your original code from here on)

# ====== Supabase client (your original) ======
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.warning("⚠️ Supabase credentials not found.")
        return None
    if not url.startswith("https://"):
        st.error("❌ SUPABASE_URL must start with 'https://'.")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {e}")
        return None

supabase = init_supabase()

# ====== REST OF YOUR ORIGINAL CODE (paste everything from here) ======
# Paste the rest of your original full code starting from "# --- Secrets (NO DEFAULTS..." all the way to the end.

# At the very bottom, make sure you have:
if __name__ == "__main__":
    if not st.session_state.get("logged_in", False):
        login_interface()
    else:
        main_app()
