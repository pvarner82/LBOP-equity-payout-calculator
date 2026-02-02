import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import date
import io
import math

# =========================
# AUTH
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
    st.title("Broker One Finance – LBOP Secure Access")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = USERS[u]["role"]
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

ROLE = st.session_state.role

# =========================
# SLIDING SCALE v2 (TUNED)
# =========================
ANCHORS = [
    (3000, 60.0),
    (5000, 58.0),
    (7000, 56.5),
    (9000, 55.0),
    (11000, 52.5),
    (13000, 50.0),
    (15000, 47.5),
    (17000, 45.0),
    (19000, 42.5),
]

def equity_percentage(buy_now):
    if buy_now <= 3000:
        return 60.0
    if buy_now >= 19000:
        return 42.5

    for i in range(len(ANCHORS) - 1):
        low_price, low_pct = ANCHORS[i]
        high_price, high_pct = ANCHORS[i + 1]

        if low_price <= buy_now <= high_price:
            position = (buy_now - low_price) / (high_price - low_price)
            pct = low_pct - position * (low_pct - high_pct)
            return math.floor(pct * 10) / 10  # truncate to 1 decimal

# =========================
# UI INPUTS
# =========================
st.title("LBOP Equity Participation Calculator")
st.caption(f"Role: {ROLE.upper()}")

client_name = st.text_input("Client Name")

vehicle = ""
lender = ""
dealer_name = ""

if ROLE != "client":
    vehicle = st.text_input("Vehicle (Year / Make / Model)")
    lender = st.text_input("Lender / Credit Union")

if ROLE in ["dealer", "admin"]:
    dealer_name = st.text_input("Dealership Name")

retail_value = st.number_input("Retail Vehicle Value (Loan Reference)", min_value=0.0)
buy_now = st.number_input("Buy Now Price (Vehicle Acquisition)", min_value=0.0)

# =========================
# STANDARD FEES
# =========================
st.subheader("Standard Fees")

dealer_fee = st.number_input("Dealer Fee", value=2000.0)
auction_fee = st.number_input("Auction Fee", value=1050.0)
registration_fee = st.number_input("Registration Fee", value=250.0)
transport_fee = st.number_input("Transport Fee", value=1000.0)
storage_fee = st.number_input("Storage Fee", value=300.0)

partner_fee = buy_now * 0.10
st.text(f"Partner / Floor Plan Fee (10% of Buy Now): ${partner_fee:,.2f}")

sales_tax = retail_value * 0.07
st.text(f"Sales Tax (7%): ${sales_tax:,.2f}")

additional_tax_pct = st.number_input("Additional Tax (%)", value=0.0)
additional_tax = retail_value * (additional_tax_pct / 100)

# =========================
# ADDITIONAL FEES
# =========================
additional_fees = {}
if ROLE != "client":
    count = st.number_input("Number of Additional Fees", 0, 10, 0)
    for i in range(count):
        name = st.text_input(f"Fee Name {i+1}")
        amt = st.number_input(f"Fee Amount {i+1}", min_value=0.0)
        if name:
            additional_fees[name] = amt

# =========================
# CALCULATIONS
# =========================
fees = {
    "Dealer Fee": dealer_fee,
    "Auction Fee": auction_fee,
    "Registration Fee": registration_fee,
    "Transport Fee": transport_fee,
    "Storage Fee": storage_fee,
    "Partner / Floor Plan Fee (10%)": partner_fee,
    "Sales Tax (7%)": sales_tax,
    "Additional Tax": additional_tax,
}
fees.update(additional_fees)

total_fees = sum(fees.values())
equity_pool = retail_value - buy_now - total_fees
equity_pct = equity_percentage(buy_now)
client_payout = equity_pool * (equity_pct / 100)

dealer_remaining = equity_pool - client_payout
referral_fee = dealer_remaining * 0.60
marketing_fee = dealer_remaining * 0.40

# =========================
# RESULTS
# =========================
st.subheader("Equity Results")
st.metric("Equity Participation %", f"{equity_pct}%")
st.metric("Client Equity Payout", f"${client_payout:,.2f}")

if ROLE in ["dealer", "admin"]:
    st.metric("Remaining Equity After Client Payout", f"${dealer_remaining:,.2f}")

# =========================
# PDF BUILDER
# =========================
def build_pdf(title, header, fees, results, footer="", signature=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    def make_table(data):
        t = Table(data, colWidths=[280, 200])
        t.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke)
        ]))
        return t

    story.append(make_table([["Field", "Value"]] + list(header.items())))
    story.append(Spacer(1, 14))
    story.append(make_table([["Fee", "Amount"]] + [(k, f"${v:,.2f}") for k,v in fees.items()]))
    story.append(Spacer(1, 14))
    story.append(make_table([["Metric", "Value"]] + list(results.items())))

    if footer:
        story.append(Spacer(1, 18))
        story.append(Paragraph(footer, styles["Italic"]))

    if signature:
        story.append(Spacer(1, 36))
        story.append(Paragraph(signature, styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return buf

# =========================
# PDF DOWNLOAD
# =========================
if st.button("Download PDF"):
    today = date.today().strftime("%B %d, %Y")

    if ROLE == "client":
        pdf = build_pdf(
            "Equity Participation Estimate",
            {"Client": client_name, "Date": today},
            fees,
            {
                "Total Equity Pool": f"${equity_pool:,.2f}",
                "Equity %": f"{equity_pct}%",
                "Estimated Client Payout": f"${client_payout:,.2f}",
            },
            footer="This document is an estimate only. Final figures may vary."
        )

    elif ROLE == "sales":
        pdf = build_pdf(
            "Client Participation Summary",
            {"Client": client_name, "Vehicle": vehicle, "Lender": lender},
            fees,
            {
                "Total Equity Pool": f"${equity_pool:,.2f}",
                "Equity %": f"{equity_pct}%",
                "Client Payout": f"${client_payout:,.2f}",
            }
        )

    elif ROLE == "dealer":
        pdf = build_pdf(
            "Dealer Service Payment Summary",
            {"Client": client_name, "Dealer": dealer_name},
            fees,
            {
                "Referral Fee (60%)": f"${referral_fee:,.2f}",
                "Marketing Fee (40%)": f"${marketing_fee:,.2f}",
            },
            signature=f"Authorized by {dealer_name}"
        )

    else:
        pdf = build_pdf(
            "Equity Participation Fee Summary",
            {"Client": client_name, "Date": today},
            fees,
            {
                "Total Equity Pool": f"${equity_pool:,.2f}",
                "Client Payout": f"${client_payout:,.2f}",
                "Broker One Retained": f"${dealer_remaining:,.2f}",
            },
            signature="Approved by Broker One Finance – CEO"
        )

    st.download_button("Download PDF File", pdf, "lbop_summary.pdf")
