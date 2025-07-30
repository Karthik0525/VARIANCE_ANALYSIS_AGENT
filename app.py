import streamlit as st
import pandas as pd
from backend.analysis import process_data_and_generate_explanations
from exports.reporting import generate_pdf_report, generate_excel_report, generate_word_report

# Initialize session state
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'original_df' not in st.session_state:
    st.session_state.original_df = None
if 'config' not in st.session_state:
    st.session_state.config = {}

# --- App Layout ---
st.set_page_config(layout="wide", page_title="Variance Analysis Agent")
st.title("🤖 Variance Analysis Agent")
st.markdown("Upload a P&L, set materiality, and get instant, AI-powered variance explanations.")

# --- Sidebar for Inputs ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", help="Required for AI explanations.")
    company_name = st.text_input("Company Name", value="My Company")
    uploaded_file = st.file_uploader("Upload P&L (.csv or .xlsx)", type=['csv', 'xlsx'])

# --- Main App Logic ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.session_state.original_df = df.copy() # Save original data for exports

        st.header("1. Map Your Data Columns")
        columns = df.columns.tolist()
        account_col = st.selectbox("Select Account Column", columns, index=0)
        current_col = st.selectbox("Select Current Period Column", columns, index=1 if len(columns) > 1 else 0)
        prior_col = st.selectbox("Select Prior Period Column", columns, index=2 if len(columns) > 2 else 0)

        st.header("2. Set Materiality Thresholds")
        col1, col2 = st.columns(2)
        with col1:
            dollar_thresh = st.number_input("Dollar ($) Threshold", value=50000, min_value=0)
        with col2:
            percent_thresh = st.number_input("Percentage (%) Threshold", value=10.0, min_value=0.0, format="%.2f")

        if st.button("🚀 Run Analysis & Get Explanations", type="primary"):
            if not api_key:
                st.error("Please enter your OpenAI API key in the sidebar.")
            else:
                with st.spinner("Analyzing variances and generating AI explanations..."):
                    # Save config for reports
                    st.session_state.config = {
                        'company': company_name,
                        'period': f"{current_col} vs. {prior_col}",
                        'dollar': dollar_thresh,
                        'percent': percent_thresh
                    }
                    # Run full analysis
                    renamed_df = df.rename(columns={account_col: 'Account'})
                    results = process_data_and_generate_explanations(
                        renamed_df, current_col, prior_col, dollar_thresh, percent_thresh, api_key
                    )
                    st.session_state.results_df = results
                    st.success("Analysis Complete!")

    except Exception as e:
        st.error(f"An error occurred: {e}")

# --- Display Results ---
if st.session_state.results_df is not None:
    st.header("3. Material Variances & Explanations")
    if st.session_state.results_df.empty:
        st.info("No material variances were found based on the provided thresholds.")
    else:
        st.dataframe(st.session_state.results_df, use_container_width=True)

        st.header("4. Export Reports")
        cfg = st.session_state.config
        res_df = st.session_state.results_df
        orig_df = st.session_state.original_df

        col1, col2, col3 = st.columns(3)
        with col1:
            pdf_data = generate_pdf_report(res_df, cfg['company'], cfg['period'], cfg['dollar'], cfg['percent'])
            st.download_button("⬇️ Download PDF Report", pdf_data, f"{cfg['company']}_Variance_Report.pdf", "application/pdf")
        with col2:
            excel_data = generate_excel_report(orig_df, res_df)
            st.download_button("⬇️ Download Excel Report", excel_data, f"{cfg['company']}_Variance_Report.xlsx")
        with col3:
            word_data = generate_word_report(res_df, cfg['company'], cfg['period'])
            st.download_button("⬇️ Download Word Report", word_data, f"{cfg['company']}_Variance_Report.docx")