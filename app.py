import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
from datetime import date

# =========================
# AUTH SYSTEM
# =========================
USERS = {
    "client": {"password": "client123", "role": "client"},
    "sales": {"password": "sales123", "role": "sales"},
    "dealer": {"password": "dealer123", "role": "dealer"},
    "admin": {"password": "admin123", "role": "admin"},
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
            st.experimental_set_query_params()
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

role = st.session_state.role

# =========================
# SLIDING SCALE (FINAL)
# =========================
def equity_percentage(buy_now):
    if buy_now < 3000:
        return 0.60
    elif buy_now < 5000:
        return 0.60
    elif buy_now < 7500:
        return 0.575
    elif buy_now < 10000:
        return 0.55
    elif buy_now < 15000:
        return 0.50
    elif buy_now <= 19000:
        return 0.425
    else:
        return 0.425

# =========================
# STANDARD FEES
# =========================
STANDARD_FEES = {
    "Dealer Fee": 2000,
    "Auction Fee": 1050,
    "Registration Fee": 250,
    "Sales Tax (7%)": None,
    "Transport Fee": 1000,
    "Storage Fee": 300,
}

# =========================
# INPUTS
# =========================
st.title("LBOP Equity Participation Calculator")

client_name = st.text_input("Client Name") if role != "client" else st.text_input("Your Name")

loan_amount = st.number_input("Retail Vehicle Value (Loan Amount Reference)", min_value=0.0, step=500.0)
buy_now = st.number_input("Buy Now Price (Vehicle Acquisition Cost)", min_value=0.0, step=500.0)

sales_tax = loan_amount * 0.07

fees = {
    "Dealer Fee": STANDARD_FEES["Dealer Fee"],
    "Auction Fee": STANDARD_FEES["Auction Fee"],
    "Registration Fee": STANDARD_FEES["Registration Fee"],
    "Sales Tax (7%)": sales_tax,
    "Transport Fee": STANDARD_FEES["Transport Fee"],
    "Storage Fee": STANDARD_FEES["Storage Fee"],
}

additional_fees = {}

if role in ["dealer", "admin"]:
    st.subheader("Additional Fees")
    count = st.number_input("Number of additional fees", 0, 5, 0)
    for i in range(count):
        name = st.text_input(f"Fee Name {i+1}")
        val = st.number_input(f"Fee Amount {i+1}", 0.0)
        if name:
            additional_fees[name] = val

# =========================
# CALCULATIONS
# =========================
total_fees = sum(fees.values()) + sum(additional_fees.values())
equity_value = loan_amount - buy_now - total_fees
equity_value = max(equity_value, 0)

pct = equity_percentage(buy_now)
client_payout = equity_value * pct
dealer_remainder = equity_value - client_payout

# Dealer split
referral = dealer_remainder * 0.60
marketing = dealer_remainder * 0.40

# =========================
# DISPLAY RESULTS
# =========================
st.subheader("Equity Participation Results")
st.metric("Equity Participation Percentage", f"{pct*100:.1f}%")
st.metric("Equity Participation Payout", f"${client_payout:,.2f}")

if role in ["dealer", "admin"]:
    st.metric("Dealer Remittance to Broker One", f"${dealer_remainder:,.2f}")
    st.write(f"Referral (60%): ${referral:,.2f}")
    st.write(f"Marketing (40%): ${marketing:,.2f}")

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(title, footer_note):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    y = height - 1 * inch
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, y, title)

    y -= 40
    c.setFont("Helvetica", 11)
    c.drawString(1*inch, y, f"Client: {client_name}")
    y -= 15
    c.drawString(1*inch, y, f"Date: {date.today()}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, y, "Fee Breakdown")
    y -= 20

    c.setFont("Helvetica", 10)
    for k,v in fees.items():
        c.drawString(1*inch, y, k)
        c.drawRightString(width-1*inch, y, f"${v:,.2f}")
        y -= 14

    for k,v in additional_fees.items():
        c.drawString(1*inch, y, k)
        c.drawRightString(width-1*inch, y, f"${v:,.2f}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, y, "Equity Participation")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(1*inch, y, f"Equity Percentage: {pct*100:.1f}%")
    y -= 15
    c.drawString(1*inch, y, f"Payout: ${client_payout:,.2f}")

    y -= 40
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, y, footer_note)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# =========================
# PDF BUTTONS
# =========================
if role == "client":
    st.download_button(
        "Download Client Estimation PDF",
        generate_pdf(
            "Equity Participation Estimation",
            "This document is an estimate only. Final payouts may vary based on deal specifics."
        ),
        "client_estimate.pdf"
    )

if role == "sales":
    st.download_button(
        "Download Sales PDF",
        generate_pdf(
            "Client Participation Summary",
            "Sales-use summary. Subject to final approval."
        ),
        "sales_summary.pdf"
    )

if role == "dealer":
    st.download_button(
        "Download Dealer PDF",
        generate_pdf(
            "Dealer Service Payment Summary",
            "Dealer-facing summary for remittance records."
        ),
        "dealer_summary.pdf"
    )

if role == "admin":
    st.download_button(
        "Download Internal PDF",
        generate_pdf(
            "Internal Equity Participation Summary",
            "Internal Broker One Finance record."
        ),
        "internal_summary.pdf"
    )
