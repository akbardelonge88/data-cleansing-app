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
def extract_va(text, keyword):
    if pd.isna(text):
        return ""

    lines = str(text).split(";")
    result = []

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
    "va_number_adt_indodana",
    "va_number_adt_blibli",
    "va_number_adt_tiket",
    "va_number_imf_indodana",
    "va_number_imf_blibli",
    "va_number_imf_tiket",
    ]

    rows = []

    for _, r in df.iterrows():
        for m in cli_map:
            cli_val = r.get(m["cli_col"])
            product_val = r.get(m["product_col"])

            if pd.notna(cli_val) and str(cli_val).strip() != "":

                new_row = {
                    "CLIENT_NAME": "INDODANA MULTI FINANCE",
                    "CLIENT_CODE": "CLI00057",
                    "ASSIGNMENT_DATE": r["start_date"],
                    "ASSIGNED_TO": None,
                    "BATCH": r["batch_import"],
                    "CUSTOMER_ID": cli_val,
                    "ADDRESS": None,
                    "AGREEMENT_NO": r["orderId_DC"],
                    "CITY": None,
                    "CUSTOMER_NAME": str(r["name"]).upper(),
                    "PROVINCE": None, 
                    "GENDER": r["applicantGender"],
                    "MOBILE_NO": split_phones(r["PhoneNumber"], 0),
                    "DATE_OF_BIRTH": r["dob"],
                    "MOBILE_NO_2": split_phones(r["PhoneNumber"], 1),
                    "EMAIL": r["applicantPersonalEmail"],
                    "PRODUCT": m["cli_col"].split("_")[-1],
                    "TENOR": r["tenure"],
                    "SUB_PRODUCT": m["cli_col"],
                    "RENTAL": r["angsuran_per_bulan"],
                    "DISBURSE_DATE": None, 
                    "OVD_DAYS": r["max_current_dpd"],
                    "LOAN_AMOUNT": extract_amount(r["total_hutang_detail"], cli_val),
                    "BUCKET": None,
                    "DUEDATE": r["tgl_jatuh_tempo"],
                    "AMOUNT_OVERDUE": None,
                    "OS_PRINCIPAL": extract_amount(r["pokok_tertunggak_detail"], cli_val),
                    "LAST_PAYMENT_DATE": None,
                    "OS_INTEREST": None,
                    "LAST_PAYMENT_AMOUNT": None,
                    "OS_CHARGES": extract_amount(r["latefee_detail"], cli_val),
                    "PAID_OFF_WITH_DISCOUNT": None,
                    "TOTAL_OUTSTANDING": extract_amount(r["total_outstanding_detail"], cli_val),
                    "FLAG_DISCOUNT": None,
                    "BCA_VA": extract_va_multi(r, va_sources, "BCA"),
                    "INDOMARET": None,
                    "MANDIRI_VA": extract_va_multi(r, va_sources, "MANDIRI"),
                    "ALFAMART": None,
                    "BRI_VA": None,
                    "PERMATA_VA":extract_va_multi(r, va_sources, "PERMATA"),
                    "COMPANY_NAME":r["current_company_name"],
                    "ADDRESS_COMPANY": None, 
                    "POSITION": r["jobTitle"],
                    "OFFICE_PHONE_NO": r["currentCompanyPhoneNumber"],
                    "EMERGENCY_NAME_1": r["mothername"],
                    "EMERGENCY_NAME_2": split_refs(r["referenceFullName"], 0),
                    "EMERGENCY_RELATIONSHIP_1": "Ibu Kandung",
                    "EMERGENCY_RELATIONSHIP_2": split_refs(r["referenceRelationship"], 0),
                    "EMERGENCY_PHONE_NO_1": None,
                    "EMERGENCY_PHONE_NO_2": r["referenceMobilePhoneNumber"],
                    "EMERGENCY_ADDRESS_1": None,
                    "EMERGENCY_ADDRESS_2": None,
                    "REMARKS 1": None,
                    "REMARKS 2": None,
                    "REMARKS 3": None,
                    "COLLATERAL_DESCRIPTION": product_val,
                    "CERTIFICATE_NO / POLICE_NO": None,
                    "AGENT": None,
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
