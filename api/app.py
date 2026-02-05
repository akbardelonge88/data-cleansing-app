import streamlit as st
import pandas as pd
import re
from io import BytesIO

# ================= LOGIN =================
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
            st.rerun()
        else:
            st.error("Username atau password salah")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# ================= HELPER =================

def extract_trx_from_collateral(collateral_text):
    if pd.isna(collateral_text):
        return []
    return re.findall(r"TRX-[A-Z0-9]+", str(collateral_text))

def extract_payments_filtered(payment_text, trx_list):
    if pd.isna(payment_text) or payment_text.strip() == "":
        return pd.DataFrame()

    pattern = r"(TRX-[A-Z0-9]+).*?Date ([0-9\-]+), Amount ([0-9]+)"
    matches = re.findall(pattern, payment_text)

    rows = []
    for trx, date, amount in matches:
        if trx in trx_list:
            rows.append([trx, pd.to_datetime(date), int(amount)])

    if not rows:
        return pd.DataFrame()

    dfp = pd.DataFrame(rows, columns=["trx", "date", "amount"])
    dfp = dfp.groupby(["trx", "date"], as_index=False)["amount"].sum()
    dfp = dfp.sort_values("date", ascending=False).reset_index(drop=True)
    return dfp

def get_last_3_payments(payment_text, collateral_text):
    trx_list = extract_trx_from_collateral(collateral_text)
    dfp = extract_payments_filtered(payment_text, trx_list)

    results = {
        "Last_Payment_Date": "",
        "Last_Payment_Amount": "",
        "2nd_Last_Payment_Date": "",
        "2nd_Last_Payment_Amount": "",
        "3rd_Last_Payment_Date": "",
        "3rd_Last_Payment_Amount": "",
    }

    for i in range(min(3, len(dfp))):
        results[list(results.keys())[i*2]] = dfp.loc[i, "date"].strftime("%Y-%m-%d")
        results[list(results.keys())[i*2+1]] = f"{dfp.loc[i, 'amount']:,}"

    return results

def payment_column_from_subproduct(sub_product):
    sp = sub_product.lower()
    if "indodana" in sp:
        return "payments_history_cli_indodana_2"
    elif "blibli" in sp:
        return "payments_history_cli_blibli_3"
    elif "tiket" in sp:
        return "payments_history_cli_tiket_4"
    return None

def extract_amount(detail_str, cli_code):
    if pd.isna(detail_str) or pd.isna(cli_code):
        return 0
    pattern = rf"{re.escape(str(cli_code))}=([\d]+)"
    match = re.search(pattern, str(detail_str))
    return int(match.group(1)) if match else 0

def split_phones(phone_str, index):
    if pd.isna(phone_str):
        return ""
    parts = [p.strip() for p in str(phone_str).split(";")]
    return parts[index] if index < len(parts) else ""

# ================= PROCESS =================
def process_data(df):

    cli_map = [
        ("CLI_indodana_2_contain_adt", "product_CLI_indodana_2_adt"),
        ("CLI_blibli_3_contain_adt", "product_CLI_blibli_3_adt"),
        ("CLI_tiket_4_contain_adt", "product_CLI_tiket_4_adt"),
        ("CLI_indodana_2_contain_imf", "product_CLI_indodana_2_imf"),
        ("CLI_blibli_3_contain_imf", "product_CLI_blibli_3_imf"),
        ("CLI_tiket_4_contain_imf", "product_CLI_tiket_4_imf"),
    ]

    rows = []

    for _, r in df.iterrows():
        for cli_col, prod_col in cli_map:
            cli_val = r.get(cli_col)
            product_val = r.get(prod_col)

            if pd.notna(cli_val) and str(cli_val).strip() != "":
                payment_col = payment_column_from_subproduct(cli_col)
                payments = get_last_3_payments(r.get(payment_col, ""), product_val)

                new_row = {
                    "CUSTOMER_ID": cli_val,
                    "CUSTOMER_NAME": str(r["name"]).upper(),
                    "AGREEMENT_NO": r["orderId_DC"],
                    "SUB_PRODUCT": cli_col,
                    "PRODUCT_DETAIL": product_val,
                    "TENOR": r["tenure"],
                    "RENTAL": r["angsuran_per_bulan"],
                    "OVD_DAYS": r["max_current_dpd"],
                    "LOAN_AMOUNT": extract_amount(r["total_hutang_detail"], cli_val),
                    "OS_PRINCIPAL": extract_amount(r["pokok_tertunggak_detail"], cli_val),
                    "OS_CHARGES": extract_amount(r["latefee_detail"], cli_val),
                    "TOTAL_OUTSTANDING": extract_amount(r["total_outstanding_detail"], cli_val),
                    "MOBILE_NO": str(split_phones(r["PhoneNumber"], 0)).lstrip("0"),
                    **payments
                }

                rows.append(new_row)

    return pd.DataFrame(rows)

# ================= APP =================
if not st.session_state.login_status:
    login()
else:
    st.title("📊 Aplikasi Data Cleansing CLI (Multi Produk)")
    uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

    if uploaded_file and st.button("🚀 Proses Data"):
        df = pd.read_excel(uploaded_file)
        result_df = process_data(df)
        st.session_state.result = result_df
        st.success("Data berhasil diproses & dipecah per produk!")

    if "result" in st.session_state:
        st.dataframe(st.session_state.result)

        output = BytesIO()
        st.session_state.result.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Download Hasil Cleansing",
            output,
            "hasil_final_cli_multi_produk.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.button("Logout", on_click=logout)

st.markdown("---")
st.markdown("© 2026 - Muhamad Akbar")