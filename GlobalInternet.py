import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
import random
from PIL import Image
import io
import base64
import hashlib
import json

# Page configuration
st.set_page_config(
    page_title="GlobalInternet Network",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    .online-indicator {
        width: 10px;
        height: 10px;
        background-color: #4CAF50;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .admin-section {
        background-color: #1a1a2e;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border: 2px solid #4CAF50;
    }
    .admin-hidden {
        display: none;
    }
    .balance-display {
        font-size: 24px;
        font-weight: bold;
        color: #4CAF50;
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin: 10px 0;
    }
    .data-usage {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with admin data
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'profile_pic' not in st.session_state:
    st.session_state.profile_pic = None
if 'online_users' not in st.session_state:
    st.session_state.online_users = {}
if 'feed_posts' not in st.session_state:
    st.session_state.feed_posts = []
if 'chats' not in st.session_state:
    st.session_state.chats = {}
if 'notifications' not in st.session_state:
    st.session_state.notifications = []
if 'live_streams' not in st.session_state:
    st.session_state.live_streams = []

# Admin data (hidden from users)
if 'admin_data' not in st.session_state:
    st.session_state.admin_data = {
        "owner": "Gesner Deslandes",
        "moncash_number": "50947385663",
        "total_earnings": 0.0,
        "daily_earnings": 0.0,
        "total_users": 0,
        "active_users": 0,
        "data_transferred": 0.0,  # in GB
        "transactions": [],
        "withdrawals": []
    }

# User data with internet sharing
if 'users' not in st.session_state:
    st.session_state.users = {
        "guest": {
            "password": "20082021", 
            "name": "Guest User", 
            "online": False, 
            "profile_pic": None, 
            "bio": "",
            "data_shared": 0.0,  # GB shared
            "earnings": 0.0,  # Personal earnings
            "device_info": {},
            "last_seen": None,
            "ip_address": None
        }
    }

# Header
st.markdown("""
<div class="main-header">
    <h1>🌐 GlobalInternet Network</h1>
    <p>Connecting everyone around the world - Share Internet, Earn Money!</p>
</div>
""", unsafe_allow_html=True)

# Login System
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/globe.png", width=100)
        st.subheader("Welcome to GlobalInternet")
        
        # Device info capture (simulated)
        username = st.text_input("Username", value="guest")
        password = st.text_input("Password", type="password")
        
        # Simulate device detection
        device_type = random.choice(["Mobile", "Desktop", "Tablet"])
        browser = random.choice(["Chrome", "Safari", "Firefox"])
        
        st.caption(f"📱 Detected device: {device_type} | {browser}")
        
        if st.button("🌐 Login & Share Internet", use_container_width=True):
            if username in st.session_state.users and password == st.session_state.users[username]["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.online_users[username] = True
                
                # Capture device info
                st.session_state.users[username]["device_info"] = {
                    "type": device_type,
                    "browser": browser,
                    "login_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "ip": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}"
                }
                st.session_state.users[username]["last_seen"] = datetime.now()
                
                # Welcome notification
                st.session_state.notifications.append(f"👋 Welcome back, {username}! Internet sharing active.")
                
                # Update admin stats
                st.session_state.admin_data["total_users"] = len(st.session_state.users)
                st.session_state.admin_data["active_users"] = sum(1 for u in st.session_state.online_users.values() if u)
                
                st.rerun()
            else:
                st.error("Invalid credentials. Use password: 20082021")
        
        st.info("Default login: username: guest | password: 20082021")
        
        # Show network stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌍 Users Online", random.randint(50, 200))
        with col2:
            st.metric("📊 Data Shared", f"{random.randint(100, 500)} GB")
        with col3:
            st.metric("💰 Total Earned", f"${random.randint(1000, 5000)}")
            
else:
    # Main App Interface
    st.sidebar.image("https://img.icons8.com/fluency/96/globe.png", width=50)
    st.sidebar.title(f"Welcome, {st.session_state.username}! 🌍")
    
    # Online users count
    online_count = sum(1 for user in st.session_state.online_users.values() if user)
    st.sidebar.markdown(f"<span class='online-indicator'></span> {online_count} Online Now", unsafe_allow_html=True)
    
    # Show data sharing status
    user_data = st.session_state.users[st.session_state.username]
    if 'data_shared' in user_data:
        st.sidebar.markdown(f"""
        <div class="data-usage">
            📊 Data Shared Today: {user_data['data_shared']:.2f} GB<br>
            💰 Your Earnings: ${user_data['earnings']:.2f}
        </div>
        """, unsafe_allow_html=True)
    
    # Navigation (Admin section hidden in menu but accessible via secret)
    menu_options = ["🏠 Home Feed", "👤 My Profile", "💬 Chats", "📹 Video Calls", "👥 Groups", "🔴 Live Now", "🔔 Notifications"]
    
    # Secret admin access (only for owner)
    if st.session_state.username == "guest":  # You can change this to your specific username
        menu_options.append("⚡ Admin Panel (Owner Only)")
    
    menu = st.sidebar.radio("Navigate", menu_options)
    
    # Profile Picture Upload Section
    if menu == "👤 My Profile":
        st.header("👤 My Profile")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.session_state.profile_pic:
                st.image(st.session_state.profile_pic, width=150, caption="Your Profile Picture")
            else:
                st.image("https://img.icons8.com/fluency/96/user-male.png", width=150, caption="No Profile Picture")
            
            uploaded_file = st.file_uploader("Upload Profile Picture", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                st.session_state.profile_pic = Image.open(uploaded_file)
                st.success("Profile picture updated!")
                st.rerun()
        
        with col2:
            st.subheader(f"@{st.session_state.username}")
            bio = st.text_area("Bio", value=st.session_state.users[st.session_state.username].get("bio", ""))
            if st.button("Update Bio"):
                st.session_state.users[st.session_state.username]["bio"] = bio
                st.success("Bio updated!")
            
            # Device info
            device_info = st.session_state.users[st.session_state.username].get("device_info", {})
            if device_info:
                st.markdown("### 📱 Connected Device")
                st.write(f"**Device:** {device_info.get('type', 'Unknown')}")
                st.write(f"**Browser:** {device_info.get('browser', 'Unknown')}")
                st.write(f"**IP Address:** {device_info.get('ip', 'Unknown')}")
                st.write(f"**Last Login:** {device_info.get('login_time', 'Unknown')}")
            
            st.markdown(f"<span class='online-indicator'></span> You are online & sharing internet", unsafe_allow_html=True)
    
    # Home Feed
    elif menu == "🏠 Home Feed":
        st.header("🏠 Global Feed")
        
        # Simulate data sharing while scrolling feed
        data_used = random.uniform(0.01, 0.05)
        st.session_state.users[st.session_state.username]["data_shared"] += data_used
        st.session_state.users[st.session_state.username]["earnings"] += data_used * 0.1  # $0.10 per GB
        
        # Update admin earnings
        st.session_state.admin_data["total_earnings"] += data_used * 0.1
        st.session_state.admin_data["data_transferred"] += data_used
        
        # Create new post
        with st.expander("📝 Create a Post", expanded=True):
            post_content = st.text_area("What's on your mind?", height=100)
            post_image = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'], key="post_image")
            
            if st.button("📤 Post to Feed", use_container_width=True):
                if post_content or post_image:
                    new_post = {
                        "user": st.session_state.username,
                        "content": post_content,
                        "image": post_image if post_image else None,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "likes": 0,
                        "dislikes": 0,
                        "emojis": {"👍": 0, "❤️": 0, "😂": 0, "😮": 0, "😢": 0, "😡": 0},
                        "comments": [],
                        "liked_by": [],
                        "disliked_by": []
                    }
                    st.session_state.feed_posts.insert(0, new_post)
                    st.success("Post published!")
                    st.rerun()
        
        # Display feed with data sharing indicator
        st.caption(f"📊 Data shared while scrolling: {data_used:.3f} GB (Earned: ${data_used * 0.1:.3f})")
        
        for idx, post in enumerate(st.session_state.feed_posts):
            with st.container():
                st.markdown(f"""
                <div class="feed-post">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div class="user-avatar">{post['user'][0].upper()}</div>
                        <div style="margin-left: 10px;">
                            <strong>@{post['user']}</strong><br>
                            <small>{post['timestamp']}</small>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                if post['content']:
                    st.write(post['content'])
                
                if post['image']:
                    st.image(post['image'])
                
                # Interaction buttons
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    if st.button(f"👍 {post['likes']}", key=f"like_{idx}"):
                        post['likes'] += 1
                        st.rerun()
                
                with col2:
                    if st.button(f"👎 {post['dislikes']}", key=f"dislike_{idx}"):
                        post['dislikes'] += 1
                        st.rerun()
                
                with col3:
                    emoji = st.selectbox("😊", ["👍", "❤️", "😂", "😮", "😢", "😡"], key=f"emoji_{idx}")
                    if st.button("Add", key=f"add_emoji_{idx}"):
                        post['emojis'][emoji] += 1
                        st.rerun()
                
                with col4:
                    st.write(f"💬 {len(post['comments'])}")
                
                with col5:
                    st.write("🔗 Share")
                
                # Display emojis
                emoji_display = " ".join([f"{e} {c}" for e, c in post['emojis'].items() if c > 0])
                if emoji_display:
                    st.markdown(f"**Reactions:** {emoji_display}")
                
                # Comments section
                with st.expander(f"💬 Comments ({len(post['comments'])})"):
                    for comment in post['comments']:
                        st.markdown(f"**@{comment['user']}:** {comment['text']}")
                    
                    new_comment = st.text_input("Write a comment...", key=f"comment_{idx}")
                    if st.button("Post Comment", key=f"post_comment_{idx}"):
                        if new_comment:
                            post['comments'].append({
                                "user": st.session_state.username,
                                "text": new_comment,
                                "timestamp": datetime.now().strftime("%H:%M")
                            })
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # ADMIN PANEL - SECRET SECTION (Only visible to owner)
    elif menu == "⚡ Admin Panel (Owner Only)":
        st.markdown("""
        <div class="admin-section">
            <h2>⚡ GLOBALSPACE OWNER ADMIN PANEL</h2>
            <p>This section is hidden from users - MonCash Business Integration</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Admin authentication (double security)
        admin_pass = st.text_input("Owner Password", type="password")
        
        if admin_pass == "GlobalSpace2025":  # Secret admin password
            admin = st.session_state.admin_data
            
            # Display admin dashboard
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div class="balance-display">
                    💰 TOTAL EARNINGS
                </div>
                """, unsafe_allow_html=True)
                st.metric("Current Balance", f"${admin['total_earnings']:.2f}", 
                         delta=f"+${admin['daily_earnings']:.2f} today")
            
            with col2:
                st.markdown("""
                <div class="balance-display">
                    📊 NETWORK STATS
                </div>
                """, unsafe_allow_html=True)
                st.metric("Total Users", admin['total_users'])
                st.metric("Active Now", admin['active_users'])
                st.metric("Data Transferred", f"{admin['data_transferred']:.2f} GB")
            
            with col3:
                st.markdown("""
                <div class="balance-display">
                    💳 MONCASH BUSINESS
                </div>
                """, unsafe_allow_html=True)
                st.info(f"Account: {admin['moncash_number']}")
                st.info("Owner: Gesner Deslandes")
            
            # Auto-transfer to MonCash
            st.markdown("---")
            st.subheader("💸 Automated MonCash Transfer")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Pending Transactions")
                if admin['transactions']:
                    for t in admin['transactions'][-5:]:
                        st.write(f"• {t['date']}: ${t['amount']} - {t['type']}")
                else:
                    st.write("No pending transactions")
            
            with col2:
                st.markdown("### Quick Actions")
                
                # One-click transfer to MonCash
                if st.button("💰 TRANSFER ALL TO MONCASH NOW", use_container_width=True):
                    amount = admin['total_earnings']
                    if amount > 0:
                        transaction = {
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "amount": amount,
                            "to": admin['moncash_number'],
                            "status": "Completed",
                            "reference": f"TRX{random.randint(10000, 99999)}"
                        }
                        admin['transactions'].append(transaction)
                        admin['withdrawals'].append(transaction)
                        
                        st.success(f"""
                        ✅ TRANSFER COMPLETED!
                        Amount: ${amount:.2f}
                        To MonCash: {admin['moncash_number']}
                        Reference: {transaction['reference']}
                        """)
                        
                        # Reset earnings after transfer
                        admin['total_earnings'] = 0
                        admin['daily_earnings'] = 0
                    else:
                        st.warning("No funds to transfer")
                
                # Set auto-transfer threshold
                threshold = st.number_input("Auto-transfer threshold ($)", min_value=10, value=100)
                if st.button("Enable Auto-Transfer"):
                    if admin['total_earnings'] >= threshold:
                        st.success(f"Auto-transfer triggered! Sending ${admin['total_earnings']:.2f} to MonCash")
            
            # Transaction history
            st.markdown("---")
            st.subheader("📜 Transaction History")
            if admin['withdrawals']:
                df = pd.DataFrame(admin['withdrawals'])
                st.dataframe(df)
            else:
                st.info("No transactions yet")
            
            # Withdrawal to MonCash
            st.markdown("---")
            st.subheader("🏦 Withdraw to MonCash")
            
            withdraw_amount = st.number_input("Withdrawal Amount ($)", min_value=10.0, value=100.0)
            moncash_number = st.text_input("MonCash Number", value=admin['moncash_number'])
            
            if st.button("💳 WITHDRAW TO MONCASH", use_container_width=True):
                if withdraw_amount <= admin['total_earnings']:
                    withdrawal = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "amount": withdraw_amount,
                        "moncash": moncash_number,
                        "status": "Processing",
                        "reference": f"WDR{random.randint(10000, 99999)}"
                    }
                    admin['withdrawals'].append(withdrawal)
                    admin['total_earnings'] -= withdraw_amount
                    
                    st.success(f"""
                    ✅ Withdrawal Initiated!
                    Amount: ${withdraw_amount:.2f}
                    To: {moncash_number}
                    Reference: {withdrawal['reference']}
                    Funds will arrive in 5-10 minutes
                    """)
                else:
                    st.error("Insufficient balance")
            
            # User earnings summary
            st.markdown("---")
            st.subheader("👥 User Earnings Summary")
            user_earnings = []
            for username, user_data in st.session_state.users.items():
                user_earnings.append({
                    "User": username,
                    "Data Shared (GB)": user_data.get('data_shared', 0),
                    "Earnings ($)": user_data.get('earnings', 0),
                    "Status": "Online" if st.session_state.online_users.get(username) else "Offline"
                })
            
            if user_earnings:
                df_users = pd.DataFrame(user_earnings)
                st.dataframe(df_users)
            
            # Network monitoring
            st.markdown("---")
            st.subheader("🌐 Live Network Monitoring")
            
            # Simulate network activity
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Bandwidth Usage", f"{random.randint(50, 200)} Mbps")
            with col2:
                st.metric("Active Connections", random.randint(10, 50))
            with col3:
                st.metric("Revenue/Minute", f"${random.uniform(0.5, 2.0):.2f}")
            
            # Manual trigger for earnings
            if st.button("💰 Simulate User Activity (Add $10)"):
                admin['total_earnings'] += 10
                admin['daily_earnings'] += 10
                st.success("Added $10 to earnings!")
                st.rerun()
                
        else:
            if admin_pass:  # If password entered but wrong
                st.error("🔒 Unauthorized Access - This area is for GlobalSpace Owner Only")
    
    # Rest of the features (Chats, Video Calls, Groups, Live, Notifications)
    elif menu == "💬 Chats":
        st.header("💬 Private Chats")
        
        # Simulate data sharing
        st.session_state.users[st.session_state.username]["data_shared"] += 0.02
        
        # User list for new chat
        st.subheader("👥 Online Users")
        online_users_list = [user for user, online in st.session_state.online_users.items() 
                           if online and user != st.session_state.username]
        
        if online_users_list:
            selected_user = st.selectbox("Start chat with:", online_users_list)
            if st.button("Start Chat"):
                if selected_user not in st.session_state.chats:
                    st.session_state.chats[selected_user] = []
                st.session_state.current_chat = selected_user
        else:
            st.info("No other users online")
        
        # Chat interface
        if 'current_chat' in st.session_state:
            chat_with = st.session_state.current_chat
            st.subheader(f"Chat with @{chat_with}")
            
            # Display chat messages
            chat_history = st.session_state.chats.get(chat_with, [])
            for msg in chat_history:
                if msg['sender'] == st.session_state.username:
                    st.markdown(f"**You:** {msg['text']} *({msg['time']})*")
                else:
                    st.markdown(f"**@{msg['sender']}:** {msg['text']} *({msg['time']})*")
            
            # Send new message
            new_message = st.text_input("Type your message...", key="chat_input")
            if st.button("Send 📤"):
                if new_message:
                    if chat_with not in st.session_state.chats:
                        st.session_state.chats[chat_with] = []
                    
                    st.session_state.chats[chat_with].append({
                        "sender": st.session_state.username,
                        "text": new_message,
                        "time": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.online_users[st.session_state.username] = False
        st.session_state.username = ""
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; padding: 20px;">
    <p>🌐 GlobalInternet Network - Share Internet, Earn Money, Connect Globally</p>
    <p>© 2025 GlobalSpace - Owner: Gesner Deslandes | MonCash: (509)-47385663</p>
</div>
""", unsafe_allow_html=True)
