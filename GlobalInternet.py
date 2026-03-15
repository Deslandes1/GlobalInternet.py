"""
GLOBALINTERNET.PY - Satellite Communication Platform
Lead Developer: Gesner Deslandes
Collaborators: Gesner Junior Deslandes, Roosevert Deslandes,
               Sebastien Stephane Deslandes, Zendaya Christelle Deslandes
Version: 5.1.0 (Fixed profile creation on post)
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import socket
import hashlib
from datetime import datetime
import requests
from supabase import create_client, Client
import io
from PIL import Image

st.set_page_config(page_title="GLOBALINTERNET.PY", page_icon="🇭🇹", layout="wide")

# --- Supabase client ---
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        st.warning("⚠️ Supabase credentials not found. User registration/login disabled.")
        return None
    if not url.startswith(("http://", "https://")):
        st.error("❌ SUPABASE_URL must start with http:// or https://")
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
OWNSPACE_PASSWORD = st.secrets.get("OwnSpace_Password", "OwnerSpace2025")

# --- Session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "profile" not in st.session_state:
    st.session_state.profile = None
if "data_comp" not in st.session_state:
    st.session_state.data_comp = 0.0
if "connection_time" not in st.session_state:
    st.session_state.connection_time = time.time()
if "posts" not in st.session_state:
    st.session_state.posts = []
if "owner_space_access" not in st.session_state:
    st.session_state.owner_space_access = False

# --- UI styling (Haitian symbol + collaborators) ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(145deg, #f0f4fa 0%, #d9e2ef 100%);
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
        padding: 10px 28px;
        font-weight: 600;
        box-shadow: 0 8px 16px rgba(0,128,255,0.2);
    }
    .stButton > button:hover {
        background: linear-gradient(105deg, #0080ff 0%, #0066cc 100%);
        box-shadow: 0 12px 24px rgba(0,128,255,0.3);
        transform: scale(1.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- Helper functions for Supabase ---

def get_or_create_profile(user_id, email):
    """Fetch profile; if missing, create one with robust error handling."""
    if supabase is None:
        st.error("Supabase not configured.")
        return None
    try:
        # Attempt to fetch existing profile
        response = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
        else:
            # No profile exists – create one
            new_profile = {
                "id": user_id,
                "full_name": email.split('@')[0],
                "avatar_url": None,
                "bio": "",
                "location": ""
            }
            insert_response = supabase.table("profiles").insert(new_profile).execute()
            if insert_response.data:
                return insert_response.data[0]
            else:
                st.error("Failed to create profile – no data returned.")
                return None
    except Exception as e:
        st.error(f"Error in get_or_create_profile: {e}")
        if hasattr(e, 'args') and len(e.args) > 0:
            st.error(f"Details: {e.args[0]}")
        return None

def update_profile(profile_data):
    if supabase is None:
        return False
    try:
        supabase.table("profiles").update(profile_data).eq("id", profile_data["id"]).execute()
        return True
    except Exception as e:
        st.error(f"Error updating profile: {e}")
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
        st.error(f"Avatar upload failed: {e}")
        return None

def load_posts():
    if supabase is None:
        return []
    try:
        response = supabase.table("posts").select(
            "*, profiles(full_name, avatar_url)"
        ).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading posts: {e}")
        return []

def create_post(user_id, content, is_public=True):
    """Create a new post with profile existence check."""
    if supabase is None:
        st.error("Supabase not configured.")
        return False
    try:
        # Ensure the user has a profile before inserting post
        profile_check = supabase.table("profiles").select("id").eq("id", user_id).execute()
        if not profile_check.data:
            st.warning("Profile missing – attempting to recreate...")
            # Try to recreate profile using email from session
            if st.session_state.user and st.session_state.user.email:
                email = st.session_state.user.email
                profile = get_or_create_profile(user_id, email)
                if not profile:
                    st.error("Could not create profile. Please contact support.")
                    return False
            else:
                st.error("User email not found in session.")
                return False
        
        # Proceed with post creation
        post = {
            "user_id": user_id,
            "content": content,
            "is_public": is_public,
            "likes_count": 0,
            "shares_count": 0,
            "created_at": datetime.now().isoformat()
        }
        result = supabase.table("posts").insert(post).execute()
        if result.data:
            st.session_state.posts = load_posts()  # refresh feed
            return True
        else:
            st.error("Post insertion returned no data.")
            return False
    except Exception as e:
        st.error(f"Error creating post: {e}")
        return False

def like_post(post_id, increment=True):
    if supabase is None:
        return
    try:
        if increment:
            supabase.rpc("increment_likes", {"post_id": post_id}).execute()
        else:
            supabase.rpc("decrement_likes", {"post_id": post_id}).execute()
    except Exception as e:
        st.error(f"Error updating likes: {e}")

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
        st.session_state.posts = load_posts()
        return True
    except Exception as e:
        st.error(f"Error sharing post: {e}")
        return False

def add_comment(post_id, user_id, content):
    if supabase is None:
        return False
    try:
        comment = {
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        supabase.table("comments").insert(comment).execute()
        return True
    except Exception as e:
        st.error(f"Error adding comment: {e}")
        return False

def load_comments(post_id):
    if supabase is None:
        return []
    try:
        response = supabase.table("comments").select(
            "*, profiles(full_name, avatar_url)"
        ).eq("post_id", post_id).order("created_at").execute()
        return response.data
    except Exception as e:
        st.error(f"Error loading comments: {e}")
        return []

# --- Health monitoring ---
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

# --- Auth (only Supabase) ---
def sign_up(email, password, full_name):
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
            st.success("Sign-up successful! Please log in.")
            return True
    except Exception as e:
        st.error(f"Sign-up failed: {e}")
        return False

def log_in(email, password):
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
            profile = get_or_create_profile(user.user.id, email)
            st.session_state.profile = profile
            st.session_state.connection_time = time.time()
            st.session_state.posts = load_posts()
            st.rerun()
    except Exception as e:
        st.error(f"Login failed: {e}")

def logout():
    if supabase:
        supabase.auth.sign_out()
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.owner_space_access = False
    st.rerun()

# --- Page functions ---
def render_feed():
    st.header("🌐 Collaboration Feed")
    with st.form("new_post", clear_on_submit=True):
        col1, col2 = st.columns([4,1])
        with col1:
            content = st.text_area("What's on your mind?", height=100)
        with col2:
            is_public = st.checkbox("Public", value=True)
        if st.form_submit_button("🚀 Post"):
            if content:
                if create_post(st.session_state.user.id, content, is_public):
                    st.success("Post published!")
                    st.rerun()
    st.divider()
    for post in st.session_state.posts:
        with st.container():
            col_a, col_b, col_c = st.columns([1,5,2])
            with col_a:
                avatar = post.get("profiles", {}).get("avatar_url")
                if avatar:
                    st.image(avatar, width=40)
                else:
                    st.markdown("👤")
            with col_b:
                st.markdown(f"**{post['profiles']['full_name']}**")
            with col_c:
                st.caption(post['created_at'][:16])
            st.markdown(f"<div class='post-card'>{post['content']}</div>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([1,1,1,4])
            with col1:
                if st.button(f"👍 {post['likes_count']}", key=f"like_{post['id']}"):
                    like_post(post['id'], increment=True)
                    st.rerun()
            with col2:
                if st.button(f"💬", key=f"comment_{post['id']}"):
                    st.session_state[f"show_comments_{post['id']}"] = not st.session_state.get(f"show_comments_{post['id']}", False)
                    st.rerun()
            with col3:
                if st.button(f"🔄 {post['shares_count']}", key=f"share_{post['id']}"):
                    share_post(post['id'], st.session_state.user.id, is_public=True)
                    st.rerun()
            if st.session_state.get(f"show_comments_{post['id']}", False):
                comments = load_comments(post['id'])
                for c in comments:
                    st.markdown(f"**{c['profiles']['full_name']}**: {c['content']}")
                with st.form(key=f"add_comment_{post['id']}"):
                    new_comment = st.text_input("Write a comment...")
                    if st.form_submit_button("Post Comment"):
                        if new_comment:
                            add_comment(post['id'], st.session_state.user.id, new_comment)
                            st.rerun()
            st.divider()

def render_profile():
    st.header("👤 My Profile")
    if st.session_state.profile is None:
        return
    profile = st.session_state.profile
    col1, col2 = st.columns([1,2])
    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=150)
        else:
            st.image("https://via.placeholder.com/150", width=150)
        uploaded = st.file_uploader("Change profile picture", type=["png","jpg","jpeg"])
        if uploaded:
            url = upload_avatar(st.session_state.user.id, uploaded)
            if url:
                profile["avatar_url"] = url
                update_profile(profile)
                st.rerun()
    with col2:
        with st.form("edit_profile"):
            full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
            bio = st.text_area("Bio", value=profile.get("bio", ""))
            location = st.text_input("Location", value=profile.get("location", ""))
            if st.form_submit_button("💾 Update Profile"):
                profile.update({"full_name": full_name, "bio": bio, "location": location})
                if update_profile(profile):
                    st.success("Profile updated!")
                    st.rerun()

def render_map():
    st.header("🛰️ Satellite Network")
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

def render_reclaim():
    st.header("🔐 Owner's Dashboard")
    duration = time.time() - st.session_state.connection_time
    st.session_state.data_comp = duration * 0.035
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Compensation", f"${st.session_state.data_comp:.4f}")
    with col2:
        st.metric("Uptime", get_uptime())
    with col3:
        st.metric("Network Users", np.random.randint(100, 500))
    st.divider()
    st.subheader("💰 Withdraw Funds")
    method = st.selectbox("Method", ["MonCash", "Bank Transfer", "Crypto"])
    amount = st.number_input("Amount ($)", 0.0, float(st.session_state.data_comp))
    if st.button("🚀 Transfer", use_container_width=True):
        if amount > 0:
            st.balloons()
            st.success(f"Transferred ${amount:.2f} via {method}")
            st.session_state.data_comp -= amount

def owner_space():
    st.header("🕊️ Owner Space (Private)")
    if not st.session_state.owner_space_access:
        with st.form("owner_space_login"):
            pwd = st.text_input("Enter Owner Space Password", type="password")
            if st.form_submit_button("Access"):
                if pwd == OWNSPACE_PASSWORD:
                    st.session_state.owner_space_access = True
                    st.rerun()
                else:
                    st.error("Invalid password")
        return
    st.success("Welcome, Owner!")
    st.markdown("### 🔑 Your Private Credentials")
    st.markdown(f"- **CIN Number:** `{OWNER_CIN}`")
    st.markdown(f"- **MonCash Business:** `{MONCASH_NUM}`")
    st.markdown(f"- **OwnerSpace Password:** `{OWNSPACE_PASSWORD}`")
    if st.button("Logout from Owner Space"):
        st.session_state.owner_space_access = False
        st.rerun()

def main_app():
    with st.sidebar:
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
        lat, sig, qual = get_network_status()
        st.markdown("### 🛡️ System Health")
        st.markdown(f"""
        <div class='health-text'>
        📡 Signal: {sig}<br>
        ⏱️ Latency: {lat}ms<br>
        📊 Quality: {qual}%<br>
        ⏰ Uptime: {get_uptime()}<br>
        🔒 Status: ENCRYPTED
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown(f"💰 **Compensation:** ${st.session_state.data_comp:.4f}")
        st.divider()
        if st.session_state.profile:
            st.markdown(f"👤 **Logged in as:** {st.session_state.profile.get('full_name', 'User')}")
        if st.button("🚪 Logout"):
            logout()
        st.divider()
        pages = {
            "📡 Feed": render_feed,
            "🛰️ Satellite Map": render_map,
            "👤 Profile": render_profile,
            "🔐 Owner's Dashboard": render_reclaim,
            "🕊️ Owner Space": owner_space
        }
        choice = st.selectbox("Menu", list(pages.keys()))
    pages[choice]()

def login_interface():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<div style='text-align: center;'><span class='haiti-symbol' style='font-size:6rem;'>🇭🇹</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #0a2a44;'>GLOBALINTERNET.PY</h1>", unsafe_allow_html=True)
        st.markdown("<div class='owner-name' style='font-size:1.8rem;'>Gesner Deslandes</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='collaborators' style='font-size:1rem;'>
            <b>Collaborators:</b><br>
            Gesner Junior Deslandes · Roosevert Deslandes · Sebastien Stephane Deslandes · Zendaya Christelle Deslandes
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("🚀 Login", use_container_width=True):
                    log_in(email, password)
        with tab2:
            with st.form("signup_form"):
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("📝 Sign Up", use_container_width=True):
                    if full_name and email and password:
                        sign_up(email, password, full_name)
                    else:
                        st.warning("Please fill all fields")
        # No admin login – only Supabase auth

if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_interface()
    else:
        main_app()
