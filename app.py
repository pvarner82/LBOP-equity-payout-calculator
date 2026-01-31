import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# =========================
# AUTH
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
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

ROLE_LABEL = {
    "client": "Client Calculator",
    "dealer": "Dealer Calculator",
    "sales": "Internal Sales Calculator",
    "admin": "Internal Admin Calculator",
}

st.title("Broker One Finance")
st.subheader("Lease Buyout Program (LBOP)")
st.caption(ROLE_LABEL[st.session_state.role])

# =========================
# COMMON INPUTS
# =========================
loan = st.number_input("Loan Amount", 0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", 0.0, step=100.0)
sales_tax = loan * 0.07

def sliding_pct(bn):
    if bn <= 3000:
        return 0.60
    if bn >= 19000:
        return 0.425
    return 0.60 - ((bn - 3000) / 16000) * 0.175

# =========================
# STANDARD FEES (DEFAULTS)
# =========================
def fee_field(label, default):
    return st.number_input(label, value=default, step=50.0)

if st.session_state.role in ["admin", "sales"]:
    st.subheader("Standard Fees (Editable)")
    dealer_fee = fee_field("Dealer Fee", 2000.0)
    auction_fee = fee_field("Auction Fee", 1000.0)
    registration_fee = fee_field("Registration Fee", 250.0)
    transport_fee = fee_field("Transport Fee", 500.0)
    partner_fee = fee_field("Partner / Floor Fee", 350.0)
else:
    dealer_fee = 2000.0
    auction_fee = 1000.0
    registration_fee = 250.0
    transport_fee = 500.0
    partner_fee = 350.0

# =========================
# CLIENT
# =========================
if st.session_state.role == "client":
    client_name = st.text_input("Your Name")

    fees = [
        ("Dealer Fee", dealer_fee),
        ("Auction Fee", auction_fee),
        ("Registration Fee", registration_fee),
        ("Transport Fee", transport_fee),
        ("Partner / Floor Fee", partner_fee),
        ("Sales Tax (7%)", sales_tax),
    ]

    total_fees = sum(v for _, v in fees)
    equity = loan - (buy_now + total_fees)
    pct = sliding_pct(buy_now)
    payout = equity * pct

    st.subheader("Standard Program Fees")
    for label, val in fees:
        st.write(f"{label}: ${val:,.2f}")

    st.metric("Equity Percentage", f"{pct*100:.2f}%")
    st.metric("Estimated Equity", f"${equity:,.2f}")
    st.metric("Estimated Cash Payout", f"${payout:,.2f}")

# =========================
# DEALER
# =========================
if st.session_state.role == "dealer":
    st.subheader("Deal Information")
    client_name = st.text_input("Client Name")
    dealership = st.text_input("Dealership Name")
    vehicle = st.text_input("Vehicle (Year / Make / Model)")
    vin = st.text_input("VIN (Optional)")

    st.subheader("Standard Fees")
    fees = [
        ("Dealer Fee", dealer_fee),
        ("Auction Fee", auction_fee),
        ("Registration Fee", registration_fee),
        ("Transport Fee", transport_fee),
        ("Partner / Floor Fee", partner_fee),
        ("Sales Tax (7%)", sales_tax),
    ]
    for f in fees:
        st.write(f"{f[0]}: ${f[1]:,.2f}")

    st.subheader("Additional Dealer Fees")
    extras = []
    n = st.number_input("Number of additional fees", 0, 5, 0)
    for i in range(n):
        name = st.text_input(f"Fee Name #{i+1}")
        val = st.number_input(f"Fee Amount #{i+1}", 0.0)
        extras.append((name, val))

    total_fees = sum(v for _, v in fees) + sum(v for _, v in extras)
    remainder = loan - (buy_now + total_fees)

    st.metric("Remaining After Fees", f"${remainder:,.2f}")
    st.metric("Referral Fee (60%)", f"${remainder*0.60:,.2f}")
    st.metric("Marketing Fee (40%)", f"${remainder*0.40:,.2f}")

# =========================
# INTERNAL
# =========================
if st.session_state.role in ["admin", "sales"]:
    st.subheader("Additional Internal Fees")
    extras = []
    n = st.number_input("Number of additional internal fees", 0, 5, 0)
    for i in range(n):
        name = st.text_input(f"Fee Label #{i+1}")
        val = st.number_input(f"Fee Value #{i+1}", 0.0)
        extras.append((name, val))

    fees = [
        ("Dealer Fee", dealer_fee),
        ("Auction Fee", auction_fee),
        ("Registration Fee", registration_fee),
        ("Transport Fee", transport_fee),
        ("Partner / Floor Fee", partner_fee),
        ("Sales Tax (7%)", sales_tax),
    ] + extras

    total_fees = sum(v for _, v in fees)
    equity = loan - (buy_now + total_fees)
    pct = sliding_pct(buy_now)
    payout = equity * pct
    profit = equity - payout

    st.metric("Equity", f"${equity:,.2f}")
    st.metric("Client Payout", f"${payout:,.2f}")

    if st.session_state.role == "admin":
        st.metric("Broker One Profit", f"${profit:,.2f}")
        if profit < 2000:
            st.error("⚠ Profit below $2,000 floor")

# =========================
# FANCY PDF EXPORT
# =========================
def export_pdf(title, rows):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Broker One Finance</b>", styles["Title"]))
    elements.append(Paragraph("Lease Buyout Program (LBOP)", styles["Normal"]))
    elements.append(Paragraph(title, styles["Heading2"]))
    elements.append(Spacer(1, 12))

    table = Table(rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 40))

    elements.append(Paragraph("Approved By: ____________________________", styles["Normal"]))
    elements.append(Paragraph("CEO Signature", styles["Italic"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

pdf_rows = [["Item", "Amount"]]

if st.session_state.role == "client":
    pdf_rows += [
        ["Loan Amount", f"${loan:,.2f}"],
        ["Buy Now Price", f"${buy_now:,.2f}"],
        ["Equity %", f"{pct*100:.2f}%"],
        ["Equity", f"${equity:,.2f}"],
        ["Cash Payout", f"${payout:,.2f}"],
    ]

elif st.session_state.role == "dealer":
    pdf_rows += [
        ["Remaining After Fees", f"${remainder:,.2f}"],
        ["Referral Fee (60%)", f"${remainder*0.60:,.2f}"],
        ["Marketing Fee (40%)", f"${remainder*0.40:,.2f}"],
    ]

elif st.session_state.role in ["admin", "sales"]:
    pdf_rows += [
        ["Equity", f"${equity:,.2f}"],
        ["Client Payout", f"${payout:,.2f}"],
    ]
    if st.session_state.role == "admin":
        pdf_rows.append(["Broker One Profit", f"${profit:,.2f}"])

st.download_button(
    "Download PDF Summary",
    export_pdf(ROLE_LABEL[st.session_state.role], pdf_rows),
    file_name="BrokerOne_LBOP_Payout_Certificate.pdf",
    mime="application/pdf"
)
