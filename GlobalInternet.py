import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
import hashlib
from supabase import create_client

st.set_page_config(page_title="GlobalInternet Fun", page_icon="🌐", layout="wide")

# Custom CSS (keep as before, but shortened for space)
st.markdown("""
<style> ... </style>  // (copy your full CSS here, but I'm omitting for brevity)
""", unsafe_allow_html=True)

# Hash function
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# Initialize session state
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.demo = False
    st.session_state.supabase = None
    st.session_state.connected = False

    # Owner data – stored as dict, no .items() used anywhere
    st.session_state.owner = {
        "name": "Gesner Deslandes",
        "moncash": "50947385663",
        "total_revenue": 0.0,
        "daily_revenue": 0.0,
        "total_data": 0.0,
        "transactions": []
    }

# Try to connect Supabase
try:
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        if isinstance(url, str) and isinstance(key, str):
            st.session_state.supabase = create_client(url, key)
            st.session_state.connected = True
        else:
            st.session_state.connected = False
    else:
        st.session_state.connected = False
except:
    st.session_state.connected = False

# Header
st.markdown("<h1 style='text-align:center;color:#00b09b;'>🌐 GlobalInternet Fun</h1><p style='text-align:center;'>Created by <strong>Gesner Deslandes, Python Developer</strong></p>", unsafe_allow_html=True)

# Login / Signup section
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if not st.session_state.connected:
            st.warning("⚠️ Demo mode: Use guest/20082021")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                if st.session_state.connected and st.session_state.supabase:
                    # real login
                    resp = st.session_state.supabase.table("users").select("*").eq("username", username).execute()
                    if resp.data and len(resp.data)>0 and resp.data[0]["password"] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.user = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                else:
                    # demo login
                    if username == "guest" and password == "20082021":
                        st.session_state.logged_in = True
                        st.session_state.user = "guest"
                        st.session_state.demo = True
                        st.rerun()
                    else:
                        st.error("Demo: use guest/20082021")
        with tab2:
            new_user = st.text_input("Username", key="signup_user")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            confirm = st.text_input("Confirm", type="password", key="signup_confirm")
            email = st.text_input("Email (optional)")
            agree = st.checkbox("I agree")
            if st.button("Sign Up"):
                if not agree:
                    st.error("You must agree")
                elif new_pass != confirm:
                    st.error("Passwords do not match")
                elif len(new_user) < 3:
                    st.error("Username too short")
                elif not st.session_state.connected:
                    st.error("Supabase not connected – cannot create account")
                else:
                    # check if exists
                    resp = st.session_state.supabase.table("users").select("*").eq("username", new_user).execute()
                    if resp.data and len(resp.data)>0:
                        st.error("Username taken")
                    else:
                        data = {
                            "username": new_user,
                            "password": hash_password(new_pass),
                            "email": email,
                            "created_at": datetime.now().isoformat(),
                            "data_used": 0.0,
                            "earnings": 0.0,
                            "last_active": datetime.now().isoformat()
                        }
                        st.session_state.supabase.table("users").insert(data).execute()
                        st.session_state.logged_in = True
                        st.session_state.user = new_user
                        st.rerun()

# Main app when logged in
else:
    user = st.session_state.user
    st.sidebar.markdown(f"**👤 {user}**")
    if st.session_state.demo:
        st.sidebar.info("Demo mode")
    st.sidebar.markdown("---")
    
    # Simulate data usage (revenue generation)
    data = random.uniform(1, 10)
    rev = data * 0.05
    st.session_state.owner["total_revenue"] += rev
    st.session_state.owner["daily_revenue"] += rev
    st.session_state.owner["total_data"] += data / 1000
    
    st.sidebar.metric("Data used", f"{data:.1f} MB")
    
    # Main content
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🟢 You are connected")
        st.info(f"IP: 10.0.{random.randint(1,255)}.{random.randint(1,255)}")
        st.progress(random.uniform(0.5,1.0))
    with col2:
        st.markdown("### Quick actions")
        st.button("📱 YouTube")
        st.button("📘 Facebook")
    
    # Owner panel – NO .items() used anywhere
    with st.expander("⚙️ Owner Panel"):
        pw = st.text_input("Owner password", type="password")
        if pw == "OwnerSpace2025":
            st.markdown("### Gesner Deslandes")
            st.markdown(f"MonCash: {st.session_state.owner['moncash']}")
            colr1, colr2 = st.columns(2)
            with colr1:
                st.metric("Total revenue", f"${st.session_state.owner['total_revenue']:.4f}")
                st.metric("Today", f"${st.session_state.owner['daily_revenue']:.4f}")
            with colr2:
                st.metric("Total data", f"{st.session_state.owner['total_data']:.2f} GB")
            if st.button("💰 Transfer to MonCash"):
                if st.session_state.owner['total_revenue'] > 0:
                    st.success(f"Sent ${st.session_state.owner['total_revenue']:.4f} to MonCash")
                    st.session_state.owner['total_revenue'] = 0
                    st.session_state.owner['daily_revenue'] = 0
                else:
                    st.warning("No funds")
    
    if st.button("🔌 Disconnect"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align:center;'>© 2025 Gesner Deslandes | MonCash: 509-47385663</p>", unsafe_allow_html=True)
