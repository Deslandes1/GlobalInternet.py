import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
import hashlib
import socket
import threading
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="GlobalInternet Provider",
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    
    # User database
    st.session_state.users = {}
    st.session_state.active_connections = {}
    st.session_state.internet_pool = {
        "total_bandwidth": 1000,  # Mbps
        "available_bandwidth": 1000,
        "active_peers": 0,
        "data_transferred": 0  # GB
    }
    
    # Create default guest user
    st.session_state.users["guest"] = {
        "password": "20082021",
        "name": "Guest User",
        "device": "Unknown",
        "ip_assigned": None,
        "bandwidth_used": 0,
        "connection_time": None,
        "data_used": 0,  # MB
        "earnings": 0,  # $ earned for owner
        "signal_strength": random.randint(70, 100)
    }
    
    # Owner data (hidden)
    st.session_state.owner = {
        "name": "Gesner Deslandes",
        "moncash": "50947385663",
        "total_revenue": 0.0,
        "daily_revenue": 0.0,
        "active_users": 0,
        "total_data": 0.0,  # GB
        "profit_rate": 0.05,  # $ per MB
        "transactions": [],
        "withdrawals": []
    }
    
    # Network status
    st.session_state.network = {
        "status": "ACTIVE",
        "peers": 0,
        "latency": random.randint(20, 100),
        "packets_sent": 0,
        "uptime": "99.99%"
    }

# Function to simulate internet connection
def provide_internet(username):
    """Provide internet connection to user"""
    if username in st.session_state.users:
        # Assign IP address
        ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
        st.session_state.users[username]["ip_assigned"] = ip
        st.session_state.users[username]["connection_time"] = datetime.now()
        st.session_state.users[username]["signal_strength"] = random.randint(75, 100)
        
        # Add to active connections
        st.session_state.active_connections[username] = {
            "ip": ip,
            "connected_at": datetime.now(),
            "bandwidth": random.randint(10, 100),  # Mbps
            "data_used": 0
        }
        
        # Update network stats
        st.session_state.internet_pool["active_peers"] += 1
        st.session_state.internet_pool["available_bandwidth"] -= random.randint(5, 20)
        st.session_state.network["peers"] += 1
        
        return True
    return False

# Function to monitor usage and generate revenue
def monitor_usage():
    """Track data usage and convert to revenue"""
    for username, connection in list(st.session_state.active_connections.items()):
        # Simulate data usage (1-5 MB per second)
        data_used = random.uniform(0.1, 0.5)  # MB
        revenue = data_used * st.session_state.owner["profit_rate"]
        
        # Update user stats
        st.session_state.users[username]["data_used"] += data_used
        st.session_state.users[username]["earnings"] += revenue
        
        # Update connection stats
        connection["data_used"] += data_used
        
        # Update owner revenue
        st.session_state.owner["total_revenue"] += revenue
        st.session_state.owner["daily_revenue"] += revenue
        st.session_state.owner["total_data"] += data_used / 1000  # Convert to GB
        
        # Update internet pool
        st.session_state.internet_pool["data_transferred"] += data_used / 1000

# Header
st.markdown("""
<div class="main-header">
    <h1>🌐 GlobalInternet Provider</h1>
    <p>Providing FREE Internet to Everyone - Connect, Browse, Earn!</p>
    <h3 style="color: #ffd700;">"Internet for All, Revenue for the Creator"</h3>
</div>
""", unsafe_allow_html=True)

# Login/Connection Section
if 'connected' not in st.session_state:
    st.session_state.connected = False

