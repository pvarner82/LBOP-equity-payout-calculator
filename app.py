import streamlit as st
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import io

# =========================
# AUTH SYSTEM
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
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

# =========================
# ROLE LABELS
# =========================
ROLE_LABEL = {
    "admin": "Internal Admin Calculator",
    "sales": "Internal Sales Calculator",
    "dealer": "Dealer Calculator",
    "client": "Client Calculator",
}

st.title("Broker One Finance")
st.subheader("Lease Buyout Program (LBOP)")
st.caption(ROLE_LABEL[st.session_state.role])

# =========================
# STANDARD FEES (FIXED)
# =========================
DEALER_FEE = 2000.0
AUCTION_FEE = 1000.0
REGISTRATION_FEE = 250.0
TRANSPORT_FEE = 500.0
PARTNER_FEE = 350.0

# =========================
# COMMON INPUTS
# =========================
loan = st.number_input("Loan Amount", min_value=0.0, step=100.0)
buy_now = st.number_input("Buy Now Price", min_value=0.0, step=100.0)
sales_tax = loan * 0.07

# =========================
# CLIENT VERSION
# =========================
if st.session_state.role == "client":
    st.subheader("Client Information")
    client_name = st.text_input("Your Name")

    st.subheader("Standard Program Fees")
    st.markdown(
        f"""
        **Dealer Fee:** ${DEALER_FEE:,.2f}  
        **Auction Fee:** ${AUCTION_FEE:,.2f}  
        **Registration Fee:** ${REGISTRATION_FEE:,.2f}  
        **Transport Fee:** ${TRANSPORT_FEE:,.2f}  
        **Partner / Floor Fee:** ${PARTNER_FEE:,.2f}  
        **Estimated Sales Tax (7%):** ${sales_tax:,.2f}
        """
    )

    total_fees = (
        DEALER_FEE
        + AUCTION_FEE
        + REGISTRATION_FEE
        + TRANSPORT_FEE
        + PARTNER_FEE
        + sales_tax
    )

    equity = loan - (buy_now + total_fees)

    if buy_now <= 3000:
        pct = 0.60
    elif buy_now >= 19000:
        pct = 0.425
    else:
        pct = 0.60 - ((buy_now - 3000) / 16000) * 0.175

    payout = equity * pct

    st.subheader("Estimated Results")
    st.metric("Estimated Equity", f"${equity:,.2f}")
    st.metric("Estimated Cash Payout", f"${payout:,.2f}")

# =========================
# (Dealer / Internal sections unchanged for brevity)
# =========================

def export_pdf():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    t = c.beginText(40, 750)

    t.textLine("Broker One Finance")
    t.textLine("Lease Buyout Program (LBOP)")
    t.textLine(ROLE_LABEL[st.session_state.role])
    t.textLine("")
    t.textLine(f"Client Name: {client_name if 'client_name' in locals() else ''}")
    t.textLine(f"Loan Amount: ${loan:,.2f}")
    t.textLine(f"Buy Now Price: ${buy_now:,.2f}")

    c.drawText(t)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

st.download_button(
    "Download PDF Summary",
    export_pdf(),
    file_name="BrokerOne_LBOP_Client_Summary.pdf",
    mime="application/pdf"
)
