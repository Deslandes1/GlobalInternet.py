
import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- SYSTEM LOGIC: MODULE SAFETY CATCH ---
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode
    VIDEO_READY = True
except ImportError:
    VIDEO_READY = False

try:
    from streamlit_folium import folium_static
    import folium
    MAP_READY = True
except ImportError:
    MAP_READY = False

try:
    from fpdf import FPDF
    PDF_READY = True
except ImportError:
    PDF_READY = False

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(page_title="GLOBALINTERNET.PY", layout="wide")

def apply_global_theme():
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background-image: url("https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        [data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.8) !important; }
        .stMarkdown, h1, h2, h3, p, label { color: white !important; }
        .log-text { color: #00ff00; font-family: monospace; font-size: 0.8rem; }
        </style>
    """, unsafe_allow_html=True)

apply_global_theme()

# Hidden Backstage Credentials
GLOBAL_PASSWORD = "20082021"
OWNER_CIN = "1248795849"
MONCASH_BIZ_NUM = "(509)-47385663"

# Session State Persistence
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "data_comp" not in st.session_state: st.session_state.data_comp = 0.0
if "posts" not in st.session_state: st.session_state.posts = []
if "system_logs" not in st.session_state: st.session_state.system_logs = []
if "profile" not in st.session_state: st.session_state.profile = {"name": "User", "image": None}

def add_log(event):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.system_logs.insert(0, f"[{timestamp}] {event}")

# --- 2. MODULE: MONCASH REPORT ENGINE ---
def generate_pdf(amount):
    if not PDF_READY: return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="OFFICIAL MONCASH TRANSACTION REPORT", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Founder: Gesner Deslandes", ln=True)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(200, 10, txt=f"Target: {MONCASH_BIZ_NUM}", ln=True)
    pdf.cell(200, 10, txt=f"Amount: ${amount:.4f}", ln=True)
    pdf.cell(200, 10, txt=f"Verification: CIN {OWNER_CIN}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. PAGE LOGIC ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Gesner Deslandes - Python Specialist</h3>", unsafe_allow_html=True)
    st.divider()
    with st.columns([1,1,1])[1]:
        pwd = st.text_input("Enter Access Password:", type="password")
        if st.button("Unlock Global Mesh", use_container_width=True):
            if pwd == GLOBAL_PASSWORD:
                st.session_state.logged_in = True
                add_log(f"User '{st.session_state.profile['name']}' joined the mesh.")
                st.rerun()
            else: st.error("Access Denied.")

def main_app():
    st.sidebar.title("GLOBALINTERNET.PY")
    st.session_state.data_comp += 0.012 # Simulated continuous data flow
    
    # SYSTEM LOG VIEW (Sidebar)
    with st.sidebar.expander("📝 System Logs"):
        for log in st.session_state.system_logs[:10]:
            st.markdown(f"<p class='log-text'>{log}</p>", unsafe_allow_html=True)
    
    menu = ["Chatbox Feed", "Live Video", "Global Satellite Map", "Profile Setup", "Owner's Reclaim"]
    choice = st.sidebar.radio("Navigation", menu)

    if choice == "Chatbox Feed":
        st.header("💬 Collaborator Chatbox")
        with st.form("chat", clear_on_submit=True):
            msg = st.text_area("Share a professional update:")
            if st.form_submit_button("Broadcast"):
                st.session_state.posts.insert(0, {"user": st.session_state.profile["name"], "text": msg})
                add_log(f"New post by {st.session_state.profile['name']}")
        for p in st.session_state.posts:
            st.chat_message("user").write(f"**{p['user']}**: {p['text']}")

    elif choice == "Live Video":
        st.header("📹 Live Video Mesh")
        st.info("Recording Tip: Start video, then right-click the player and select 'Save Video As' to save to Laptop/OneDrive.")
        if VIDEO_READY:
            webrtc_streamer(key="stream", mode=WebRtcMode.SENDRECV)
        else: st.error("Video drivers not found. Please reboot Streamlit Cloud.")

    elif choice == "Global Satellite Map":
        st.header("🛰️ Real-Time Satellite Tracking")
        if MAP_READY:
            m = folium.Map(location=[18.53, -72.33], zoom_start=3)
            folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                             attr='Esri', name='Satellite Imagery').add_to(m)
            # Green Light Markers
            folium.Marker([18.53, -72.33], popup="Gesner Deslandes (ONLINE)", icon=folium.Icon(color='green', icon='bolt', prefix='fa')).add_to(m)
            folium_static(m)
        else: st.error("Map Module (folium) is missing.")

    elif choice == "Profile Setup":
        st.header("👤 Professional Account Setup")
        st.session_state.profile["name"] = st.text_input("Full Name:", value=st.session_state.profile["name"])
        pic = st.file_uploader("Upload Profile Image:", type=['jpg', 'png'])
        if pic: st.session_state.profile["image"] = pic
        if st.button("Save Profile"): 
            st.success("Account Synced.")
            add_log("Profile settings updated.")

    elif choice == "Owner's Reclaim":
        st.header("🔐 Owner's Reclaim Interface")
        cin = st.text_input("Verify Owner CIN:", type="password")
        if cin == OWNER_CIN:
            current_pot = st.session_state.data_comp
            st.metric("Compensation Ready", f"${current_pot:.4f}")
            if st.button("Confirm Payout to MonCash"):
                st.balloons()
                if PDF_READY:
                    report = generate_pdf(current_pot)
                    st.download_button("📥 Save Transaction Report (PDF)", data=report, file_name=f"MonCash_{datetime.now().strftime('%Y%m%d')}.pdf")
                    add_log(f"Owner reclaimed ${current_pot:.2f} successfully.")
                st.session_state.data_comp = 0.0
        elif cin: st.error("Unauthorized Access.")

# --- EXECUTION ---
if not st.session_state.logged_in: login_page()
else: main_app()
