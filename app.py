import streamlit as st
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
    st.title("Broker One Finance – LBOP Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(u)
        if user and user["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================
# ROLE LABELS
# =========================
ROLE_LABEL = {
    "admin": "Internal Admin Calculator",
    "sales": "Internal Sales Calculator",
    "dealer": "Dealer Calculator",
    "client": "Client Calculator",
}

st.title("Broker One Finance")
st.subheader("Lease Buyout Program (LBOP)")
st.caption(ROLE_LABEL[st.session_state.role])

# =========================
# COMMON INPUTS
# =========================
loan = st.number_input("Loan Amount", min_value=0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", min_value=0.0, step=100.0)

# =========================
# FIXED BASE FEES
# =========================
dealer_fee = 2000.0
auction_fee = 1000.0
registration_fee = 250.0
transport_fee = 500.0
partner_fee = 350.0
sales_tax = loan * 0.07

# =========================
# CLIENT VERSION
# =========================
if st.session_state.role == "client":
    client_name = st.text_input("Your Name")

    total_fees = (
        dealer_fee
        + auction_fee
        + registration_fee
        + transport_fee
        + partner_fee
        + sales_tax
    )

    equity = loan - (buy_now + total_fees)

    if buy_now <= 3000:
        pct = 0.60
    elif buy_now >= 19000:
        pct = 0.425
    else:
        pct = 0.60 - ((buy_now - 3000) / 16000) * 0.175

    payout = equity * pct

    st.subheader("Estimated Results")
    st.metric("Estimated Equity", f"${equity:,.2f}")
    st.metric("Estimated Cash Payout", f"${payout:,.2f}")

# =========================
# DEALER VERSION
# =========================
if st.session_state.role == "dealer":
    st.subheader("Deal Information")

    client_name = st.text_input("Client Name")
    dealership_name = st.text_input("Dealership Name")
    lender = st.text_input("Lender / Credit Union")

    vehicle_year = st.text_input("Vehicle Year")
    vehicle_make = st.text_input("Vehicle Make")
    vehicle_model = st.text_input("Vehicle Model")
    vin = st.text_input("VIN (Optional)")

    st.subheader("Dealer Fees")
    dealer_fees = dealer_fee + auction_fee + registration_fee + transport_fee

    extra_fees = []
    fee_count = st.number_input("Number of additional dealer fees", 0, 5, 0)

    for i in range(fee_count):
        title = st.text_input(f"Fee Name #{i+1}")
        amount = st.number_input(f"Fee Amount #{i+1}", min_value=0.0)
        extra_fees.append(amount)

    total_dealer_fees = dealer_fees + sum(extra_fees) + sales_tax + partner_fee
    remainder = loan - (buy_now + total_dealer_fees)

    referral_fee = remainder * 0.60
    marketing_fee = remainder * 0.40

    st.subheader("Dealer Remittance Summary")
    st.metric("Remaining Balance After Fees", f"${remainder:,.2f}")
    st.metric("Referral Fee (60%)", f"${referral_fee:,.2f}")
    st.metric("Marketing Fee (40%)", f"${marketing_fee:,.2f}")

# =========================
# INTERNAL VERSION
# =========================
if st.session_state.role in ["admin", "sales"]:
    st.subheader("Internal Deal Info")

    client_name = st.text_input("Client Name")
    dealership_name = st.text_input("Dealership Name")

    extra_fees = []
    count = st.number_input("Additional Internal Fees", 0, 5, 0)

    for i in range(count):
        label = st.text_input(f"Fee Label #{i+1}")
        fee_type = st.selectbox(
            f"Fee Type #{i+1}",
            ["Flat", "% of Loan", "% of Buy Now"]
        )
        value = st.number_input(f"Fee Value #{i+1}", min_value=0.0)

        if fee_type == "Flat":
            extra_fees.append(value)
        elif fee_type == "% of Loan":
            extra_fees.append(loan * value / 100)
        else:
            extra_fees.append(buy_now * value / 100)

    total_fees = (
        dealer_fee
        + auction_fee
        + registration_fee
        + transport_fee
        + partner_fee
        + sales_tax
        + sum(extra_fees)
    )

    equity = loan - (buy_now + total_fees)

    if buy_now <= 3000:
        pct = 0.60
    elif buy_now >= 19000:
        pct = 0.425
    else:
        pct = 0.60 - ((buy_now - 3000) / 16000) * 0.175

    payout = equity * pct
    profit = equity - payout

    st.subheader("Internal Results")
    st.metric("Equity", f"${equity:,.2f}")
    st.metric("Client Payout", f"${payout:,.2f}")
    st.metric("Broker One Profit", f"${profit:,.2f}")

    if profit < 2000:
        st.error("⚠ Profit below $2,000 floor")

# =========================
# PDF EXPORT
# =========================
def export_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    t = c.beginText(40, 750)

    t.textLine("Broker One Finance")
    t.textLine("Lease Buyout Program (LBOP)")
    t.textLine(ROLE_LABEL[st.session_state.role])
    t.textLine("")
    t.textLine(f"Client Name: {client_name}")

    c.drawText(t)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

st.download_button(
    "Download PDF Summary",
    export_pdf(),
    file_name="BrokerOne_LBOP_Summary.pdf",
    mime="application/pdf"
)
