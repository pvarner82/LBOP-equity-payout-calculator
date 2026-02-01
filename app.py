import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io
from datetime import date

# =================================================
# AUTH
# =================================================
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "sales": {"password": "sales123", "role": "sales"},
    "client": {"password": "client123", "role": "client"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Broker One Finance – LBOP Access")
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
# STANDARD FEES (BASELINE)
# =================================================
STANDARD_FEES = {
    "Dealer Fee": 2000,
    "Auction Fee": 1000,
    "Registration Fee": 250,
    "Transport Fee": 1000,
    "Storage Fee": 300,
}

# =================================================
# INPUTS
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

elif role == "client":
    st.subheader("Standard Program Fees")
    for k, v in fees.items():
        st.text(f"{k}: ${v:,.2f}")

# =================================================
# PROGRAM EQUITY (INTERNAL)
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

# =================================================
# RESULTS
# =================================================
st.subheader("Equity Participation Results")

st.metric(
    "Equity Participation Percentage",
    f"{participation_pct * 100:.1f}%"
)

st.metric(
    "Equity Participation Payout",
    f"${equity_payout:,.2f}"
)

# =================================================
# PDF GENERATION
# =================================================
def generate_pdf(title, disclaimer=False, show_profit=False, signature=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 50, title)

    c.setFont("Helvetica", 11)
    y = h - 100
    c.drawString(40, y, f"Client: {client_name}")
    y -= 20
    c.drawString(40, y, f"Date: {date.today()}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Fee Breakdown")
    y -= 20
    c.setFont("Helvetica", 10)

    for k, v in fees.items():
        c.drawString(50, y, k)
        c.drawRightString(w - 50, y, f"${v:,.2f}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"Equity Participation Payout: ${equity_payout:,.2f}")
    y -= 18
    c.drawString(40, y, f"Participation Percentage: {participation_pct * 100:.1f}%")

    if show_profit:
        broker_profit = program_equity - equity_payout
        y -= 20
        c.drawString(40, y, f"Broker One Internal Margin: ${broker_profit:,.2f}")

    if disclaimer:
        y -= 40
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(
            40,
            y,
            "This document is an estimate only. Final equity participation payouts may vary based on final acquisition costs, dealer fees, and transaction expenses."
        )

    if signature:
        y -= 50
        c.drawString(40, y, "Approved By:")
        y -= 18
        c.drawString(40, y, signature)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# =================================================
# PDF DOWNLOADS
# =================================================
st.divider()

if role == "client":
    pdf = generate_pdf(
        "Equity Participation Payout Estimate",
        disclaimer=True
    )
    st.download_button("Download Estimate PDF", pdf, "client_estimate.pdf")

elif role == "sales":
    pdf = generate_pdf(
        "Client Participation Summary"
    )
    st.download_button("Download Sales PDF", pdf, "sales_summary.pdf")

elif role == "admin":
    pdf = generate_pdf(
        "Equity Participation Fee Summary",
        show_profit=True,
        signature="Picasso Ali Varner – CEO, Broker One Finance"
    )
    st.download_button("Download Internal PDF", pdf, "internal_summary.pdf")
