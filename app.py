import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import date
import io

# =====================================================
# AUTH
# =====================================================
USERS = {
    "client": {"password": "client123", "role": "client"},
    "dealer": {"password": "dealer123", "role": "dealer"},
    "sales": {"password": "sales123", "role": "sales"},
    "admin": {"password": "admin123", "role": "admin"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Broker One Finance – LBOP Secure Portal")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = USERS[u]["role"]
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

role = st.session_state.role
st.caption(f"Logged in as **{role.upper()}**")

# =====================================================
# CORE EQUITY ENGINE (LOCKED)
# =====================================================
def calculate_equity_payout(
    equity_value_reference: float,
    fees: dict
):
    """
    Equity is program-determined vehicle value.
    This function enforces the 42.5%–60% participation clamp.
    """

    total_fees = sum(fees.values())
    program_equity = equity_value_reference - total_fees

    # sliding scale example (can be adjusted internally)
    if program_equity <= 3000:
        raw_pct = 0.60
    elif program_equity >= 19000:
        raw_pct = 0.425
    else:
        raw_pct = 0.60 - ((program_equity - 3000) / 16000) * 0.175

    applied_pct = max(0.425, min(raw_pct, 0.60))
    payout = program_equity * applied_pct

    return {
        "program_equity": program_equity,
        "participation_pct": applied_pct,
        "payout": payout,
        "broker_remainder": program_equity - payout
    }

# =====================================================
# STANDARD FEES (BASELINE)
# =====================================================
def get_standard_fees(equity_reference):
    return {
        "Dealer Fee": 2000,
        "Auction Fee": 1053,
        "Registration Fee": 250,
        "Sales Tax (7%)": equity_reference * 0.07,
        "Transport Fee": 1000,
        "Partner / Floor Fee": 1100,
        "Storage Fee": 300,
    }

# =====================================================
# COMMON INPUTS
# =====================================================
st.header("LBOP Equity Participation Calculator")

client_name = st.text_input("Client Name")
vehicle = st.text_input("Vehicle (Year / Make / Model)")
vin = st.text_input("VIN (optional)")
equity_value_reference = st.number_input(
    "Equity Value Reference",
    min_value=0.0,
    step=100.0,
    help="Used as a reference point for determining program equity. Not a loan."
)

# =====================================================
# CLIENT CALCULATOR
# =====================================================
if role == "client":
    fees = get_standard_fees(equity_value_reference)

    st.subheader("Standard Program Fees")
    for k, v in fees.items():
        st.write(f"{k}: ${v:,.2f}")

    result = calculate_equity_payout(equity_value_reference, fees)

    st.metric(
        "Equity Participation Percentage",
        f"{result['participation_pct']*100:.2f}%"
    )
    st.metric(
        "Estimated Equity Participation Payout",
        f"${result['payout']:,.2f}"
    )

    def client_pdf():
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER)
        w, h = LETTER

        y = h - 60
        c.setFont("Times-Bold", 20)
        c.drawCentredString(w/2, y, "Equity Participation Payout Estimate")

        y -= 40
        c.setFont("Times-Roman", 12)
        c.drawString(50, y, f"Client: {client_name}")
        y -= 18
        c.drawString(50, y, f"Vehicle: {vehicle}")
        y -= 18
        c.drawString(50, y, f"VIN: {vin}")

        y -= 30
        c.setFont("Times-Bold", 14)
        c.drawString(50, y, "Program Fees")
        y -= 20

        c.setFont("Times-Roman", 12)
        for k, v in fees.items():
            c.drawString(60, y, k)
            c.drawRightString(w-50, y, f"${v:,.2f}")
            y -= 16

        y -= 20
        c.setFont("Times-Bold", 14)
        c.drawString(50, y, "Estimated Payout")
        y -= 25
        c.setFont("Times-Bold", 18)
        c.drawCentredString(
            w/2,
            y,
            f"${result['payout']:,.2f} ({result['participation_pct']*100:.2f}%)"
        )

        y -= 40
        c.setFont("Times-Italic", 10)
        c.drawCentredString(
            w/2,
            y,
            "This document is an estimate only. Final figures may vary based on deal specifics."
        )

        c.showPage()
        c.save()
        buf.seek(0)
        return buf

    st.download_button(
        "Download Estimate PDF",
        client_pdf(),
        file_name="Equity_Participation_Estimate.pdf",
        mime="application/pdf"
    )

# =====================================================
# DEALER CALCULATOR
# =====================================================
if role == "dealer":
    st.subheader("Dealer Fees")
    fees = get_standard_fees(equity_value_reference)

    for k in list(fees.keys()):
        fees[k] = st.number_input(k, value=float(fees[k]))

    extra_count = st.number_input("Additional Dealer Fees", 0, 5, 0)
    for i in range(extra_count):
        name = st.text_input(f"Fee Name #{i+1}")
        amt = st.number_input(f"Amount #{i+1}", step=50.0)
        if name:
            fees[name] = amt

    result = calculate_equity_payout(equity_value_reference, fees)

    remainder = result["program_equity"]
    referral = remainder * 0.60
    marketing = remainder * 0.40

    st.metric("Total Dealer Deductions", f"${sum(fees.values()):,.2f}")
    st.metric("Referral Fee (60%)", f"${referral:,.2f}")
    st.metric("Marketing Fee (40%)", f"${marketing:,.2f}")

# =====================================================
# SALES CALCULATOR
# =====================================================
if role == "sales":
    fees = get_standard_fees(equity_value_reference)

    st.subheader("Standard Program Fees")
    for k, v in fees.items():
        st.write(f"{k}: ${v:,.2f}")

    result = calculate_equity_payout(equity_value_reference, fees)

    st.metric(
        "Equity Participation Percentage",
        f"{result['participation_pct']*100:.2f}%"
    )
    st.metric(
        "Equity Participation Payout",
        f"${result['payout']:,.2f}"
    )

# =====================================================
# ADMIN CALCULATOR
# =====================================================
if role == "admin":
    st.subheader("Internal Fee Controls")
    fees = get_standard_fees(equity_value_reference)

    for k in list(fees.keys()):
        fees[k] = st.number_input(k, value=float(fees[k]))

    extra = st.number_input("Additional Internal Fees", 0, 5, 0)
    for i in range(extra):
        name = st.text_input(f"Internal Fee #{i+1}")
        amt = st.number_input(f"Amount #{i+1}", step=50.0)
        if name:
            fees[name] = amt

    result = calculate_equity_payout(equity_value_reference, fees)

    st.metric(
        "Client Payout",
        f"${result['payout']:,.2f}"
    )
    st.metric(
        "Broker One Remainder",
        f"${result['broker_remainder']:,.2f}"
    )
