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
    st.rerun()

# ==============================
# 🧠 HELPER FUNCTIONS
# ==============================
def split_phones(text, idx):
    if pd.isna(text):
        return ""
    arr = [x.strip() for x in str(text).split(";")]
    return arr[idx] if idx < len(arr) else ""

def split_refs(text, idx):
    if pd.isna(text):
        return ""
    arr = [x.strip() for x in str(text).split(";")]
    return arr[idx] if idx < len(arr) else ""

def extract_amount(detail, cli):
    if pd.isna(detail) or pd.isna(cli):
        return 0
    m = re.search(rf"{re.escape(str(cli))}=([\d]+)", str(detail))
    return int(m.group(1)) if m else 0

def extract_va_multi(row, cols, keyword):
    res = []
    for c in cols:
        v = row.get(c)
        if pd.notna(v):
            for x in str(v).split(";"):
                if keyword.upper() in x.upper():
                    res.append(x.strip() + ";")
    return "\n".join(res)

# ==============================
# 💳 PAYMENT PARSER
# ==============================
def extract_payments(payment_text):
    if pd.isna(payment_text) or payment_text.strip() == "":
        return pd.DataFrame()

    pattern = r"(TRX-[A-Z0-9]+).*?Date ([0-9\-]+), Amount ([0-9]+)"
    matches = re.findall(pattern, payment_text)

    rows = []
    for trx, date, amt in matches:
        rows.append([trx, pd.to_datetime(date), int(amt)])

    if not rows:
        return pd.DataFrame()

    dfp = pd.DataFrame(rows, columns=["trx", "date", "amount"])

    # ⚠️ RULE:
    # hanya dijumlahkan kalau TRX & DATE sama
    dfp = dfp.groupby(["trx", "date"], as_index=False)["amount"].sum()
    dfp = dfp.sort_values("date", ascending=False).reset_index(drop=True)
    return dfp

def get_last_3_payments(payment_text):
    dfp = extract_payments(payment_text)

    out = {
        "Last_Payment_Date": "",
        "Last_Payment_Amount": "",
        "2nd_Last_Payment_Date": "",
        "2nd_Last_Payment_Amount": "",
        "3rd_Last_Payment_Date": "",
        "3rd_Last_Payment_Amount": "",
    }

    for i in range(min(3, len(dfp))):
        d = dfp.loc[i, "date"].strftime("%Y-%m-%d")
        a = f"{dfp.loc[i, 'amount']:,}"

        if i == 0:
            out["Last_Payment_Date"] = d
            out["Last_Payment_Amount"] = a
        elif i == 1:
            out["2nd_Last_Payment_Date"] = d
            out["2nd_Last_Payment_Amount"] = a
        elif i == 2:
            out["3rd_Last_Payment_Date"] = d
            out["3rd_Last_Payment_Amount"] = a

    return out

def payment_col_from_subproduct(sub_product):
    sp = sub_product.lower()
    if "indodana" in sp:
        return "payments_history_cli_indodana_2"
    if "blibli" in sp:
        return "payments_history_cli_blibli_3"
    if "tiket" in sp:
        return "payments_history_cli_tiket_4"
    return None

# ==============================
# 🧠 MAIN PROCESS
# ==============================
def process_data(df):

    cli_map = [
        {"cli": "CLI_indodana_2_contain_adt", "prod": "product_CLI_indodana_2_adt"},
        {"cli": "CLI_blibli_3_contain_adt", "prod": "product_CLI_blibli_3_adt"},
        {"cli": "CLI_tiket_4_contain_adt", "prod": "product_CLI_tiket_4_adt"},
        {"cli": "CLI_indodana_2_contain_imf", "prod": "product_CLI_indodana_2_imf"},
        {"cli": "CLI_blibli_3_contain_imf", "prod": "product_CLI_blibli_3_imf"},
        {"cli": "CLI_tiket_4_contain_imf", "prod": "product_CLI_tiket_4_imf"},
    ]

    va_sources = [
        "va_number_adt_indodana","va_number_adt_blibli","va_number_adt_tiket",
        "va_number_imf_indodana","va_number_imf_blibli","va_number_imf_tiket"
    ]

    rows = []

    for _, r in df.iterrows():
        for m in cli_map:
            cli_val = r.get(m["cli"])
            if pd.isna(cli_val) or str(cli_val).strip() == "":
                continue

            pay_col = payment_col_from_subproduct(m["cli"])
            payment_info = get_last_3_payments(r.get(pay_col)) if pay_col else {}

            row = {
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
                "MOBILE_NO": str(split_phones(r["PhoneNumber"], 0)).lstrip("0"),
                "DATE_OF_BIRTH": r["dob"],
                "MOBILE_NO_2": str(split_phones(r["PhoneNumber"], 1)).lstrip("0"),
                "EMAIL": r["applicantPersonalEmail"],
                "PRODUCT": m["cli"].split("_")[-1].upper(),
                "TENOR": r["tenure"],
                "SUB_PRODUCT": m["cli"],
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
                **payment_info
            }

            rows.append(row)

    return pd.DataFrame(rows)

# ==============================
# 🌐 STREAMLIT APP
# ==============================
if not st.session_state.login_status:
    login()
else:
    st.title("📊 Aplikasi Data Cleansing CLI")

    file = st.file_uploader("Upload File Excel", type=["xlsx"])

    if file and st.button("🚀 Proses Data"):
        df = pd.read_excel(file)
        result = process_data(df)
        st.session_state.result = result
        st.success("Data berhasil diproses")

    if "result" in st.session_state:
        st.dataframe(st.session_state.result)

        buf = BytesIO()
        st.session_state.result.to_excel(buf, index=False)
        buf.seek(0)

        st.download_button(
            "📥 Download Hasil",
            buf,
            "hasil_final_cli.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.button("Logout", on_click=logout)

st.markdown("---")
st.markdown("© 2026 - Muhamad Akbar")