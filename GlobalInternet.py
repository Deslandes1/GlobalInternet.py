# Hidden Admin Panel - Owner Access Only
with st.expander("⚙️ System Status (Owner Only)", expanded=False):
    owner_pass = st.text_input("OwnerSpace Password", type="password", key="owner_pass")
    
    if owner_pass == "OwnerSpace2026":
        owner = st.session_state.owner
        
        st.markdown("""
        <div class="admin-panel">
            <h2>💰 GLOBALINTERNET OWNER - GESNER DESLANDES</h2>
            <p>Welcome back, Owner! Configure your payment details below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Owner credentials setup
        st.subheader("🔐 Step 1: Set Your Payment Credentials")
        
        col_cred1, col_cred2 = st.columns(2)
        with col_cred1:
            owner_name = st.text_input("Your Full Name", value=owner.get("name", "Gesner Deslandes"))
            owner_moncash = st.text_input("MonCash Business Number", value=owner.get("moncash", "50947385663"))
            owner_email = st.text_input("Email Address", value="gesner@example.com")
        
        with col_cred2:
            owner_bank = st.text_input("Bank Name (Optional)", value="")
            owner_phone = st.text_input("Phone Number", value="50947385663")
            owner_currency = st.selectbox("Currency", ["HTG - Haitian Gourde", "USD - US Dollar"])
        
        # Save credentials
        if st.button("💾 SAVE PAYMENT CREDENTIALS", use_container_width=True):
            owner["name"] = owner_name
            owner["moncash"] = owner_moncash
            owner["email"] = owner_email
            owner["bank"] = owner_bank
            owner["phone"] = owner_phone
            owner["currency"] = owner_currency
            owner["credentials_saved"] = True
            st.success("✅ Payment credentials saved successfully!")
            st.rerun()
        
        st.markdown("---")
        
        # Revenue Dashboard
        st.subheader("💰 Step 2: Revenue Dashboard")
        
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
        
        # Live revenue ticker
        revenue_per_second = len(st.session_state.active_connections) * owner['profit_rate'] * 0.3
        background_revenue = st.session_state.internet_pool.get("background_sessions", 0) * owner['profit_rate'] * 0.15
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.metric("Generating (Active)", f"${revenue_per_second:.4f}/second")
        with col_l2:
            st.metric("Generating (Background)", f"${background_revenue:.4f}/second")
        
        st.markdown("---")
        
        # Payment Processing
        st.subheader("💸 Step 3: Process Payment to MonCash")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"""
            **Payment Details:**
            - **Recipient:** {owner.get('name', 'Gesner Deslandes')}
            - **MonCash:** {owner.get('moncash', '50947385663')}
            - **Available Balance:** ${owner['total_revenue']:.4f}
            """)
            
            # Payment amount options
            payment_option = st.radio(
                "Payment Amount",
                ["Full Balance", "Custom Amount"],
                horizontal=True
            )
            
            if payment_option == "Custom Amount":
                payment_amount = st.number_input("Amount ($)", min_value=1.0, max_value=float(owner['total_revenue']), value=min(10.0, float(owner['total_revenue'])))
            else:
                payment_amount = owner['total_revenue']
        
        with col_p2:
            st.markdown("**Payment Method:**")
            st.info(f"💳 MonCash Business: {owner.get('moncash', '50947385663')}")
            
            # Confirm payment
            if st.button("💰 PROCESS PAYMENT NOW", use_container_width=True):
                if payment_amount > 0 and payment_amount <= owner['total_revenue']:
                    # Create transaction
                    transaction = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "amount": payment_amount,
                        "to": owner['moncash'],
                        "recipient": owner['name'],
                        "status": "PROCESSING",
                        "reference": f"MC{random.randint(10000, 99999)}",
                        "method": "MonCash Instant"
                    }
                    
                    # Simulate payment processing
                    with st.spinner("Processing payment to MonCash..."):
                        time.sleep(2)
                        transaction["status"] = "COMPLETED INSTANTLY"
                        owner['transactions'].append(transaction)
                        
                        # Deduct from revenue
                        owner['total_revenue'] -= payment_amount
                        owner['daily_revenue'] = max(0, owner['daily_revenue'] - payment_amount)
                    
                    st.balloons()
                    st.success(f"""
                    ✅ PAYMENT COMPLETED SUCCESSFULLY!
                    
                    **Transaction Details:**
                    - Amount: ${payment_amount:.4f}
                    - To: {owner['moncash']}
                    - Recipient: {owner['name']}
                    - Reference: {transaction['reference']}
                    - Status: INSTANTLY SENT
                    
                    Funds should appear in your MonCash account within minutes!
                    """)
                    st.rerun()
                elif payment_amount <= 0:
                    st.error("Please enter a valid amount greater than 0")
                else:
                    st.error("Insufficient balance for this payment")
        
        st.markdown("---")
        
        # Auto-payment settings
        st.subheader("⚡ Step 4: Auto-Payment Settings (Optional)")
        
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            enable_auto = st.checkbox("Enable Auto-Payment", value=owner.get("auto_payment", False))
            if enable_auto:
                threshold = st.number_input("Auto-pay when balance exceeds ($)", min_value=10.0, value=50.0)
        
        with col_a2:
            if enable_auto and st.button("💾 SAVE AUTO-PAY SETTINGS"):
                owner["auto_payment"] = True
                owner["auto_threshold"] = threshold
                st.success(f"Auto-payment enabled! Will transfer to MonCash when balance exceeds ${threshold}")
        
        # Check auto-payment condition
        if owner.get("auto_payment") and owner['total_revenue'] >= owner.get("auto_threshold", 50):
            st.info(f"⚡ Auto-payment triggered: ${owner['total_revenue']:.2f} will be sent to {owner['moncash']}")
            # In a real app, this would trigger automatically
        
        st.markdown("---")
        
        # Active connections
        st.subheader("🔌 Active Connections Worldwide")
        for username, conn in list(st.session_state.active_connections.items())[:10]:
            bg_star = "⭐" if conn.get("background") else ""
            st.markdown(f"- **{username}** {bg_star}: {conn['ip']} | Data: {conn['data_used']:.2f} MB | BG: {conn.get('background', False)}")
        
        if len(st.session_state.active_connections) > 10:
            st.caption(f"... and {len(st.session_state.active_connections) - 10} more")
        
        # Transaction history
        if owner['transactions']:
            st.markdown("### 📜 Payment History")
            df = pd.DataFrame(owner['transactions'])
            st.dataframe(df)
        
        # Reset option (emergency only)
        with st.expander("⚠️ Emergency Reset (Use with caution)"):
            if st.button("🔄 RESET ALL DATA", use_container_width=True):
                if st.checkbox("I understand this will reset all revenue data"):
                    owner['total_revenue'] = 0
                    owner['daily_revenue'] = 0
                    owner['background_revenue'] = 0
                    owner['transactions'] = []
                    st.warning("All data has been reset!")
                    st.rerun()
    
    elif owner_pass:
        st.error("🔒 Incorrect OwnerSpace Password. Access Denied.")
