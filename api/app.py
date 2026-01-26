import streamlit as st
import pandas as pd
import re
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_CREDENTIALS = {"admin": "akbar123"}

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
    st.session_state.clear()
    st.rerun()

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


def extract_amount(detail_str, cli_code):
    if pd.isna(detail_str) or pd.isna(cli_code):
        return 0

    pattern = rf"{re.escape(str(cli_code))}=([\d]+)"
    match = re.search(pattern, str(detail_str))
    return int(match.group(1)) if match else 0


def process_data(df):

    cli_map = [
        {"cli_col": "CLI_indodana_2_contain_adt", "product_col": "product_CLI_indodana_2_adt"},
        {"cli_col": "CLI_blibli_3_contain_adt", "product_col": "product_CLI_blibli_3_adt"},
        {"cli_col": "CLI_tiket_4_contain_adt", "product_col": "product_CLI_tiket_4_adt"},
        {"cli_col": "CLI_blibli_3_contain_imf", "product_col": "product_CLI_blibli_3_imf"},
    ]

    rows = []

    for _, r in df.iterrows():
        for m in cli_map:
            cli_val = r.get(m["cli_col"])
            product_val = r.get(m["product_col"])

            if pd.notna(cli_val) and str(cli_val).strip() != "":

                new_row = {
                    "start_date": r["start_date"],
                    "batch_import": r["batch_import"],
                    "agency_name": r["agency_name"],
                    "agent_kode": r["agent_kode"],
                    "agent_name": r["agent_name"],
                    "NIK": r["NIK"],
                    "applicantPersonalEmail": r["applicantPersonalEmail"],
                    "Kode": r["Kode"],
                    "total_order_id_aktif": r["total_order_id_aktif"],
                    "orderId_DC": r["orderId_DC"],
                    "orderId": cli_val,
                    "Merchant": m["cli_col"],
                    "Product": product_val,
                    "name": r["name"],
                    "dob": r["dob"],
                    "applicantGender": r["applicantGender"],
                    "mothername": r["mothername"],
                    "max_current_dpd": r["max_current_dpd"],

                    "pokok_tertunggak": extract_amount(r["pokok_tertunggak_detail"], cli_val),
                    "total_hutang": extract_amount(r["total_hutang_detail"], cli_val),
                    "latefee": extract_amount(r["latefee_detail"], cli_val),
                    "total_outstanding": extract_amount(r["total_outstanding_detail"], cli_val),

                    "VA_BCA": extract_va(r["va_number_adt_indodana"], "BCA"),
                    "VA_BLIBLI": extract_va(r["va_number_adt_indodana"], "BLIBLI"),
                    "VA_BNI": extract_va(r["va_number_adt_indodana"], "BNI"),
                    "VA_DANAMON": extract_va(r["va_number_adt_indodana"], "DANAMON"),
                    "VA_LINKAJA": extract_va(r["va_number_adt_indodana"], "LINKAJA"),
                    "VA_MANDIRI": extract_va(r["va_number_adt_indodana"], "MANDIRI"),
                    "VA_PERMATA": extract_va(r["va_number_adt_indodana"], "PERMATA"),

                    "payments_history_cli_indodana_2": r["payments_history_cli_indodana_2"],
                    "payments_history_cli_blibli_3": r["payments_history_cli_blibli_3"],
                    "payments_history_cli_tiket_4": r["payments_history_cli_tiket_4"],
                    "PhoneNumber": r["PhoneNumber"],
                    "applicantHomePhoneNumber": r["applicantHomePhoneNumber"],
                    "jobTitle": r["jobTitle"],
                    "current_company_name": r["current_company_name"],
                    "currentCompanyPhoneNumber": r["currentCompanyPhoneNumber"],
                    "referenceFullName": r["referenceFullName"],
                    "referenceRelationship": r["referenceRelationship"],
                    "referenceHomePhoneNumber": r["referenceHomePhoneNumber"],
                    "referenceMobilePhoneNumber": r["referenceMobilePhoneNumber"],
                    "broken_promise": r["broken_promise"],
                    "registration_type": r["registration_type"],
                    "indodana_merchant": r["indodana_merchant"],
                    "blibli_merchant": r["blibli_merchant"],
                    "tiket_merchant": r["tiket_merchant"],

                    "total_payment_last_1_month": r["total_payment_last_1_month"],
                    "total_payment_last_2_month": r["total_payment_last_2_month"],
                    "total_payment_last_3_month": r["total_payment_last_3_month"],
                    "total_payment_last_4_month": r["total_payment_last_4_month"],
                    "total_payment_last_5_month": r["total_payment_last_5_month"],

                    "nominal_approve": r["nominal_approve"],
                    "tenure": r["tenure"],
                    "tenure_time_unit": r["tenure_time_unit"],
                    "tgl_jatuh_tempo": r["tgl_jatuh_tempo"],
                    "sisa_tenor": r["sisa_tenor"],
                    "angsuran_per_bulan": r["angsuran_per_bulan"],
                    "denda_per_bulan": r["denda_per_bulan"],
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
