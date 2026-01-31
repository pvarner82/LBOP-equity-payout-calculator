import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from datetime import date
import io

# =========================================================
# AUTH
# =========================================================
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
            st.experimental_rerun()
        else:
            st.error("Invalid login")
    st.stop()

role = st.session_state.role
st.caption(f"Logged in as **{role.upper()}**")

# =========================================================
# COMMON INPUTS
# =========================================================
st.header("LBOP Equity Calculator")

loan = st.number_input("Loan Approval Amount", 0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", 0.0, step=100.0)

sales_tax = loan * 0.07

STANDARD_FEES = {
    "Dealer Fee": 2000,
    "Auction Fee": 1000,
    "Registration Fee": 250,
    "Transport Fee": 1000,
    "Partner / Floor Plan Fee": 1100,
    "Storage Fee": 300,
    "Sales Tax (7%)": sales_tax,
}

# =========================================================
# CLIENT VIEW
# =========================================================
if role == "client":
    st.subheader("Client Information")
    client_name = st.text_input("Client Name")

    st.subheader("Standard Fees (Fixed)")
    for k, v in STANDARD_FEES.items():
        st.write(f"{k}: ${v:,.2f}")

    total_deductions = sum(STANDARD_FEES.values())
    equity = loan - total_deductions

    def equity_pct(e):
        if e <= 3000: return 0.60
        if e <= 19000: return 0.661
        return 0.425

    pct = equity_pct(equity)
    payout = equity * pct

    st.markdown(f"### Equity Percentage: **{pct*100:.1f}%**")
    st.markdown(f"### Estimated Client Payout: **${payout:,.2f}**")

# =========================================================
# DEALER VIEW
# =========================================================
if role == "dealer":
    st.subheader("Dealer & Vehicle Information")
    dealer_name = st.text_input("Dealership Name")
    dealer_rep = st.text_input("Dealer Representative")
    client_name = st.text_input("Client Name")
    vehicle = st.text_input("Vehicle (Year Make Model)")
    vin = st.text_input("VIN")

    st.subheader("Dealer Fees")
    dealer_fees = {}
    for k, v in STANDARD_FEES.items():
        dealer_fees[k] = st.number_input(k, value=float(v))

    extra = st.number_input("Additional Dealer Fees", 0, 5, 0)
    for i in range(extra):
        name = st.text_input(f"Additional Fee Name #{i+1}")
        amt = st.number_input(f"Amount #{i+1}", step=50.0)
        dealer_fees[name] = amt

    total_deductions = sum(dealer_fees.values())
    remainder = loan - buy_now - total_deductions
    referral = remainder * 0.60
    marketing = remainder * 0.40

    st.markdown(f"### Total Dealer Costs: ${total_deductions:,.2f}")
    st.markdown(f"### Referral Fee (60%): ${referral:,.2f}")
    st.markdown(f"### Marketing Fee (40%): ${marketing:,.2f}")

# =========================================================
# SALES VIEW (FIXED)
# =========================================================
if role == "sales":
    st.subheader("Client & Vehicle Information")
    client_name = st.text_input("Client Name")
    vehicle = st.text_input("Vehicle (Year Make Model)")
    vin = st.text_input("VIN")
    lender = st.text_input("Credit Union / Lender")

    st.subheader("Standard Fees")
    sales_fees = {}
    for k, v in STANDARD_FEES.items():
        sales_fees[k] = st.number_input(k, value=float(v))

    total_deductions = sum(sales_fees.values())
    equity = loan - total_deductions

    pct = 0.661
    payout = equity * pct

    st.markdown(f"### Equity Percentage: {pct*100:.1f}%")
    st.markdown(f"### Client Participation Payout: ${payout:,.2f}")

# =========================================================
# ADMIN VIEW
# =========================================================
if role == "admin":
    st.subheader("Internal Underwriting")
    client_name = st.text_input("Client Name")
    vehicle = st.text_input("Vehicle")
    vin = st.text_input("VIN")

    admin_fees = {}
    for k, v in STANDARD_FEES.items():
        admin_fees[k] = st.number_input(k, value=float(v))

    extra = st.number_input("Additional Internal Fees", 0, 5, 0)
    for i in range(extra):
        name = st.text_input(f"Internal Fee #{i+1}")
        amt = st.number_input(f"Amount #{i+1}", step=50.0)
        admin_fees[name] = amt

    total_deductions = sum(admin_fees.values())
    equity = loan - total_deductions
    pct = 0.661
    payout = equity * pct

    broker_profit = equity - payout

    st.markdown(f"### Approved Client Payout: ${payout:,.2f}")
    st.markdown(f"### Broker One Profit: ${broker_profit:,.2f}")

# =========================================================
# PDF GENERATION
# =========================================================
def build_pdf(title, sections, footer):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER

    c.setFont("Times-Bold", 20)
    c.drawCentredString(w/2, h-60, title)

    y = h - 120
    c.setFont("Times-Roman", 11)

    for header, rows in sections.items():
        c.setFont("Times-Bold", 13)
        c.drawString(40, y, header)
        y -= 20
        c.setFont("Times-Roman", 11)
        for k, v in rows.items():
            c.drawString(50, y, k)
            c.drawRightString(w-50, y, f"${v:,.2f}" if isinstance(v,(int,float)) else v)
            y -= 15
        y -= 10

    c.setFont("Times-Italic", 9)
    c.drawCentredString(w/2, 40, footer)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

if st.button("Generate PDF"):
    today = date.today().strftime("%B %d, %Y")

    if role == "client":
        pdf = build_pdf(
            "Equity Participation Estimate",
            {"Estimate": {"Loan": loan, "Buy Now": buy_now, "Estimated Payout": payout}},
            "This is an estimate only. Fees and payouts may vary based on final deal terms."
        )

    elif role == "dealer":
        pdf = build_pdf(
            "Dealer Service Payment Summary",
            {"Dealer Fees": dealer_fees},
            f"{dealer_name} – Authorized Representative"
        )

    elif role == "sales":
        pdf = build_pdf(
            "Client Participation Summary",
            {"Payout Summary": {"Client": client_name, "Payout": payout}},
            f"Approved for LBOP participation – {today}"
        )

    else:
        pdf = build_pdf(
            "Internal Equity Participation Fee Summary",
            {"All Fees": admin_fees, "Broker One Profit": {"Profit": broker_profit}},
            "Broker One Finance – Internal Use Only"
        )

    st.download_button("Download PDF", pdf, file_name="LBOP_Summary.pdf")
