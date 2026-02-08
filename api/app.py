import streamlit as st
import pandas as pd
import re
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_CREDENTIALS = {"admin": "admin123"}

if "login_status" not in st.session_state:
    st.session_state.login_status = False

def login():
    st.title("🔐 Login Aplikasi Data Cleansing")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
            st.session_state.login_status = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah")

def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# ==============================
# 🧠 HELPER FUNCTIONS
# ==============================
def split_phones(text, idx):
    if pd.isna(text):
        return ""
    parts = [p.strip() for p in str(text).split(";")]
    return parts[idx] if idx < len(parts) else ""

def extract_amount(detail, cli):
    if pd.isna(detail) or pd.isna(cli):
        return 0
    m = re.search(rf"{re.escape(cli)}=([\d]+)", str(detail))
    return int(m.group(1)) if m else 0

def extract_va_multi(row, cols, keyword):
    res = []
    for c in cols:
        if pd.notna(row.get(c)):
            for l in str(row[c]).split(";"):
                if keyword.upper() in l.upper():
                    res.append(l.strip() + ";")
    return "\n".join(res)

# ==============================
# 💰 PAYMENT FUNCTIONS
# ==============================
def extract_payments(payment_text):
    if pd.isna(payment_text) or payment_text.strip() == "":
        return pd.DataFrame()

    pattern = r"(TRX-[A-Z0-9]+).*?Date ([0-9\-]+), Amount ([0-9]+)"
    matches = re.findall(pattern, payment_text)

    dfp = pd.DataFrame(matches, columns=["trx", "date", "amount"])
    if dfp.empty:
        return dfp

    dfp["date"] = pd.to_datetime(dfp["date"])
    dfp["amount"] = dfp["amount"].astype(int)

    # trx sama + tanggal sama → dijumlah
    dfp = dfp.groupby(["trx", "date"], as_index=False)["amount"].sum()
    dfp = dfp.sort_values("date", ascending=False)

    return dfp.reset_index(drop=True)

def get_last_3_payments(payment_text):
    dfp = extract_payments(payment_text)

    cols = {
        "LAST_PAYMENT_DATE": "",
        "LAST_PAYMENT_AMOUNT": "",
        "2ND_LAST_PAYMENT_DATE": "",
        "2ND_LAST_PAYMENT_AMOUNT": "",
        "3RD_LAST_PAYMENT_DATE": "",
        "3RD_LAST_PAYMENT_AMOUNT": "",
    }

    for i in range(min(3, len(dfp))):
        d = dfp.loc[i, "date"].strftime("%Y-%m-%d")
        a = f"{dfp.loc[i, 'amount']:,}"

        if i == 0:
            cols["LAST_PAYMENT_DATE"] = d
            cols["LAST_PAYMENT_AMOUNT"] = a
        elif i == 1:
            cols["2ND_LAST_PAYMENT_DATE"] = d
            cols["2ND_LAST_PAYMENT_AMOUNT"] = a
        elif i == 2:
            cols["3RD_LAST_PAYMENT_DATE"] = d
            cols["3RD_LAST_PAYMENT_AMOUNT"] = a

    return cols

def payment_column_from_subproduct(sub_product):
    s = sub_product.lower()
    if "indodana" in s:
        return "payments_history_cli_indodana_2"
    if "blibli" in s:
        return "payments_history_cli_blibli_3"
    if "tiket" in s:
        return "payments_history_cli_tiket_4"
    return None

# ==============================
# 🚀 MAIN PROCESS
# ==============================
def process_data(df):

    cli_map = [
        ("CLI_indodana_2_contain_adt", "ADT"),
        ("CLI_blibli_3_contain_adt", "ADT"),
        ("CLI_tiket_4_contain_adt", "ADT"),
        ("CLI_indodana_2_contain_imf", "IMF"),
        ("CLI_blibli_3_contain_imf", "IMF"),
        ("CLI_tiket_4_contain_imf", "IMF"),
    ]

    va_cols = [
        "va_number_adt_indodana","va_number_adt_blibli","va_number_adt_tiket",
        "va_number_imf_indodana","va_number_imf_blibli","va_number_imf_tiket"
    ]

    rows = []

    for _, r in df.iterrows():
        for cli_col, prod in cli_map:
            cli = r.get(cli_col)
            if pd.isna(cli) or str(cli).strip() == "":
                continue

            pay_col = payment_column_from_subproduct(cli_col)
            payment_info = get_last_3_payments(r.get(pay_col, ""))

            rows.append({
                "CUSTOMER_ID": cli,
                "AGREEMENT_NO": r["orderId_DC"],
                "PRODUCT": prod,
                "SUB_PRODUCT": cli_col,
                "LOAN_AMOUNT": extract_amount(r["total_hutang_detail"], cli),
                "OS_PRINCIPAL": extract_amount(r["pokok_tertunggak_detail"], cli),
                "OS_CHARGES": extract_amount(r["latefee_detail"], cli),
                "TOTAL_OUTSTANDING": extract_amount(r["total_outstanding_detail"], cli),
                "BCA_VA": extract_va_multi(r, va_cols, "BCA"),
                "MANDIRI_VA": extract_va_multi(r, va_cols, "MANDIRI"),
                **payment_info
            })

    return pd.DataFrame(rows)

# ==============================
# 🌐 STREAMLIT UI
# ==============================
if not st.session_state.login_status:
    login()
else:
    st.title("📊 Aplikasi Data Cleansing CLI")
    file = st.file_uploader("Upload Excel", type=["xlsx"])

    if file and st.button("🚀 Proses Data"):
        df = pd.read_excel(file)
        st.session_state.result = process_data(df)
        st.success("Proses selesai")

    if "result" in st.session_state:
        st.dataframe(st.session_state.result)

        out = BytesIO()
        st.session_state.result.to_excel(out, index=False)
        out.seek(0)

        st.download_button(
            "📥 Download",
            out,
            "hasil_final_cli.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.button("Logout", on_click=logout)

st.markdown("---")
st.markdown("© 2026 - Muhamad Akbar")