if not st.session_state.connected:
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <h2>🌍 Connect to GlobalInternet</h2>
            <p>Get instant internet access when you login!</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Device detection simulation
        device_type = st.selectbox("Device Type", ["Smartphone", "Tablet", "Laptop", "Desktop"])
        connection_type = st.selectbox("Connection Method", ["WiFi", "Mobile Data", "Ethernet", "Satellite"])
        
        username = st.text_input("Username", value="guest")
        password = st.text_input("Password", type="password", value="20082021")
        
        # Show network availability
        st.markdown("""
        <div class="connection-status">
            📡 Network Status: <span style="color: #4CAF50;">AVAILABLE</span><br>
            🌍 Coverage: Global (Powered by Starlink & Peers)<br>
            ⚡ Speed: Up to 100 Mbps
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔌 CONNECT TO INTERNET NOW", use_container_width=True):
            if username in st.session_state.users and password == st.session_state.users[username]["password"]:
                # Provide internet connection
                if provide_internet(username):
                    st.session_state.connected = True
                    st.session_state.current_user = username
                    st.session_state.users[username]["device"] = f"{device_type} via {connection_type}"
                    
                    st.balloons()
                    st.success(f"""
                    ✅ CONNECTION ESTABLISHED!
                    - IP Address: {st.session_state.users[username]['ip_assigned']}
                    - Speed: {random.randint(10, 100)} Mbps
                    - Signal: {st.session_state.users[username]['signal_strength']}%
                    - You can now browse the internet!
                    """)
                    st.rerun()
            else:
                st.error("Invalid credentials. Use password: 20082021")
        
        st.info("All users login with: guest | 20082021 to get FREE internet!")

else:
    # Monitor usage in real-time
    monitor_usage()
    
    # Get current user
    user = st.session_state.users[st.session_state.current_user]
    connection = st.session_state.active_connections.get(st.session_state.current_user, {})
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="internet-card">
            <h2>🟢 You are Connected to GlobalInternet</h2>
            <p><span class='online-indicator'></span> <strong>Status:</strong> Online & Browsing</p>
            <p><strong>IP Address:</strong> {user.get('ip_assigned', 'Assigning...')}</p>
            <p><strong>Device:</strong> {user.get('device', 'Unknown')}</p>
            <p><strong>Connected Since:</strong> {user.get('connection_time', datetime.now()).strftime('%H:%M:%S')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Signal strength meter
        signal = user.get('signal_strength', 85)
        st.markdown(f"""
        <div style="margin: 20px 0;">
            <strong>📶 Signal Strength: {signal}%</strong>
            <div class="signal-strength" style="width: {signal}%;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Network stats
        st.markdown("### 🌍 Global Network Status")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Active Peers", st.session_state.internet_pool["active_peers"])
        with col_b:
            st.metric("Network Speed", f"{random.randint(50, 150)} Mbps")
        with col_c:
            st.metric("Latency", f"{st.session_state.network['latency']} ms")
        
        # Internet usage meter
        data_used = user.get('data_used', 0)
        st.progress(min(data_used / 100, 1.0))
        st.caption(f"📊 Data Used Today: {data_used:.2f} MB")
        
        # Browse simulation
        st.markdown("### 🌐 Browse the Internet")
        url = st.text_input("Enter website URL", "https://www.google.com")
        if st.button("🌍 Browse Now"):
            with st.spinner(f"Connecting to {url}..."):
                time.sleep(1)
                st.success(f"✅ Connected to {url} - You are now browsing!")
                st.markdown(f"""
                <iframe src="{url}" width="100%" height="400" style="border: 1px solid #ccc; border-radius: 10px;"></iframe>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 15px; color: white;">
            <h3>📱 Quick Actions</h3>
        """, unsafe_allow_html=True)
        
        # Quick browse options
        st.markdown("**Popular Sites:**")
        sites = ["Google", "YouTube", "Facebook", "Twitter", "Wikipedia"]
        for site in sites:
            if st.button(f"📌 {site}", key=site):
                st.info(f"Opening {site}...")
                time.sleep(0.5)
                st.success(f"✅ Connected to {site}")
        
        # Data usage stats
        st.markdown("---")
        st.markdown(f"**Your Usage:**")
        st.metric("Data Used", f"{user.get('data_used', 0):.2f} MB")
        st.metric("Session Duration", f"{random.randint(5, 60)} min")
        
        # Peer connections
        st.markdown("---")
        st.markdown("**🤝 Connected Peers:**")
        for peer in list(st.session_state.active_connections.keys())[:3]:
            if peer != st.session_state.current_user:
                st.markdown(f"<span class='online-indicator'></span> {peer}", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Hidden Admin Panel (for owner only)
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
            
            # Revenue display
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
            
            with col_r3:
                st.metric("Total Data", f"{owner['total_data']:.2f} GB")
                st.metric("Profit Rate", f"${owner['profit_rate']}/MB")
            
            # Live revenue ticker
            st.markdown("### 📈 Live Revenue Generation")
            revenue_per_second = len(st.session_state.active_connections) * owner['profit_rate'] * 0.3
            st.metric("Generating", f"${revenue_per_second:.4f}/second")
            
            # Transfer to MonCash
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
                    
                    # Reset revenue
                    owner['total_revenue'] = 0
                    owner['daily_revenue'] = 0
                    st.balloons()
                else:
                    st.warning("No revenue to claim yet")
            
            # Active connections
            st.markdown("### 🔌 Active Connections")
            for username, conn in st.session_state.active_connections.items():
                st.markdown(f"""
                - **{username}**: {conn['ip']} | Data: {conn['data_used']:.2f} MB
                """)
            
            # Transaction history
            if owner['transactions']:
                st.markdown("### 📜 Payment History")
                df = pd.DataFrame(owner['transactions'])
                st.dataframe(df)
    
    # Disconnect button
    if st.button("🔌 Disconnect Internet", use_container_width=True):
        if st.session_state.current_user in st.session_state.active_connections:
            del st.session_state.active_connections[st.session_state.current_user]
            st.session_state.internet_pool["active_peers"] -= 1
        st.session_state.connected = False
        st.rerun()

# Footer with live stats
st.markdown("---")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
with col_f1:
    st.metric("Total Users", len(st.session_state.users))
with col_f2:
    st.metric("Active Now", len(st.session_state.active_connections))
with col_f3:
    st.metric("Data Transferred", f"{st.session_state.internet_pool['data_transferred']:.2f} GB")
with col_f4:
    st.metric("Network Uptime", "99.99%")

st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>🌐 GlobalInternet Provider - Internet for Everyone, Revenue for the Creator</p>
    <p>© 2025 GlobalInternet | Owner: Gesner Deslandes | MonCash: 509-47385663</p>
    <p style="color: #4CAF50;">⚡ When you connect, you help provide internet to others and generate revenue!</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh to update stats
if st.session_state.get('connected', False):
    time.sleep(2)
    st.rerun()
