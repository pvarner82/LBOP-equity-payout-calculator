import streamlit as st
import pandas as pd
from uuid import uuid4

# -------------------------
# SIMPLE AUTH SYSTEM
# -------------------------
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "sales": {"password": "sales123", "role": "sales"},
    "client": {"password": "client123", "role": "client"},
    "dealer": {"password": "dealer123", "role": "dealer"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Broker One Finance – LBOP Platform Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user = username
            st.experimental_rerun()
        else:
            st.error("Invalid login")
    st.stop()

# -------------------------
# HEADER
# -------------------------
st.title("Broker One Finance – LBOP Equity Platform")
st.caption(f"Logged in as {st.session_state.user} ({st.session_state.role.upper()})")

# -------------------------
# DEAL STORAGE
# -------------------------
if "deals" not in st.session_state:
    st.session_state.deals = []

# -------------------------
# INPUTS
# -------------------------
st.subheader("Deal Inputs")

loan = st.number_input("Loan Amount", min_value=0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", min_value=0.0, step=100.0)
dealer_fee = st.number_input("Dealer Fee", value=2000.0)
auction_fee = st.number_input("Auction Fee", value=1000.0)
registration_fee = st.number_input("Registration Fee", value=250.0)
transport_fee = st.number_input("Transport Fee", value=500.0)
partner_fee = st.number_input("Partner / Floor Fee", value=350.0)

sales_tax = loan * 0.07
st.info(f"Sales Tax (7% of loan): ${sales_tax:,.2f}")

# -------------------------
# ADDITIONAL FEES
# -------------------------
st.subheader("Additional Fees (Internal Only)")
additional_fees = []

if st.session_state.role in ["admin", "sales"]:
    fee_count = st.number_input("Number of additional fees", 0, 5, 0)
    for i in range(fee_count):
        st.markdown(f"**Additional Fee #{i+1}**")
        fee_name = st.text_input("Fee Name", key=f"name{i}")
        fee_type = st.selectbox("Fee Type", ["Flat", "% of Loan", "% of Buy Now"], key=f"type{i}")
        value = st.number_input("Value", min_value=0.0, key=f"value{i}")
        include = st.checkbox("Include in Equity", True, key=f"include{i}")

        if include:
            if fee_type == "Flat":
                additional_fees.append(value)
            elif fee_type == "% of Loan":
                additional_fees.append(loan * (value / 100))
            else:
                additional_fees.append(buy_now * (value / 100))

# -------------------------
# CALCULATIONS
# -------------------------
total_fees = (
    dealer_fee
    + auction_fee
    + registration_fee
    + transport_fee
    + partner_fee
    + sales_tax
    + sum(additional_fees)
)

equity = loan - (buy_now + total_fees)

if buy_now <=
