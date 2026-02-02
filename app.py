import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import date

# ----------------------------
# AUTH
# ----------------------------
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
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = USERS[u]["role"]
            st.experimental_rerun()
        else:
            st.error("Invalid login")
    st.stop()

ROLE = st.session_state.role

# ----------------------------
# SLIDING SCALE (CONTINUOUS)
# Buy Now → Equity %
# 3,000 → 42.5%
# 19,000 → 60%
# ----------------------------
def equity_percentage(buy_now):
    min_buy, max_buy = 3000, 19000
    min_pct, max_pct = 42.5, 60.0
    buy_now = max(min_buy, min(max_buy, buy_now))
    return round(
        min_pct + (buy_now - min_buy) * (max_pct - min_pct) / (max_buy - min_buy),
        2
    )

# ----------------------------
# STANDARD FEES
# ----------------------------
def standard_fees(buy_now):
    return {
        "Dealer Fee": 2000,
        "Auction Fee": 1050,
        "Registration Fee": 250,
        "Transport Fee": 1000,
        "Storage Fee": 300,
        "Partner / Floor Plan Fee (10%)": buy_now * 0.10,
    }

# ----------------------------
# PDF BUILDER
# ----------------------------
def build_pdf(title, header_data, fee_data, equity_data, footer_note="", signature=None):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    table_data = [[k, v] for k, v in header_data.items()]
    table = Table(table_data, colWidths=[250, 250])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    fee_table = [["Fee", "Amount ($)"]] + [[k, f"${v:,.2f}"] for k, v in fee_data.items()]
    fee_tbl = Table(fee_table, colWidths=[300, 200])
    fee_tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))
    story.append(fee_tbl)
    story.append(Spacer(1, 20))

    eq_table = [["Metric", "Value"]] + [[k, v] for k, v in equity_data.items()]
    eq_tbl = Table(eq_table, colWidths=[300, 200])
    eq_tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)
    ]))
    story.append(eq_tbl)

    if footer_note:
        story.append(Spacer(1, 20))
        story.append(Paragraph(footer_note, styles["Italic"]))

    if signature:
        story.append(Spacer(1, 40))
        story.append(Paragraph(signature, styles["Normal"]))

    doc.build(story)
    buf.seek(0)
    return buf

# ----------------------------
# COMMON INPUTS
# ----------------------------
st.title("LBOP Equity Participation Calculator")

client_name = st.text_input("Client Name")
vehicle = st.text_input("Vehicle (Year / Make / Model)")
lender = st.text_input("Lender Name") if ROLE != "client" else None

retail_value = st.number_input("Retail Vehicle Value (Loan Reference)", min_value=0.0)
buy_now = st.number_input("Buy Now Price (Vehicle Acquisition)", min_value=0.0)

fees = standard_fees(buy_now)

sales_tax = retail_value * 0.07
fees["Sales Tax (7%)"] = sales_tax

extra_tax_pct = st.number_input("Additional Tax %", min_value=0.0)
fees["Additional Tax"] = retail_value * (extra_tax_pct / 100)

additional_fees = {}
if ROLE in ["admin", "dealer", "sales"]:
    count = st.number_input("Number of Additional Fees", 0, 10, 0)
    for i in range(count):
        name = st.text_input(f"Fee Name {i+1}")
        amt = st.number_input(f"Fee Amount {i+1}", min_value=0.0)
        if name:
            additional_fees[name] = amt

fees.update(additional_fees)

total_fees = sum(fees.values())
gross_equity = retail_value - total_fees
pct = equity_percentage(buy_now)
client_payout = gross_equity * (pct / 100)

# Dealer split
dealer_remit = gross_equity - client_payout
referral = dealer_remit * 0.60
marketing = dealer_remit * 0.40

# ----------------------------
# RESULTS
# ----------------------------
st.subheader("Equity Participation Results")
st.metric("Equity %", f"{pct}%")
st.metric("Client Payout", f"${client_payout:,.2f}")

if ROLE in ["dealer", "admin"]:
    st.metric("Dealer Remittance to Broker One", f"${dealer_remit:,.2f}")

# ----------------------------
# PDF BUTTONS
# ----------------------------
today = date.today().strftime("%B %d, %Y")

if st.button("Download PDF"):
    if ROLE == "client":
        pdf = build_pdf(
            "Equity Participation Estimate",
            {"Client": client_name, "Vehicle": vehicle},
            fees,
            {
                "Equity %": f"{pct}%",
                "Estimated Payout": f"${client_payout:,.2f}"
            },
            footer_note="This document is an estimate only. Final payouts may vary."
        )
    elif ROLE == "sales":
        pdf = build_pdf(
            "Client Participation Summary",
            {"Client": client_name, "Vehicle": vehicle, "Lender": lender},
            fees,
            {
                "Equity %": f"{pct}%",
                "Client Payout": f"${client_payout:,.2f}"
            }
        )
    elif ROLE == "dealer":
        pdf = build_pdf(
            "Dealer Service Payment Summary",
            {"Client": client_name, "Vehicle": vehicle, "Lender": lender},
            fees,
            {
                "Referral (60%)": f"${referral:,.2f}",
                "Marketing (40%)": f"${marketing:,.2f}"
            },
            signature="Authorized Dealer Representative Signature"
        )
    else:
        pdf = build_pdf(
            "Internal Equity Participation Summary",
            {"Client": client_name, "Vehicle": vehicle, "Lender": lender},
            fees,
            {
                "Client Payout": f"${client_payout:,.2f}",
                "Broker One Retained": f"${dealer_remit:,.2f}"
            },
            signature="Approved by CEO – Broker One Finance"
        )

    st.download_button("Download PDF", pdf, file_name="lbop_summary.pdf")
