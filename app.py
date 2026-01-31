import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, HexColor
import io
from datetime import date

# ---------------------------
# AUTH SYSTEM
# ---------------------------
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
        user = USERS.get(u)
        if user and user["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

role = st.session_state.role
st.caption(f"Logged in as **{role.upper()}**")

# ---------------------------
# COMMON INPUTS
# ---------------------------
st.header("LBOP Equity Calculator")

loan = st.number_input("Loan Approval Amount", min_value=0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", min_value=0.0, step=100.0)

sales_tax = loan * 0.07

# Standard fees (baseline)
standard_fees = {
    "Dealer Fee": 2000,
    "Auction Fee": 1000,
    "Registration Fee": 250,
    "Transport Fee": 1000,
    "Partner / Floor Fee": 1100,
    "Storage Fee": 300,
    "Sales Tax (7%)": sales_tax,
}

# ---------------------------
# CLIENT VIEW
# ---------------------------
if role == "client":
    st.subheader("Client Information")
    client_name = st.text_input("Client Name")

    st.subheader("Standard Fees (Fixed)")
    for k, v in standard_fees.items():
        st.write(f"{k}: ${v:,.2f}")

    total_deductions = sum(standard_fees.values())
    equity = loan - total_deductions

    def equity_pct(e):
        if e <= 3000: return 0.60
        if e <= 19000: return 0.661
        return 0.425

    pct = equity_pct(equity)
    payout = equity * pct

    st.markdown(f"### Equity Percentage: **{pct*100:.1f}%**")
    st.markdown(f"### Estimated Client Payout: **${payout:,.2f}**")

# ---------------------------
# DEALER VIEW
# ---------------------------
if role == "dealer":
    st.subheader("Dealer Information")
    dealer_name = st.text_input("Dealership Name")
    client_name = st.text_input("Client Name")
    vehicle = st.text_input("Vehicle (Year Make Model)")
    vin = st.text_input("VIN (optional)")

    st.subheader("Dealer Fees")
    dealer_fees = {}
    for k, v in standard_fees.items():
        dealer_fees[k] = st.number_input(k, value=float(v))

    extra_count = st.number_input("Additional Dealer Fees", 0, 5, 0)
    for i in range(extra_count):
        name = st.text_input(f"Fee Name #{i+1}")
        amt = st.number_input(f"Amount #{i+1}", step=50.0)
        dealer_fees[name] = amt

    total_deductions = sum(dealer_fees.values())
    remainder = loan - buy_now - total_deductions
    referral = remainder * 0.60
    marketing = remainder * 0.40

    st.markdown(f"### Total Dealer Costs: ${total_deductions:,.2f}")
    st.markdown(f"### Broker One Referral: ${referral:,.2f}")
    st.markdown(f"### Broker One Marketing: ${marketing:,.2f}")

# ---------------------------
# SALES VIEW
# ---------------------------
if role == "sales":
    st.subheader("Client & Vehicle Info")
    client_name = st.text_input("Client Name")
    vehicle = st.text_input("Vehicle")
    vin = st.text_input("VIN")
    lender = st.text_input("Lender / Credit Union")

    total_deductions = sum(standard_fees.values())
    equity = loan - total_deductions
    pct = 0.661
    payout = equity * pct

    st.markdown(f"### Verified Payout: ${payout:,.2f} ({pct*100:.1f}%)")

# ---------------------------
# ADMIN VIEW
# ---------------------------
if role == "admin":
    st.subheader("Internal Underwriting")
    client_name = st.text_input("Client Name")
    vehicle = st.text_input("Vehicle")
    vin = st.text_input("VIN")

    admin_fees = {}
    for k, v in standard_fees.items():
        admin_fees[k] = st.number_input(k, value=float(v))

    extra_count = st.number_input("Additional Internal Fees", 0, 5, 0)
    for i in range(extra_count):
        name = st.text_input(f"Internal Fee #{i+1}")
        amt = st.number_input(f"Amount #{i+1}", step=50.0)
        admin_fees[name] = amt

    total_deductions = sum(admin_fees.values())
    equity = loan - total_deductions
    pct = 0.661
    payout = equity * pct

    st.markdown(f"### Internal Approved Payout: ${payout:,.2f}")

# ---------------------------
# PDF GENERATION (ROLE-BASED)
# ---------------------------
def generate_pdf(title, sections, footer):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    c.setFont("Times-Bold", 20)
    c.drawCentredString(width/2, height-60, title)

    y = height - 110
    c.setFont("Times-Roman", 11)

    for header, rows in sections.items():
        c.setFont("Times-Bold", 13)
        c.drawString(40, y, header)
        y -= 20
        c.setFont("Times-Roman", 11)
        for k, v in rows.items():
            c.drawString(50, y, k)
            c.drawRightString(width-50, y, f"${v:,.2f}" if isinstance(v, (int,float)) else v)
            y -= 16
        y -= 10

    c.setFont("Times-Italic", 9)
    c.drawCentredString(width/2, 40, footer)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

if st.button("Generate PDF"):
    if role == "client":
        pdf = generate_pdf(
            "Equity Participation Estimate",
            {
                "Client Summary": {"Client": client_name},
                "Estimate": {"Loan": loan, "Buy Now": buy_now, "Estimated Payout": payout}
            },
            "This document is an estimate only. Final terms may vary."
        )

    elif role == "dealer":
        pdf = generate_pdf(
            "Dealer Service Payment Summary",
            {"Dealer Fees": dealer_fees},
            f"{dealer_name} – Authorized Representative"
        )

    elif role == "sales":
        pdf = generate_pdf(
            "Client Participation Summary",
            {"Payout": {"Verified Payout": payout}},
            "Broker One Finance – LBOP"
        )

    else:
        pdf = generate_pdf(
            "Internal Equity Participation Fee Summary",
            {"All Fees": admin_fees, "Approved Payout": {"Amount": payout}},
            "Broker One Finance – Internal Use Only"
        )

    st.download_button("Download PDF", pdf, file_name="LBOP_Summary.pdf")
