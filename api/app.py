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
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# ==============================
# 🧠 HELPER FUNCTIONS
# ==============================

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
        date_str = dfp.loc[i, "date"].strftime("%Y-%m-%d")
        amt_str = f"{dfp.loc[i, 'amount']:,}"

        if i == 0:
            results["Last_Payment_Date"] = date_str
            results["Last_Payment_Amount"] = amt_str
        elif i == 1:
            results["2nd_Last_Payment_Date"] = date_str
            results["2nd_Last_Payment_Amount"] = amt_str
        elif i == 2:
            results["3rd_Last_Payment_Date"] = date_str
            results["3rd_Last_Payment_Amount"] = amt_str

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


def extract_va_multi(row, columns, keyword):
    result = []
    for col in columns:
        val = row.get(col)
        if pd.notna(val):
            lines = str(val).split(";")
            for l in lines:
                if keyword.upper() in l.upper():
                    result.append(l.strip() + ";")
    return "\n".join(result)


def split_phones(phone_str, index):
    if pd.isna(phone_str):
        return ""
    parts = [p.strip() for p in str(phone_str).split(";")]
    return parts[index] if index < len(parts) else ""

def split_refs(text, index):
    if pd.isna(text):
        return ""
    parts = [p.strip() for p in str(text).split(";")]
    return parts[index] if index < len(parts) else ""


# ==============================
# ⚙️ PROCESS DATA
# ==============================
def process_data(df):

    cli_map = [
        {"cli_col": "CLI_indodana_2_contain_adt", "product_col": "product_CLI_indodana_2_adt"},
        {"cli_col": "CLI_blibli_3_contain_adt", "product_col": "product_CLI_blibli_3_adt"},
        {"cli_col": "CLI_tiket_4_contain_adt", "product_col": "product_CLI_tiket_4_adt"},
        {"cli_col": "CLI_indodana_2_contain_imf", "product_col": "product_CLI_indodana_2_imf"},
        {"cli_col": "CLI_blibli_3_contain_imf", "product_col": "product_CLI_blibli_3_imf"},
        {"cli_col": "CLI_tiket_4_contain_imf", "product_col": "product_CLI_tiket_4_imf"},
    ]

    va_sources = [
        "va_number_adt_indodana","va_number_adt_blibli","va_number_adt_tiket",
        "va_number_imf_indodana","va_number_imf_blibli","va_number_imf_tiket",
    ]

    rows = []

    for _, r in df.iterrows():
        for m in cli_map:
            cli_val = r.get(m["cli_col"])
            product_val = r.get(m["product_col"])

            if pd.notna(cli_val) and str(cli_val).strip() != "":

                payment_col = payment_column_from_subproduct(m["cli_col"])
                payments = get_last_3_payments(r.get(payment_col, ""), product_val)

                new_row = {
                    "CLIENT_NAME": "INDODANA MULTI FINANCE",
                    "CLIENT_CODE": "CLI00057",
                    "ASSIGNMENT_DATE": r["start_date"],
                    "BATCH": r["batch_import"],
                    "CUSTOMER_ID": cli_val,
                    "AGREEMENT_NO": r["orderId_DC"],
                    "CUSTOMER_NAME": str(r["name"]).upper(),
                    "GENDER": r["applicantGender"],
                    "MOBILE_NO": str(split_phones(r["PhoneNumber"], 0)).lstrip("0"),
                    "MOBILE_NO_2": str(split_phones(r["PhoneNumber"], 1)).lstrip("0"),
                    "EMAIL": r["applicantPersonalEmail"],
                    "PRODUCT": m["cli_col"].split("_")[-1].upper(),
                    "TENOR": r["tenure"],
                    "SUB_PRODUCT": m["cli_col"],
                    "RENTAL": r["angsuran_per_bulan"],
                    "OVD_DAYS": r["max_current_dpd"],
                    "LOAN_AMOUNT": extract_amount(r["total_hutang_detail"], cli_val),
                    "OS_PRINCIPAL": extract_amount(r["pokok_tertunggak_detail"], cli_val),
                    "OS_CHARGES": extract_amount(r["latefee_detail"], cli_val),
                    "TOTAL_OUTSTANDING": extract_amount(r["total_outstanding_detail"], cli_val),
                    "BCA_VA": extract_va_multi(r, va_sources, "BCA"),
                    "MANDIRI_VA": extract_va_multi(r, va_sources, "MANDIRI"),
                    "PERMATA_VA": extract_va_multi(r, va_sources, "PERMATA"),
                    "COMPANY_NAME": r["current_company_name"],
                    "POSITION": r["jobTitle"],
                    "COLLATERAL_DESCRIPTION": product_val,
                    **payments
                }

                rows.append(new_row)

    return pd.DataFrame(rows)

# ==============================
# 🌐 MAIN APP
# ==============================
if not st.session_state.login_status:
    login()
else:
    st.title("📊 Aplikasi Data Cleansing CLI")
    uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

    if uploaded_file and st.button("🚀 Proses Data"):
        df = pd.read_excel(uploaded_file)
        result_df = process_data(df)
        st.session_state.result = result_df
        st.success("Data berhasil diproses!")

    if "result" in st.session_state:
        st.dataframe(st.session_state.result)

        output = BytesIO()
        st.session_state.result.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            "📥 Download Hasil Cleansing",
            output,
            "hasil_final_cli.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.button("Logout", on_click=logout)

st.markdown("---")
st.markdown("© 2026 - Muhamad Akbar")