import streamlit as st
import pandas as pd
import time
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from streamlit_folium import folium_static
import folium
from fpdf import FPDF
from datetime import datetime

# --- 1. SYSTEM CONFIGURATION ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

# Hidden Backstage Credentials
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_BIZ_NUM = "(509)-47385663"

# --- 2. THEME & STYLING ---
def apply_theme():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
            background-size: cover;
            background-attachment: fixed;
        }
        .report-btn { background-color: #2ecc71; color: white; border-radius: 5px; padding: 10px; }
        </style>
    """, unsafe_allow_html=True)

apply_theme()

# --- 3. SESSION STATE ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "data_comp" not in st.session_state: st.session_state.data_comp = 0.0
if "profile" not in st.session_state: st.session_state.profile = {"name": "User", "image": None}

# --- 4. TRANSACTIONAL REPORT GENERATOR ---
def generate_moncash_report(amount):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="MONCASH BUSINESS TRANSACTION REPORT", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Owner: Gesner Deslandes", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(200, 10, txt=f"MonCash Number: {MONCASH_BIZ_NUM}", ln=True)
    pdf.cell(200, 10, txt=f"Transaction Status: SUCCESSFUL", ln=True)
    pdf.set_text_color(46, 204, 113) # Green color for amount
    pdf.cell(200, 10, txt=f"Amount Reclaimed: ${amount:.4f}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. MAIN APP MODULES ---

def main_app():
    st.sidebar.title("GLOBALINTERNET.PY")
    st.session_state.data_comp += 0.015 # Continuous flow
    
    menu = ["Chatbox Feed", "Live Video", "Global Satellite Map", "Profile Setup", "Owner's Reclaim"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "Live Video":
        st.header("📹 Live Video & Automatic Recording")
        st.info("💡 To save: Click 'Start', then right-click the video and select 'Save Video As' to store it on your Phone, Laptop, or OneDrive.")
        webrtc_streamer(key="recording", mode=WebRtcMode.SENDRECV)

    elif choice == "Owner's Reclaim":
        st.header("🔐 Owner's Reclaim & Reporting")
        cin = st.text_input("Enter Owner CIN:", type="password")
        if cin == OWNER_CIN:
            amount_to_claim = st.session_state.data_comp
            st.metric("Accumulated Funds", f"${amount_to_claim:.4f}")
            
            if st.button("Confirm Withdrawal"):
                st.balloons()
                st.success(f"Funds cleared to {MONCASH_BIZ_NUM}")
                
                # Generate Report
                report_data = generate_moncash_report(amount_to_claim)
                st.download_button(
                    label="📥 Download Transaction Report (PDF)",
                    data=report_data,
                    file_name=f"MonCash_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                st.session_state.data_comp = 0.0

    # (Other modules like Map and Chatbox remain here)

# --- EXECUTION ---
if not st.session_state.logged_in:
    # (Login screen code here)
    st.title("GLOBALINTERNET.PY Login")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if pwd == GLOBAL_PASSWORD: 
            st.session_state.logged_in = True
            st.rerun()
else:
    main_app()
