# ============================================================
# LBOP EQUITY PARTICIPATION PLATFORM – FULL APPLICATION
# ============================================================

import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from datetime import datetime
import io

# ------------------------------------------------------------
# APP CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="LBOP Equity Participation Platform",
    layout="centered"
)

# ------------------------------------------------------------
# AUTH SYSTEM
# ------------------------------------------------------------
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

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.role = USERS[username]["role"]
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

role = st.session_state.role

# ------------------------------------------------------------
# SLIDING SCALE (42.5% – 60%)
# ------------------------------------------------------------
def equity_percentage(buy_now):
    if buy_now <= 3000:
        return 0.60
    if buy_now >= 19000:
        return 0.425
    return 0.60 - ((buy_now - 3000) / (19000 - 3000)) * (0.60 - 0.425)

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("LBOP Equity Participation Calculator")
st.caption(f"Role: {role.upper()}")

# ------------------------------------------------------------
# CLIENT / VEHICLE INFO
# ------------------------------------------------------------
client_name = st.text_input("Client Name")

vehicle_desc = ""
vin = ""
lender = ""
dealer_name = ""

if role in ["sales", "dealer", "admin"]:
    vehicle_desc = st.text_input("Vehicle (Year / Make / Model)")
    vin = st.text_input("VIN (optional)")
    lender = st.text_input("Lender / Credit Union")

if role in ["dealer", "admin"]:
    dealer_name = st.text_input("Dealership Name")

# ------------------------------------------------------------
# CORE VALUES
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# STANDARD FEES
# ------------------------------------------------------------
st.header("Standard Fees")

dealer_fee = st.number_input("Dealer Fee", value=2000.0)
auction_fee = st.number_input("Auction Fee", value=1050.0)
registration_fee = st.number_input("Registration Fee", value=250.0)
partner_fee = st.number_input("Partner / Floor Plan Fee", value=1100.0)
transport_fee = st.number_input("Transport Fee", value=1000.0)
storage_fee = st.number_input("Storage Fee", value=300.0)

# ------------------------------------------------------------
# TAXES
# ------------------------------------------------------------
st.subheader("Taxes")

sales_tax_rate = st.number_input(
    "Sales Tax (%)",
    value=7.0,
    step=0.25
)

additional_tax_rate = st.number_input(
    "Additional Tax (%)",
    value=0.0,
    step=0.25
)

sales_tax = retail_value * (sales_tax_rate / 100)
additional_tax = retail_value * (additional_tax_rate / 100)

# ------------------------------------------------------------
# ADDITIONAL FEES
# ------------------------------------------------------------
st.header("Additional Fees")

additional_fees_total = 0.0
additional_fee_count = st.number_input(
    "Number of additional fees",
    min_value=0,
    max_value=10,
    step=1
)

additional_fees = []

for i in range(int(additional_fee_count)):
    label = st.text_input(f"Fee {i+1} Name")
    amount = st.number_input(f"Fee {i+1} Amount", min_value=0.0)
    additional_fees.append((label, amount))
    additional_fees_total += amount

# ------------------------------------------------------------
# CALCULATIONS
# ------------------------------------------------------------
total_fees = (
    dealer_fee +
    auction_fee +
    registration_fee +
    partner_fee +
    transport_fee +
    storage_fee +
    sales_tax +
    additional_tax +
    additional_fees_total
)

gross_equity = retail_value - buy_now - total_fees
equity_pct = equity_percentage(buy_now)
equity_payout = max(gross_equity * equity_pct, 0)

dealer_remittance = gross_equity - equity_payout
referral_fee = dealer_remittance * 0.60
marketing_fee = dealer_remittance * 0.40

# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------
st.header("Equity Participation Results")

st.metric("Equity Participation Percentage", f"{equity_pct*100:.1f}%")
st.metric("Equity Participation Payout", f"${equity_payout:,.2f}")

if role in ["dealer", "admin"]:
    st.metric("Dealer Remittance to Broker One", f"${dealer_remittance:,.2f}")

# ------------------------------------------------------------
# PDF GENERATION HELPERS
# ------------------------------------------------------------
def generate_pdf(title, lines, footer):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    y = height - 1.25 * inch
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, y, title)

    y -= 0.75 * inch
    c.setFont("Helvetica", 10)

    for label, value in lines:
        c.drawString(1.25 * inch, y, label)
        c.drawRightString(width - 1.25 * inch, y, value)
        y -= 0.25 * inch

        if y < 1.5 * inch:
            c.showPage()
            y = height - 1.25 * inch
            c.setFont("Helvetica", 10)

    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, 0.75 * inch, footer)

    c.save()
    buffer.seek(0)
    return buffer

# ------------------------------------------------------------
# PDF DOWNLOADS (ROLE-SPECIFIC)
# ------------------------------------------------------------
today = datetime.now().strftime("%B %d, %Y")

if role == "client":
    pdf = generate_pdf(
        "Equity Participation Estimate",
        [
            ("Client", client_name),
            ("Retail Vehicle Value", f"${retail_value:,.2f}"),
            ("Buy Now Price", f"${buy_now:,.2f}"),
            ("Equity Percentage", f"{equity_pct*100:.1f}%"),
            ("Estimated Payout", f"${equity_payout:,.2f}")
        ],
        "This document is an estimate only. Fees and payouts may vary."
    )
    st.download_button("Download Client Estimate PDF", pdf, "client_estimate.pdf")

elif role == "sales":
    pdf = generate_pdf(
        "Client Participation Summary",
        [
            ("Client", client_name),
            ("Vehicle", vehicle_desc),
            ("Lender", lender),
            ("Equity Percentage", f"{equity_pct*100:.1f}%"),
            ("Equity Payout", f"${equity_payout:,.2f}")
        ],
        f"Prepared {today} – Broker One Finance"
    )
    st.download_button("Download Sales PDF", pdf, "sales_summary.pdf")

elif role == "dealer":
    pdf = generate_pdf(
        "Dealer Service Payment Summary",
        [
            ("Client", client_name),
            ("Dealer", dealer_name),
            ("Equity Payout", f"${equity_payout:,.2f}"),
            ("Referral Fee (60%)", f"${referral_fee:,.2f}"),
            ("Marketing Fee (40%)", f"${marketing_fee:,.2f}")
        ],
        f"Authorized by {dealer_name}"
    )
    st.download_button("Download Dealer PDF", pdf, "dealer_summary.pdf")

elif role == "admin":
    pdf = generate_pdf(
        "Equity Participation Fee Summary",
        [
            ("Client", client_name),
            ("Gross Equity", f"${gross_equity:,.2f}"),
            ("Client Payout", f"${equity_payout:,.2f}"),
            ("Broker One Remittance", f"${dealer_remittance:,.2f}")
        ],
        f"Approved by Broker One Finance – {today}"
    )
    st.download_button("Download Internal PDF", pdf, "internal_summary.pdf")
