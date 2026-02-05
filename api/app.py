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

def extract_payments(payment_text):
    """
    Parse payment history lalu GROUP BY trx + date
    """
    if pd.isna(payment_text) or payment_text.strip() == "":
        return pd.DataFrame()

    pattern = r"(TRX-[A-Z0-9]+).*?Date ([0-9\-]+), Amount ([0-9]+)"
    matches = re.findall(pattern, payment_text)

    rows = []
    for trx, date, amount in matches:
        rows.append([trx, pd.to_datetime(date), int(amount)])

    if not rows:
        return pd.DataFrame()

    dfp = pd.DataFrame(rows, columns=["trx", "date", "amount"])
    dfp = dfp.groupby(["trx", "date"], as_index=False)["amount"].sum()
    dfp = dfp.sort_values("date", ascending=False).reset_index(drop=True)

    return dfp


def get_last_3_payments(payment_text):
    dfp = extract_payments(payment_text)

    results = {
        "LAST_PAYMENT_DATE": None,
        "LAST_PAYMENT_AMOUNT": None,
    }

    if len(dfp) > 0:
        results["LAST_PAYMENT_DATE"] = dfp.loc[0, "date"].strftime("%Y-%m-%d")
        results["LAST_PAYMENT_AMOUNT"] = dfp.loc[0, "amount"]

    return results


def extract_va(text, keyword):
    if pd.isna(text):
        return ""
    lines = str(text).split(";")
    return "\n".join([l.strip()+";" for l in lines if keyword.upper() in l.upper()])


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

                payment_info = get_last_3_payments(r.get("payment_history", ""))

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
                    "MOBILE_NO": str(split_phones(r["PhoneNumber"], 0)).lstrip("0"),
                    "DATE_OF_BIRTH": r["dob"],
                    "MOBILE_NO_2": str(split_phones(r["PhoneNumber"], 1)).lstrip("0"),
                    "EMAIL": r["applicantPersonalEmail"],
                    "PRODUCT": m["cli_col"].split("_")[-1].upper(),
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
                    "OS_INTEREST": None,
                    "OS_CHARGES": extract_amount(r["latefee_detail"], cli_val),
                    "PAID_OFF_WITH_DISCOUNT": None,
                    "TOTAL_OUTSTANDING": extract_amount(r["total_outstanding_detail"], cli_val),
                    "FLAG_DISCOUNT": None,
                    "BCA_VA": extract_va_multi(r, va_sources, "BCA"),
                    "INDOMARET": None,
                    "MANDIRI_VA": extract_va_multi(r, va_sources, "MANDIRI"),
                    "ALFAMART": None,
                    "BRI_VA": None,
                    "PERMATA_VA": extract_va_multi(r, va_sources, "PERMATA"),
                    "COMPANY_NAME": r["current_company_name"],
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

                rows.append(new_row)

    return pd.DataFrame(rows)