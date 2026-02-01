import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io
from datetime import date

# =====================================================
# AUTH
# =====================================================
USERS = {
    "client": {"password": "client123", "role": "client"},
    "sales": {"password": "sales123", "role": "sales"},
    "dealer": {"password": "dealer123", "role": "dealer"},
    "admin": {"password": "admin123", "role": "admin"},
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
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

role = st.session_state.role
st.caption(f"Logged in as: {role.upper()}")

# =====================================================
# SLIDING SCALE (SMOOTH)
# =====================================================
def calculate_equity_percentage(buy_now):
    MIN_BUY = 3000
    MAX_BUY = 19000
    MAX_PCT = 0.60
    MIN_PCT = 0.425

    if buy_now <= MIN_BUY:
        return MAX_PCT
    if buy_now >= MAX_BUY:
        return MIN_PCT

    slope = (MAX_PCT - MIN_PCT) / (MAX_BUY - MIN_BUY)
    pct = MAX_PCT - (buy_now - MIN_BUY) * slope
    return round(pct, 4)

# =====================================================
# INPUTS
# =====================================================
st.title("LBOP Equity Participation Calculator")

client_name = st.text_input("Client Name")
vehicle_value = st.number_input(
    "Retail Vehicle Value (Loan Amount Reference)",
    min_value=0.0,
    step=500.0
)
buy_now = st.number_input(
    "Buy Now Price (Vehicle Acquisition Cost)",
    min_value=0.0,
    step=500.0
)

lender_name = ""
if role in ["sales", "dealer"]:
    lender_name = st.text_input("Lender / Credit Union Name")

# =====================================================
# TAXES (EXPLICIT & VISIBLE)
# =====================================================
STANDARD_TAX_PCT = 0.07
standard_tax_amount = vehicle_value * STANDARD_TAX_PCT

additional_tax_pct = 0.0
if role in ["sales", "dealer", "admin"]:
    additional_tax_pct = st.number_input(
        "Additional Tax (%)",
        min_value=0.0,
        step=0.1
    ) / 100

additional_tax_amount = vehicle_value * additional_tax_pct

# =====================================================
# STANDARD FEES (ORGANIZED & CONSISTENT)
# =====================================================
fees = {
    "Dealer Fee": 2000.0,
    "Auction Fee": 1050.0,
    "Registration Fee": 250.0,
    "Standard Sales Tax (7%)": standard_tax_amount,
    "Additional Sales Tax": additional_tax_amount,
    "Transport Fee": 1000.0,
    "Storage Fee": 300.0,
}

# =====================================================
# FEE CONTROLS
# =====================================================
additional_fees = {}

if role in ["admin", "sales", "dealer"]:
    st.subheader("Standard Fees")
    for k in fees:
        if k not in ["Standard Sales Tax (7%)", "Additional Sales Tax"]:
            fees[k] = st.number_input(k, value=float(fees[k]))

    st.subheader("Additional Fees")
    count = st.number_input("Number of additional fees", 0, 10, 0)
    for i in range(count):
        name = st.text_input(f"Fee Name {i+1}")
        amt = st.number_input(f"Fee Amount {i+1}", min_value=0.0)
        if name:
            additional_fees[name] = amt

if role == "client":
    st.subheader("Standard Program Fees (Fixed)")
    for k, v in fees.items():
        if v > 0:
            st.text(f"{k}: ${v:,.2f}")

# =====================================================
# CALCULATIONS
# =====================================================
total_fees = sum(fees.values()) + sum(additional_fees.values())
equity_value = max(vehicle_value - buy_now - total_fees, 0)

equity_pct = calculate_equity_percentage(buy_now)
client_payout = equity_value * equity_pct
broker_remainder = equity_value - client_payout

referral_fee = broker_remainder * 0.60
marketing_fee = broker_remainder * 0.40

# =====================================================
# RESULTS
# =====================================================
st.subheader("Results")

if role != "dealer":
    st.metric("Equity Participation Percentage", f"{equity_pct*100:.2f}%")
    st.metric("Equity Participation Payout", f"${client_payout:,.2f}")

if role == "dealer":
    st.metric("Remaining Equity After Fees", f"${broker_remainder:,.2f}")
    st.write(f"Referral (60%): ${referral_fee:,.2f}")
    st.write(f"Marketing (40%): ${marketing_fee:,.2f}")

if role == "admin":
    st.metric("Broker One Internal Margin", f"${broker_remainder:,.2f}")

# =====================================================
# PDF GENERATOR
# =====================================================
def generate_pdf(title, footer=None, show_broker=False, dealer_split=False, signature=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER

    y = h - inch
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, y, title)

    y -= 40
    c.setFont("Helvetica", 11)
    c.drawString(inch, y, f"Client: {client_name}")
    y -= 16
    c.drawString(inch, y, f"Date: {date.today()}")

    if lender_name:
        y -= 16
        c.drawString(inch, y, f"Lender: {lender_name}")

    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(inch, y, "Fee Breakdown")
    y -= 18
    c.setFont("Helvetica", 10)

    for k, v in fees.items():
        if v > 0:
            c.drawString(inch, y, k)
            c.drawRightString(w-inch, y, f"${v:,.2f}")
            y -= 14

    for k, v in additional_fees.items():
        c.drawString(inch, y, k)
        c.drawRightString(w-inch, y, f"${v:,.2f}")
        y -= 14

    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inch, y, f"Buy Now Price: ${buy_now:,.2f}")
    y -= 16
    c.drawString(inch, y, f"Retail Vehicle Value: ${vehicle_value:,.2f}")

    if not dealer_split:
        y -= 20
        c.drawString(inch, y, f"Equity Participation %: {equity_pct*100:.2f}%")
        y -= 16
        c.drawString(inch, y, f"Equity Participation Payout: ${client_payout:,.2f}")

    if dealer_split:
        y -= 20
        c.drawString(inch, y, f"Referral (60%): ${referral_fee:,.2f}")
        y -= 16
        c.drawString(inch, y, f"Marketing (40%): ${marketing_fee:,.2f}")

    if show_broker:
        y -= 20
        c.drawString(inch, y, f"Broker One Internal Margin: ${broker_remainder:,.2f}")

    if footer:
        y -= 40
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(w/2, y, footer)

    if signature:
        y -= 50
        c.setFont("Helvetica", 10)
        c.drawString(inch, y, "Authorized Signature:")
        y -= 18
        c.drawString(inch, y, signature)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# =====================================================
# PDF DOWNLOADS
# =====================================================
st.divider()

if role == "client":
    st.download_button(
        "Download Client Estimation PDF",
        generate_pdf(
            "Equity Participation Estimation",
            footer="This document is an estimate only. Final figures may vary based on deal specifics."
        ),
        "client_estimate.pdf"
    )

elif role == "sales":
    st.download_button(
        "Download Sales PDF",
        generate_pdf("Client Participation Summary"),
        "sales_summary.pdf"
    )

elif role == "dealer":
    st.download_button(
        "Download Dealer PDF",
        generate_pdf(
            "Dealer Service Payment Summary",
            dealer_split=True,
            signature="Authorized Dealership Representative"
        ),
        "dealer_summary.pdf"
    )

elif role == "admin":
    st.download_button(
        "Download Internal PDF",
        generate_pdf(
            "Equity Participation Fee Summary",
            show_broker=True,
            signature="Picasso Ali Varner – CEO, Broker One Finance"
        ),
        "internal_summary.pdf"
    )
