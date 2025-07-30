import streamlit as st

def display_upload_section():
    """Displays the file upload UI."""
    st.header("1. Upload Your P&L Statement")
    uploaded_file = st.file_uploader(
        "Upload an Excel or CSV file",
        type=['csv', 'xlsx'],
        help="The file must contain columns for 'Account', a current period, and a prior period."
    )
    return uploaded_file

def display_config_section(columns):
    """Displays the configuration settings UI."""
    st.header("2. Configure Analysis")
    col1, col2 = st.columns(2)

    with col1:
        current_period = st.selectbox("Select Current Period", columns, index=len(columns)-2 if len(columns) > 1 else 0)
        dollar_threshold = st.number_input("Dollar ($) Materiality Threshold", value=50000)

    with col2:
        prior_period = st.selectbox("Select Prior Period", columns, index=len(columns)-1 if len(columns) > 2 else 0)
        percent_threshold = st.number_input("Percentage (%) Materiality Threshold", value=10.0)

    return current_period, prior_period, dollar_threshold, percent_threshold

def display_results(results_df):
    """Displays the variance analysis results."""
    st.header("3. Analysis Results")
    st.dataframe(results_df, use_container_width=True)

    # Create downloadable reports
    excel_data = results_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Download as CSV",
        data=excel_data,
        file_name='variance_analysis_report.csv',
        mime='text/csv',
    )