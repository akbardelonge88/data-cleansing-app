import streamlit as st
import pandas as pd
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_CREDENTIALS = {
    "admin": "akbar123"
}

if "login_status" not in st.session_state:
    st.session_state.login_status = False

def login():
    st.title("🔐 Login Aplikasi Data Cleansing")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state.login_status = True
            st.success("Login berhasil!")
            st.rerun()
        else:
            st.error("Username atau password salah")

def logout():
    st.session_state.login_status = False
    st.session_state.pop("cleaned_data", None)
    st.rerun()

# ==============================
# 🧹 DATA CLEANSING FUNCTION
# ==============================
def process_data(df):

    merchant_cols = [
        "CLI_indodana_2_contain_adt",
        "CLI_blibli_3_contain_adt",
        "CLI_tiket_4_contain_adt",
        "CLI_blibli_3_contain_imf"
    ]

    results = []

    for _, row in df.iterrows():
        for col in merchant_cols:
            if pd.notna(row.get(col)) and str(row[col]).strip() != "0":

                new_row = row.copy()

                new_row["Merchant"] = col
                new_row["Product"] = row[col]

                # Mapping nominal berdasarkan merchant
                new_row["pokok_tertunggak"] = extract_value(row["pokok_tertunggak_detail"], col)
                new_row["total_hutang"] = extract_value(row["total_hutang_detail"], col)
                new_row["latefee"] = extract_value(row["latefee_detail"], col)
                new_row["total_outstanding"] = extract_value(row["total_outstanding_detail"], col)

                results.append(new_row)

    new_df = pd.DataFrame(results)

    # Hapus kolom detail
    new_df = new_df.drop(columns=[
        "pokok_tertunggak_detail",
        "total_hutang_detail",
        "latefee_detail",
        "total_outstanding_detail"
    ], errors="ignore")

    return new_df


def extract_value(text, merchant_code):
    if pd.isna(text):
        return 0
    try:
        parts = str(text).split(";")
        for p in parts:
            if merchant_code in p:
                return int(''.join(filter(str.isdigit, p)))
    except:
        return 0
    return 0

# ==============================
# 🌐 MAIN APP
# ==============================
if not st.session_state.login_status:
    login()
else:
    st.title("📊 Aplikasi Data Cleansing")
    st.write("Upload file Excel untuk diproses")

    uploaded_file = st.file_uploader("Upload File Excel", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        if st.button("🚀 Proses Data"):
            cleaned_df = process_data(df)
            st.session_state.cleaned_data = cleaned_df
            st.success("Data berhasil diproses!")

    if "cleaned_data" in st.session_state:
        st.dataframe(st.session_state.cleaned_data)

        output = BytesIO()
        st.session_state.cleaned_data.to_excel(output, index=False)
        output.seek(0)

        st.download_button(
            label="📥 Download Hasil Cleansing",
            data=output,
            file_name="hasil_cleansing.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.button("Logout", on_click=logout)

st.markdown("---")
st.markdown("© 2026 - Muhamad Akbar")
