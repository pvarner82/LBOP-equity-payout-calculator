import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io

# =========================
# AUTH
# =========================
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "sales": {"password": "sales123", "role": "sales"},
    "dealer": {"password": "dealer123", "role": "dealer"},
    "client": {"password": "client123", "role": "client"},
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Broker One Finance – LBOP Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = USERS.get(u)
        if user and user["password"] == p:
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

# =========================
# LABELS
# =========================
ROLE_LABEL = {
    "client": "Client Calculator",
    "dealer": "Dealer Calculator",
    "sales": "Internal Sales Calculator",
    "admin": "Internal Admin Calculator",
}

st.title("Broker One Finance")
st.subheader("Lease Buyout Program (LBOP)")
st.caption(ROLE_LABEL[st.session_state.role])

# =========================
# FIXED FEES
# =========================
DEALER_FEE = 2000.0
AUCTION_FEE = 1000.0
REGISTRATION_FEE = 250.0
TRANSPORT_FEE = 500.0
PARTNER_FEE = 350.0

# =========================
# COMMON INPUTS
# =========================
loan = st.number_input("Loan Amount", 0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", 0.0, step=100.0)
sales_tax = loan * 0.07

def sliding_pct(bn):
    if bn <= 3000:
        return 0.60
    if bn >= 19000:
        return 0.425
    return 0.60 - ((bn - 3000) / 16000) * 0.175

# =========================
# CLIENT
# =========================
if st.session_state.role == "client":
    client_name = st.text_input("Your Name")

    st.subheader("Standard Program Fees")
    st.markdown(
        f"""
        Dealer Fee: ${DEALER_FEE:,.2f}  
        Auction Fee: ${AUCTION_FEE:,.2f}  
        Registration Fee: ${REGISTRATION_FEE:,.2f}  
        Transport Fee: ${TRANSPORT_FEE:,.2f}  
        Partner / Floor Fee: ${PARTNER_FEE:,.2f}  
        Sales Tax (7%): ${sales_tax:,.2f}
        """
    )

    total_fees = (
        DEALER_FEE + AUCTION_FEE + REGISTRATION_FEE +
        TRANSPORT_FEE + PARTNER_FEE + sales_tax
    )

    equity = loan - (buy_now + total_fees)
    pct = sliding_pct(buy_now)
    payout = equity * pct

    st.metric("Equity Percentage", f"{pct*100:.2f}%")
    st.metric("Estimated Equity", f"${equity:,.2f}")
    st.metric("Estimated Cash Payout", f"${payout:,.2f}")

# =========================
# DEALER
# =========================
if st.session_state.role == "dealer":
    client_name = st.text_input("Client Name")
    dealership = st.text_input("Dealership Name")
    lender = st.text_input("Lender")
    vehicle = st.text_input("Vehicle (Year / Make / Model)")
    vin = st.text_input("VIN (Optional)")

    st.subheader("Standard Fees (Fixed)")
    st.write(
        f"${DEALER_FEE+AUCTION_FEE+REGISTRATION_FEE+TRANSPORT_FEE+PARTNER_FEE+sales_tax:,.2f}"
    )

    st.subheader("Additional Dealer Fees")
    extra_labels, extra_vals = [], []
    n = st.number_input("Number of additional fees", 0, 5, 0)
    for i in range(n):
        extra_labels.append(st.text_input(f"Fee Name #{i+1}"))
        extra_vals.append(st.number_input(f"Fee Amount #{i+1}", 0.0))

    total_fees = (
        DEALER_FEE + AUCTION_FEE + REGISTRATION_FEE +
        TRANSPORT_FEE + PARTNER_FEE + sales_tax + sum(extra_vals)
    )

    remainder = loan - (buy_now + total_fees)

    st.metric("Remaining After Fees", f"${remainder:,.2f}")
    st.metric("Referral Fee (60%)", f"${remainder*0.60:,.2f}")
    st.metric("Marketing Fee (40%)", f"${remainder*0.40:,.2f}")

# =========================
# INTERNAL (SALES / ADMIN)
# =========================
if st.session_state.role in ["sales", "admin"]:
    st.subheader("Internal Fees")
    labels, vals = [], []
    n = st.number_input("Additional Internal Fees", 0, 5, 0)
    for i in range(n):
        labels.append(st.text_input(f"Fee Label #{i+1}"))
        vals.append(st.number_input(f"Fee Value #{i+1}", 0.0))

    total_fees = (
        DEALER_FEE + AUCTION_FEE + REGISTRATION_FEE +
        TRANSPORT_FEE + PARTNER_FEE + sales_tax + sum(vals)
    )

    equity = loan - (buy_now + total_fees)
    pct = sliding_pct(buy_now)
    payout = equity * pct
    profit = equity - payout

    st.metric("Equity", f"${equity:,.2f}")
    st.metric("Client Payout", f"${payout:,.2f}")

    if st.session_state.role == "admin":
        st.metric("Broker One Profit", f"${profit:,.2f}")
        if profit < 2000:
            st.error("⚠ Profit below $2,000 floor")

# =========================
# PDF EXPORT (ROLE SAFE)
# =========================
def export_pdf():
    b = io.BytesIO()
    c = canvas.Canvas(b, pagesize=LETTER)
    t = c.beginText(40, 750)

    t.textLine("Broker One Finance")
    t.textLine("Lease Buyout Program (LBOP)")
    t.textLine(ROLE_LABEL[st.session_state.role])
    t.textLine("")

    if st.session_state.role == "client":
        t.textLine(f"Client: {client_name}")
        t.textLine(f"Loan: ${loan:,.2f}")
        t.textLine(f"Buy Now: ${buy_now:,.2f}")
        t.textLine(f"Equity %: {pct*100:.2f}%")
        t.textLine(f"Equity: ${equity:,.2f}")
        t.textLine(f"Payout: ${payout:,.2f}")

    if st.session_state.role == "dealer":
        t.textLine(f"Client: {client_name}")
        t.textLine(f"Dealership: {dealership}")
        t.textLine(f"Vehicle: {vehicle}")
        t.textLine(f"VIN: {vin}")
        t.textLine(f"Remaining: ${remainder:,.2f}")
        t.textLine(f"Referral (60%): ${remainder*0.60:,.2f}")
        t.textLine(f"Marketing (40%): ${remainder*0.40:,.2f}")

    if st.session_state.role in ["sales", "admin"]:
        t.textLine(f"Equity: ${equity:,.2f}")
        t.textLine(f"Client Payout: ${payout:,.2f}")
        if st.session_state.role == "admin":
            t.textLine(f"Broker Profit: ${profit:,.2f}")

    c.drawText(t)
    c.showPage()
    c.save()
    b.seek(0)
    return b

st.download_button(
    "Download PDF Summary",
    export_pdf(),
    file_name="BrokerOne_LBOP_Summary.pdf",
    mime="application/pdf"
)
