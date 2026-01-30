import streamlit as st
import pandas as pd
from uuid import uuid4
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io

# =========================
# AUTH SYSTEM
# =========================
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "sales": {"password": "sales123", "role": "sales"},
    "dealer": {"password": "dealer123", "role": "dealer"},
    "client": {"password": "client123", "role": "client"},
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
            st.session_state.user = username
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.stop()

# =========================
# ROLE LABELS
# =========================
ROLE_LABELS = {
    "admin": "Internal Admin Calculator",
    "sales": "Internal Sales Calculator",
    "dealer": "Dealer Calculator",
    "client": "Client Calculator",
}

# =========================
# HEADER
# =========================
st.title("Broker One Finance")
st.subheader("Lease Buyout Program (LBOP)")
st.caption(ROLE_LABELS[st.session_state.role])

# =========================
# DEAL & VEHICLE INFO
# =========================
st.subheader("Deal & Vehicle Information")

client_name = st.text_input("Client Name")
dealership_name = st.text_input("Dealership Name")
lender_name = st.text_input("Credit Union / Lender")

vehicle_year = st.text_input("Vehicle Year")
vehicle_make = st.text_input("Vehicle Make")
vehicle_model = st.text_input("Vehicle Model")
vin = st.text_input("VIN (Optional)")

# =========================
# FINANCIAL INPUTS
# =========================
st.subheader("Financial Inputs")

loan = st.number_input("Loan Approval Amount", min_value=0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", min_value=0.0, step=100.0)

dealer_fee = st.number_input("Dealer Fee", value=2000.0)
auction_fee = st.number_input("Auction Fee", value=1000.0)
registration_fee = st.number_input("Registration Fee", value=250.0)
transport_fee = st.number_input("Transport Fee", value=500.0)
partner_fee = st.number_input("Partner / Floor Fee", value=350.0)

# =========================
# TAX (LOCKED)
# =========================
sales_tax = loan * 0.07
st.info(f"Sales Tax (7% of loan): ${sales_tax:,.2f}")

# =========================
# ADDITIONAL FEES (INTERNAL)
# =========================
additional_fees = []

if st.session_state.role in ["admin", "sales"]:
    st.subheader("Additional Internal Fees")

    fee_count = st.number_input(
        "Number of additional fees",
        min_value=0,
        max_value=5,
        step=1
    )

    for i in range(fee_count):
        st.markdown(f"**Additional Fee #{i + 1}**")

        fee_type = st.selectbox(
            "Fee Type",
            ["Flat", "% of Loan", "% of Buy Now"],
            key=f"fee_type_{i}"
        )

        fee_value = st.number_input(
            "Fee Value",
            min_value=0.0,
            key=f"fee_value_{i}"
        )

        if fee_type == "Flat":
            additional_fees.append(fee_value)
        elif fee_type == "% of Loan":
            additional_fees.append(loan * (fee_value / 100))
        else:
            additional_fees.append(buy_now * (fee_value / 100))

# =========================
# CALCULATIONS
# =========================
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

# Sliding payout scale
if buy_now <= 3000:
    payout_pct = 0.60
elif buy_now >= 19000:
    payout_pct = 0.425
else:
    payout_pct = 0.60 - ((buy_now - 3000) / 16000) * 0.175

client_payout = equity * payout_pct
broker_profit = equity - client_payout

# =========================
# RESULTS
# =========================
st.subheader("Equity Summary")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Equity", f"${equity:,.2f}")
col2.metric("Client %", f"{payout_pct * 100:.2f}%")
col3.metric("Client Payout", f"${client_payout:,.2f}")

if st.session_state.role == "admin":
    col4.metric("Broker One Profit", f"${broker_profit:,.2f}")
    if broker_profit < 2000:
        st.error("⚠ Broker One profit below $2,000 minimum")

# =========================
# DEALER VIEW
# =========================
if st.session_state.role == "dealer":
    st.subheader("Dealer Remittance Breakdown")
    st.write("Marketing Fee (40%)", f"${equity * 0.40:,.2f}")
    st.write("Referral Fee (60%)", f"${equity * 0.60:,.2f}")

# =========================
# PDF EXPORT
# =========================
def generate_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    text = c.beginText(40, 750)

    text.textLine("Broker One Finance")
    text.textLine("Lease Buyout Program (LBOP)")
    text.textLine(ROLE_LABELS[st.session_state.role])
    text.textLine("")

    text.textLine(f"Client Name: {client_name}")
    text.textLine(f"Dealership: {dealership_name}")
    text.textLine(f"Lender: {lender_name}")
    text.textLine("")
    text.textLine(f"Vehicle: {vehicle_year} {vehicle_make} {vehicle_model}")
    text.textLine(f"VIN: {vin}")
    text.textLine("")
    text.textLine(f"Loan Amount: ${loan:,.2f}")
    text.textLine(f"Buy Now Price: ${buy_now:,.2f}")
    text.textLine(f"Total Equity: ${equity:,.2f}")
    text.textLine(f"Client Payout: ${client_payout:,.2f}")

    if st.session_state.role == "admin":
        text.textLine(f"Broker One Profit: ${broker_profit:,.2f}")

    if st.session_state.role == "dealer":
        text.textLine(f"Marketing Fee: ${equity * 0.40:,.2f}")
        text.textLine(f"Referral Fee: ${equity * 0.60:,.2f}")

    c.drawText(text)
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

st.subheader("Export")
pdf_file = generate_pdf()

st.download_button(
    "Download PDF Summary",
    pdf_file,
    file_name="BrokerOne_LBOP_Deal_Summary.pdf",
    mime="application/pdf"
)
