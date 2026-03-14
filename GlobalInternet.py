import streamlit as st
import pandas as pd
import plotly.express as px
from moncash import Moncash, environment

# Initialize MonCash with your credentials
gateway = Moncash(
    client_id="1a938096ed21b2854071101fc05ea428",  # Your Client ID
    client_secret="WC0SjOxywUguKbbwFgDpRoaj0MqiQQcwHF-dFQJisxwM0gnYlSL0OdoRqVqU8DTJ",  # Your Client Secret
    environment=environment.Sandbox  # Use Sandbox for testing first
)

st.set_page_config(page_title="MonCash Payment App", layout="wide")

st.title("💰 MonCash Payment Integration")
st.write(f"Welcome **Gesner Deslandes** (CIN: 1248795849)")

# Initialize session state for balance
if 'balance' not in st.session_state:
    st.session_state.balance = 0

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Make a Payment")
    amount = st.number_input("Amount (HTG)", min_value=10, max_value=10000, value=100, step=10)
    
    if st.button("💳 Pay with MonCash"):
        try:
            # Create payment
            order_id = f"ORDER_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            payment = gateway.payment.create(
                amount=int(amount),
                reference=order_id
            )
            
            st.success("✅ Payment link created!")
            st.markdown(f"[Click here to complete payment]({payment.redirect_uri})")
            st.info(f"Order Reference: {order_id}")
            
        except Exception as e:
            st.error(f"Payment failed: {str(e)}")

with col2:
    st.subheader("Your Balance")
    st.metric("Current Balance", f"{st.session_state.balance} HTG")
    
    # Check payment status (you would normally get this via webhook)
    st.subheader("Recent Transactions")
    st.write("Coming soon...")

st.sidebar.header("Settings")
st.sidebar.info(f"""
**Merchant Info:**
- Name: Gesner Deslandes
- Status: Sandbox Mode
- CIN: 1248795849
""")
