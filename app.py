import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io
from datetime import date

# =================================================
# AUTH SYSTEM
# =================================================
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "sales": {"password": "sales123", "role": "sales"},
    "dealer": {"password": "dealer123", "role": "dealer"},
    "client": {"password": "client123", "role": "client"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Broker One Finance – LBOP Secure Access")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        user = USERS.get(u)
        if user and user["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.user = u
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

role = st.session_state.role
st.caption(f"Logged in as: {role.upper()}")

# =================================================
# STANDARD FEES (PROGRAM BASELINE)
# =================================================
STANDARD_FEES = {
    "Dealer Fee": 2000,
    "Auction Fee": 1000,
    "Registration Fee": 250,
    "Transport Fee": 1000,
    "Storage Fee": 300,
}

# =================================================
# INPUTS (COMMON)
# =================================================
st.header("LBOP Equity Participation Calculator")

client_name = st.text_input("Client Name")

retail_value = st.number_input(
    "Retail Vehicle Value (Loan Amount Reference)",
    min_value=0.0,
    step=500.0
)

buy_now = st.number_input(
    "Buy Now Price (Vehicle Acquisition Cost)",
    min_value=0.0,
    step=500.0
)

sales_tax = retail_value * 0.07

fees = STANDARD_FEES.copy()
fees["Sales Tax (7%)"] = sales_tax

# =================================================
# ROLE-BASED FEE CONTROL
# =================================================
if role == "admin":
    st.subheader("Editable Standard Fees")
    for k in fees:
        if k != "Sales Tax (7%)":
            fees[k] = st.number_input(k, value=float(fees[k]))

    extra_count = st.number_input("Additional Fees", 0, 5, 0)
    for i in range(extra_count):
        name = st.text_input(f"Additional Fee Name {i+1}")
        amt = st.number_input(f"Amount {i+1}", min_value=0.0)
        if name:
            fees[name] = amt

elif role == "dealer":
    st.subheader("Dealer Fees (Itemized)")
    for k in fees:
        if k != "Sales Tax (7%)":
            fees[k] = st.number_input(k, value=float(fees[k]))

    extra_count = st.number_input("Additional Dealer Fees", 0, 5, 0)
    for i in range(extra_count):
        name = st.text_input(f"Dealer Fee Name {i+1}")
        amt = st.number_input(f"Amount {i+1}", min_value=0.0)
        if name:
            fees[name] = amt

elif role == "client":
    st.subheader("Standard Program Fees (Fixed)")
    for k, v in fees.items():
        st.text(f"{k}: ${v:,.2f}")

# =================================================
# PROGRAM EQUITY (INTERNAL ONLY)
# =================================================
total_deductions = sum(fees.values()) + buy_now
program_equity = max(retail_value - total_deductions, 0)

# =================================================
# PARTICIPATION SLIDING SCALE (BUY NOW BASED)
# =================================================
if buy_now <= 3000:
    participation_pct = 0.60
elif buy_now >= 19000:
    participation_pct = 0.425
else:
    participation_pct = 0.60 - ((buy_now - 3000) / 16000) * (0.60 - 0.425)

participation_pct = min(max(participation_pct, 0.425), 0.60)

equity_payout = program_equity * participation_pct
broker_margin = program_equity - equity_payout

# =================================================
# RESULTS DISPLAY
# =================================================
st.subheader("Equity Participation Results")

st.metric("Equity Participation Percentage", f"{participation_pct * 100:.1f}%")
st.metric("Equity Participation Payout", f"${equity_payout:,.2f}")

if role in ["dealer", "sales"]:
    st.metric("Dealer Remittance to Broker One", f"${broker_margin:,.2f}")

if role == "admin":
    st.metric("Broker One Internal Margin", f"${broker_margin:,.2f}")

# =================================================
# PDF GENERATION
# =================================================
def generate_pdf(title, footer_note=None, signature=None, show_margin=False):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 50, title)

    c.setFont("Helvetica", 11)
    y = h - 100
    c.drawString(40, y, f"Client: {client_name}")
    y -= 18
    c.drawString(40, y, f"Date: {date.today()}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Fee Breakdown")
    y -= 18
    c.setFont("Helvetica", 10)

    for k, v in fees.items():
        c.drawString(50, y, k)
        c.drawRightString(w - 50, y, f"${v:,.2f}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Buy Now Price: ${buy_now:,.2f}")
    y -= 16
    c.drawString(40, y, f"Retail Value Reference: ${retail_value:,.2f}")
    y -= 16
    c.drawString(40, y, f"Equity Participation %: {participation_pct * 100:.1f}%")
    y -= 16
    c.drawString(40, y, f"Equity Participation Payout: ${equity_payout:,.2f}")

    if show_margin:
        y -= 20
        c.drawString(40, y, f"Broker One Internal Margin: ${broker_margin:,.2f}")

    if footer_note:
        y -= 40
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(40, y, footer_note)

    if signature:
        y -= 50
        c.setFont("Helvetica", 10)
        c.drawString(40, y, "Approved By:")
        y -= 16
        c.drawString(40, y, signature)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# =================================================
# PDF DOWNLOADS BY ROLE
# =================================================
st.divider()

if role == "client":
    pdf = generate_pdf(
        "Equity Participation Payout Estimate",
        footer_note="This document is an estimate only. Final payouts may vary based on deal structure and final costs."
    )
    st.download_button("Download Client Estimate PDF", pdf, "client_estimate.pdf")

elif role == "dealer":
    pdf = generate_pdf(
        "Dealer Service Payment Summary"
    )
    st.download_button("Download Dealer PDF", pdf, "dealer_summary.pdf")

elif role == "sales":
    pdf = generate_pdf(
        "Client Participation Summary"
    )
    st.download_button("Download Sales PDF", pdf, "sales_summary.pdf")

elif role == "admin":
    pdf = generate_pdf(
        "Equity Participation Fee Summary",
        signature="Picasso Ali Varner – CEO, Broker One Finance",
        show_margin=True
    )
    st.download_button("Download Internal PDF", pdf, "internal_summary.pdf")
