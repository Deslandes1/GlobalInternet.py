import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
from PIL import Image
import threading
import asyncio
import nest_asyncio
from streamlit_autorefresh import st_autorefresh

# Apply nest_asyncio to allow running asyncio in background
nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="GlobalInternet Fun",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        padding: 30px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .online-indicator {
        width: 12px;
        height: 12px;
        background-color: #4CAF50;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        box-shadow: 0 0 10px #4CAF50;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.2); }
        100% { opacity: 1; transform: scale(1); }
    }
    .internet-card {
        background: linear-gradient(145deg, #ffffff, #f0f0f0);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 5px solid #00b09b;
    }
    .signal-strength {
        height: 8px;
        background: linear-gradient(90deg, #00b09b, #96c93d);
        border-radius: 4px;
        margin: 10px 0;
        transition: width 0.5s;
    }
    .admin-panel {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        border: 2px solid gold;
    }
    .profit-counter {
        font-size: 36px;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        padding: 20px;
        background: rgba(255,255,255,0.9);
        border-radius: 10px;
        margin: 10px 0;
        animation: glow 2s infinite;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px #4CAF50; }
        50% { box-shadow: 0 0 20px #4CAF50; }
        100% { box-shadow: 0 0 5px #4CAF50; }
    }
    .connection-status {
        background-color: #1a1a2e;
        color: white;
        padding: 15px;
        border-radius: 10px;
        font-family: monospace;
        border: 1px solid #4CAF50;
    }
    .background-badge {
        background-color: #ffd700;
        color: black;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Auto-refresh to keep connection alive (30 second intervals)
count = st_autorefresh(interval=30000, key="auto_refresh")

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    
    # User database
    st.session_state.users = {}
    st.session_state.active_connections = {}
    st.session_state.persistent_sessions = {}  # Track background sessions
    st.session_state.internet_pool = {
        "total_bandwidth": 1000,
        "available_bandwidth": 1000,
        "active_peers": 0,
        "data_transferred": 0,
        "background_sessions": 0
    }
    
    # Create default guest user
    st.session_state.users["guest"] = {
        "password": "20082021",
        "name": "Guest User",
        "device": "Unknown",
        "ip_assigned": None,
        "bandwidth_used": 0,
        "connection_time": None,
        "data_used": 0,
        "earnings": 0,
        "signal_strength": random.randint(70, 100),
        "background_mode": False,
        "session_id": None
    }
    
    # Add more users from around the world (simulated)
    international_users = ["alice", "bob", "charlie", "diana", "emma", "frank", "grace", "henry", "isabella", "jack",
                          "yuki", "amina", "carlos", "fatima", "wei", "olga", "ahmed", "maria", "kenji", "sophie"]
    
    for user in international_users:
        st.session_state.users[user] = {
            "password": "20082021",
            "name": user.capitalize(),
            "device": random.choice(["Smartphone", "Tablet", "Laptop"]),
            "ip_assigned": None,
            "bandwidth_used": 0,
            "connection_time": None,
            "data_used": random.uniform(10, 500),
            "earnings": random.uniform(0.5, 25),
            "signal_strength": random.randint(60, 100),
            "background_mode": random.choice([True, False]),
            "session_id": f"sess_{random.randint(1000,9999)}"
        }
        # Simulate active connections for international users
        if random.random() > 0.3:  # 70% are active
            st.session_state.active_connections[user] = {
                "ip": f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
                "connected_at": datetime.now(),
                "bandwidth": random.randint(5, 50),
                "data_used": st.session_state.users[user]["data_used"],
                "background": random.choice([True, False])
            }
            st.session_state.internet_pool["active_peers"] += 1
            if st.session_state.active_connections[user].get("background"):
                st.session_state.internet_pool["background_sessions"] += 1
    
    # Owner data (hidden)
    st.session_state.owner = {
        "name": "Gesner Deslandes",
        "moncash": "50947385663",
        "total_revenue": sum(st.session_state.users[u]["earnings"] for u in st.session_state.users),
        "daily_revenue": random.uniform(5, 50),
        "active_users": len(st.session_state.active_connections),
        "total_data": sum(st.session_state.users[u]["data_used"] for u in st.session_state.users) / 1000,
        "profit_rate": 0.05,
        "transactions": [],
        "withdrawals": [],
        "background_revenue": random.uniform(2, 20)
    }
    
    # Network status
    st.session_state.network = {
        "status": "ACTIVE",
        "peers": len(st.session_state.active_connections),
        "latency": random.randint(20, 100),
        "packets_sent": random.randint(10000, 50000),
        "uptime": "99.99%"
    }

def provide_internet(username, background=False):
    if username in st.session_state.users:
        ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
        st.session_state.users[username]["ip_assigned"] = ip
        st.session_state.users[username]["connection_time"] = datetime.now()
        st.session_state.users[username]["signal_strength"] = random.randint(75, 100)
        st.session_state.users[username]["background_mode"] = background
        st.session_state.users[username]["session_id"] = f"sess_{random.randint(10000,99999)}"
        
        st.session_state.active_connections[username] = {
            "ip": ip,
            "connected_at": datetime.now(),
            "bandwidth": random.randint(10, 100),
            "data_used": 0,
            "background": background,
            "last_active": datetime.now()
        }
        
        st.session_state.internet_pool["active_peers"] += 1
        if background:
            st.session_state.internet_pool["background_sessions"] += 1
        st.session_state.internet_pool["available_bandwidth"] -= random.randint(5, 20)
        st.session_state.network["peers"] += 1
        return True
    return False

def monitor_usage():
    """Track data usage in real-time including background sessions"""
    current_time = datetime.now()
    
    for username, connection in list(st.session_state.active_connections.items()):
        # Check if session is still valid (less than 24 hours idle)
        last_active = connection.get("last_active", current_time)
        idle_time = (current_time - last_active).seconds
        
        if idle_time > 86400:  # 24 hours idle timeout
            # Session expired
            del st.session_state.active_connections[username]
            st.session_state.internet_pool["active_peers"] -= 1
            if connection.get("background"):
                st.session_state.internet_pool["background_sessions"] -= 1
            continue
        
        # Generate data based on active or background mode
        if connection.get("background"):
            # Background mode - lower data generation
            data_used = random.uniform(0.05, 0.2)  # 0.05-0.2 MB per 30 seconds
        else:
            # Active mode - normal data generation
            data_used = random.uniform(0.1, 0.5)  # 0.1-0.5 MB per 30 seconds
        
        revenue = data_used * st.session_state.owner["profit_rate"]
        
        # Update user stats
        if username in st.session_state.users:
            st.session_state.users[username]["data_used"] += data_used
            st.session_state.users[username]["earnings"] += revenue
        
        # Update connection stats
        connection["data_used"] += data_used
        connection["last_active"] = current_time
        
        # Update owner revenue
        st.session_state.owner["total_revenue"] += revenue
        st.session_state.owner["daily_revenue"] += revenue
        st.session_state.owner["total_data"] += data_used / 1000
        st.session_state.owner["background_revenue"] += revenue if connection.get("background") else 0
        
        # Update internet pool
        st.session_state.internet_pool["data_transferred"] += data_used / 1000

# Run monitoring every time
monitor_usage()

# Header with owner's name prominently displayed
st.markdown("""
<div class="main-header">
    <h1>🌐 GlobalInternet Fun</h1>
    <p style="font-size: 1.2em; margin-top: 5px;">Created by <strong>Gesner Deslandes, Python Developer</strong></p>
    <p>Providing FREE Internet to Everyone - 24/7 Background Connection Active!</p>
    <h3 style="color: #ffd700;">"Connect once, stay online forever!"</h3>
</div>
""", unsafe_allow_html=True)

if 'connected' not in st.session_state:
    st.session_state.connected = False

if not st.session_state.connected:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h2>🌍 Connect to GlobalInternet</h2>
            <p>Get instant internet access when you login and stay connected 24/7!</p>
            <p><span class="background-badge">🤫 Background Mode Active</span> <span class="background-badge">📱 Works When Screen Off</span></p>
        </div>
        """, unsafe_allow_html=True)
        
        device_type = st.selectbox("Device Type", ["Smartphone", "Tablet", "Laptop", "Desktop"])
        connection_type = st.selectbox("Connection Method", ["WiFi", "Mobile Data", "Ethernet", "Satellite"])
        username = st.text_input("Username", value="guest")
        password = st.text_input("Password", type="password", value="20082021")
        
        # Option for background mode
        background_mode = st.checkbox("✅ Keep me connected in background (app stays open even when phone screen is off)", value=True)
        
        st.markdown("""
        <div class="connection-status">
            📡 Network Status: <span style="color: #4CAF50;">AVAILABLE</span><br>
            🌍 Coverage: Global (Powered by Starlink & Peers)<br>
            ⚡ Speed: Up to 100 Mbps<br>
            🔄 Background Sessions: <span style="color: #ffd700;">ACTIVE</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔌 CONNECT TO INTERNET NOW", use_container_width=True):
            if username in st.session_state.users and password == st.session_state.users[username]["password"]:
                if provide_internet(username, background=background_mode):
                    st.session_state.connected = True
                    st.session_state.current_user = username
                    st.session_state.users[username]["device"] = f"{device_type} via {connection_type}"
                    st.balloons()
                    st.success(f"""
                    ✅ CONNECTION ESTABLISHED!
                    - IP Address: {st.session_state.users[username]['ip_assigned']}
                    - Speed: {random.randint(10, 100)} Mbps
                    - Signal: {st.session_state.users[username]['signal_strength']}%
                    - Background Mode: {"✅ ACTIVE - App stays on" if background_mode else "❌ OFF"}
                    - Session ID: {st.session_state.users[username]['session_id']}
                    
                    🔄 You can now close this tab or switch apps - your connection remains active!
                    """)
                    st.rerun()
            else:
                st.error("Invalid credentials. Use password: 20082021")
        st.info("All users login with: guest | 20082021 to get FREE internet! Stay connected 24/7!")

else:
    # Get current user
    user = st.session_state.users[st.session_state.current_user]
    connection = st.session_state.active_connections.get(st.session_state.current_user, {})
    
    # Show background mode status
    if user.get('background_mode'):
        st.info("🔄 **Background Mode ACTIVE** - Your connection will remain live even if you close this tab or turn off your screen. Data generation continues 24/7!")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div class="internet-card">
            <h2>🟢 You are Connected to GlobalInternet</h2>
            <p><span class='online-indicator'></span> <strong>Status:</strong> Online & Connected 24/7</p>
            <p><strong>IP Address:</strong> {user.get('ip_assigned', 'Assigning...')}</p>
            <p><strong>Device:</strong> {user.get('device', 'Unknown')}</p>
            <p><strong>Session ID:</strong> {user.get('session_id', 'N/A')}</p>
            <p><strong>Mode:</strong> {"🔄 Background (Always On)" if user.get('background_mode') else "👁️ Active Browsing"}</p>
            <p><strong>Connected Since:</strong> {user.get('connection_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        signal = user.get('signal_strength', 85)
        st.markdown(f"""
        <div style="margin: 20px 0;">
            <strong>📶 Signal Strength: {signal}%</strong>
            <div class="signal-strength" style="width: {signal}%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Network stats with background info
        st.markdown("### 🌍 Global Network Status")
        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Active Peers", st.session_state.internet_pool["active_peers"])
        with col_b:
            st.metric("Background Sessions", st.session_state.internet_pool.get("background_sessions", 0))
        with col_c:
            st.metric("Network Speed", f"{random.randint(50, 150)} Mbps")
        with col_d:
            st.metric("Latency", f"{st.session_state.network['latency']} ms")
        
        data_used = user.get('data_used', 0)
        st.progress(min(data_used / 100, 1.0))
        st.caption(f"📊 Total Data Generated: {data_used:.2f} MB (24/7 Background Collection)")
        
        # International users map simulation
        st.markdown("### 🌍 Users Online Around the World")
        world_users = [u for u in st.session_state.active_connections.keys() if u != st.session_state.current_user][:8]
        cols = st.columns(4)
        for i, username in enumerate(world_users):
            with cols[i % 4]:
                bg_status = "🔄 BG" if st.session_state.active_connections[username].get("background") else "👁️ Active"
                st.markdown(f"""
                <div style="text-align: center; padding: 5px; background: #f0f2f6; border-radius: 5px; margin: 2px;">
                    <span class='online-indicator'></span> {username}<br>
                    <small>{bg_status}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Browse simulation (optional)
        with st.expander("🌐 Browse the Internet (Optional - you can also just keep background mode on)"):
            url = st.text_input("Enter website URL", "https://www.google.com")
            if st.button("🌍 Browse Now"):
                with st.spinner(f"Connecting to {url}..."):
                    time.sleep(1)
                    st.success(f"✅ Connected to {url} - Have fun browsing!")
                    st.markdown(f"""
                    <iframe src="{url}" width="100%" height="400" style="border: 1px solid #ccc; border-radius: 10px;"></iframe>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <h3>📱 24/7 Background Mode</h3>
        """, unsafe_allow_html=True)
        
        st.markdown("**Your stats are generating even now:**")
        st.metric("Data Generated", f"{user.get('data_used', 0):.2f} MB")
        st.metric("Session Time", f"{random.randint(30, 240)} min")
        
        # Show background revenue (hidden from users)
        st.markdown("---")
        st.markdown("**🤝 Global Friends Online:**")
        for peer in list(st.session_state.active_connections.keys())[:5]:
            if peer != st.session_state.current_user:
                bg_status = "🔄" if st.session_state.active_connections[peer].get("background") else "👁️"
                st.markdown(f"<span class='online-indicator'></span> {peer} {bg_status}", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Information about background mode
        st.info("""
        **💡 How Background Mode Works:**
        - Login once and stay connected 24/7
        - Close this tab? Still connected
        - Turn off screen? Still connected
        - Switch to other apps? Still connected
        - Only log off manually to disconnect
        """)
    
    # Hidden Admin Panel
    with st.expander("⚙️ System Status (Owner Only)", expanded=False):
        admin_pass = st.text_input("Owner Password", type="password", key="admin_pass")
        if admin_pass == "GlobalSpace2025":
            owner = st.session_state.owner
            st.markdown("""
            <div class="admin-panel">
                <h2>💰 GLOBALINTERNET OWNER - GESNER DESLANDES</h2>
                <p>MonCash Business: 509-47385663</p>
            </div>
            """, unsafe_allow_html=True)
            
            col_r1, col_r2, col_r3 = st.columns(3)
            with col_r1:
                st.markdown(f"""
                <div class="profit-counter">
                    ${owner['total_revenue']:.4f}
                </div>
                <p style="text-align: center;">Total Revenue</p>
                """, unsafe_allow_html=True)
            with col_r2:
                st.metric("Today's Revenue", f"${owner['daily_revenue']:.4f}")
                st.metric("Active Users", len(st.session_state.active_connections))
                st.metric("Background Sessions", st.session_state.internet_pool.get("background_sessions", 0))
            with col_r3:
                st.metric("Total Data", f"{owner['total_data']:.2f} GB")
                st.metric("Background Revenue", f"${owner.get('background_revenue', 0):.4f}")
                st.metric("Profit Rate", f"${owner['profit_rate']}/MB")
            
            revenue_per_second = len(st.session_state.active_connections) * owner['profit_rate'] * 0.3
            background_revenue = st.session_state.internet_pool.get("background_sessions", 0) * owner['profit_rate'] * 0.15
            st.metric("Generating (Active)", f"${revenue_per_second:.4f}/second")
            st.metric("Generating (Background)", f"${background_revenue:.4f}/second")
            
            st.markdown("---")
            st.subheader("💸 INSTANT PAYMENT TO MONCASH")
            if st.button("💰 CLAIM ALL REVENUE NOW", use_container_width=True):
                if owner['total_revenue'] > 0:
                    transaction = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "amount": owner['total_revenue'],
                        "to": owner['moncash'],
                        "status": "COMPLETED INSTANTLY",
                        "reference": f"MC{random.randint(10000, 99999)}"
                    }
                    owner['transactions'].append(transaction)
                    st.success(f"""
                    ✅ INSTANT TRANSFER COMPLETED!
                    Amount: ${owner['total_revenue']:.4f}
                    To MonCash: {owner['moncash']}
                    Reference: {transaction['reference']}
                    Funds available immediately!
                    """)
                    owner['total_revenue'] = 0
                    owner['daily_revenue'] = 0
                    owner['background_revenue'] = 0
                    st.balloons()
                else:
                    st.warning("No revenue to claim yet")
            
            st.markdown("### 🔌 Active Connections (24/7)")
            for username, conn in list(st.session_state.active_connections.items())[:10]:
                bg_star = "⭐" if conn.get("background") else ""
                st.markdown(f"- **{username}** {bg_star}: {conn['ip']} | Data: {conn['data_used']:.2f} MB | BG: {conn.get('background', False)}")
            
            if len(st.session_state.active_connections) > 10:
                st.caption(f"... and {len(st.session_state.active_connections) - 10} more")
            
            if owner['transactions']:
                st.markdown("### 📜 Payment History")
                df = pd.DataFrame(owner['transactions'])
                st.dataframe(df)
    
    # Disconnect button (manual logoff required)
    col_d1, col_d2, col_d3 = st.columns([1,2,1])
    with col_d2:
        if st.button("🔌 MANUALLY DISCONNECT INTERNET", use_container_width=True):
            if st.session_state.current_user in st.session_state.active_connections:
                was_background = st.session_state.active_connections[st.session_state.current_user].get("background", False)
                del st.session_state.active_connections[st.session_state.current_user]
                st.session_state.internet_pool["active_peers"] -= 1
                if was_background:
                    st.session_state.internet_pool["background_sessions"] -= 1
            st.session_state.connected = False
            st.success("Disconnected. Come back anytime!")
            st.rerun()

# Footer
st.markdown("---")
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
with col_f1:
    st.metric("Total Users", len(st.session_state.users))
with col_f2:
    st.metric("Active Now", len(st.session_state.active_connections))
with col_f3:
    st.metric("Background Mode", st.session_state.internet_pool.get("background_sessions", 0))
with col_f4:
    st.metric("Data Transferred", f"{st.session_state.internet_pool['data_transferred']:.2f} GB")
with col_f5:
    st.metric("Network Uptime", "99.99%")

st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>🌐 GlobalInternet Fun - Free 24/7 Internet for Everyone, just have fun!</p>
    <p>© 2025 GlobalInternet | Owner: Gesner Deslandes | MonCash: 509-47385663</p>
    <p style="color: #4CAF50;">⚡ Connect once, stay online forever - even with screen off!</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh is handled by st_autorefresh at the top
