import pandas as pd
import streamlit as st

from src.constants import REQUIRED_COLUMNS
from src.calculations import (
    calculate_ri,
    calculate_ws_bin,
    calculate_ti,
    calculate_shear,
    calculate_ws120,
    calculate_stability,
    calculate_delta_t,
    process_dataframe,
    build_classification_summary,
)
from src.validation import validate_upload, sanitize_numeric_columns, data_quality_summary
from src.charts import chart_stability_by_hour, chart_turbulence_distribution, chart_stability_by_windspeed
from src.column_mapping import build_rename_map

st.set_page_config(
    page_title="Thermal Stability Tool | GAWC Renewables",
    page_icon="🌬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def inject_css():
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }
        .main {
            background-color: #F7F8FA;
        }
        div.block-container {
            padding-top: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def safe_display_df(df):
    # cast mixed-type object columns to text so st.dataframe won't crash
    display_df = df.copy()
    for col in display_df.columns:
        if display_df[col].dtype == object:
            display_df[col] = display_df[col].astype(str)
    return display_df

def drop_phantom_columns(df):
    # drop empty "Unnamed: N" columns Excel sometimes leaves behind
    phantom_cols = [
        col for col in df.columns
        if str(col).startswith("Unnamed:") and df[col].isna().all()
    ]
    if phantom_cols:
        df = df.drop(columns=phantom_cols)
    return df

def page_landing():
    st.title("THERMAL STABILITY CALCULATOR")

    st.write("")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        if st.button("Manual Calculation", width='stretch', key="go_manual"):
            st.session_state.page = "manual"
            st.rerun()
    with col2:
        if st.button("Upload Excel / CSV", width='stretch', key="go_upload"):
            st.session_state.page = "upload"
            st.rerun()

def page_manual():
    st.title("Manual Calculation")

    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.rerun()

    st.write("")

    with st.form("manual_calc_form"):
        c1, c2 = st.columns(2)

        with c1:
            ws59 = st.number_input("Ch2_Speed_59m_E [m/s]", value=0.0, format="%.3f")
            ws59_sd = st.number_input("Ch2_Speed_59m_E_SD [m/s]", value=0.0, format="%.3f")
            ws22 = st.number_input("Ch6_Speed_22m_E [m/s]", value=0.0, format="%.3f")

        with c2:
            t59 = st.number_input("Ch16_Temperature_59m_N [°C]", value=0.0, format="%.3f")
            t22 = st.number_input("Ch15_Temperature_22m_N [°C]", value=0.0, format="%.3f")

        submitted = st.form_submit_button("Calculate", width='stretch')

    if submitted:
        ri = calculate_ri(ws59, ws22, t59, t22)
        ws_bin = calculate_ws_bin(ws59)
        ti = calculate_ti(ws59, ws59_sd)
        shear = calculate_shear(ws59, ws22)
        ws120 = calculate_ws120(ws59, shear)
        stability = calculate_stability(ri)
        delta_t = calculate_delta_t(t59, t22)

        st.write("")
        st.subheader("Results")

        r1c1, r1c2 = st.columns(2)
        r1c1.metric("Ri", f"{ri:.2f}" if not pd.isna(ri) else "N/A")
        r1c2.metric("Stability", stability.title() if stability and not pd.isna(stability) else "N/A")

        r2c1, r2c2 = st.columns(2)
        r2c1.metric("Shear", f"{shear:.4f}" if not pd.isna(shear) else "N/A")
        r2c2.metric("Delta T", f"{delta_t:.2f}" if not pd.isna(delta_t) else "N/A")

        r3c1, r3c2 = st.columns(2)
        r3c1.metric("WS Bin", f"{ws_bin:.1f}" if not pd.isna(ws_bin) else "N/A")
        r3c2.metric("TI", f"{ti:.3f}" if not pd.isna(ti) else "N/A")

        st.metric("WS120", f"{ws120:.2f}" if not pd.isna(ws120) else "N/A")

def page_upload():
    st.title("Upload & Batch Processing")

    if st.button("← Back to Home"):
        st.session_state.page = "landing"
        st.rerun()

    st.write("")
    st.subheader("Upload File")

    uploaded_file = st.file_uploader("Upload .xlsx or .csv", type=["xlsx", "csv"])

    if uploaded_file is None:
        st.info("Upload a file to continue. On the next step, you'll tell the app which of your columns holds each value.")
        return

    if uploaded_file.size == 0:
        st.error("The uploaded file is empty (0 bytes). Please upload a valid file.")
        return

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file)
        else:
            raw_df = pd.read_excel(uploaded_file)
    except pd.errors.EmptyDataError:
        st.error("The uploaded file has no data to read.")
        return
    except Exception as e:
        st.error(f"Could not read the uploaded file - it may be corrupted or in an unsupported format: {e}")
        return

    raw_df = drop_phantom_columns(raw_df)

    upload_errors = validate_upload(raw_df)
    if upload_errors:
        for msg in upload_errors:
            st.error(msg)
        return

    st.subheader("Preview")
    st.dataframe(safe_display_df(raw_df), width='stretch', height=320)

    # If a different file is uploaded, clear out any old typed-in column
    # names so the text boxes below don't show stale values from before.
    if st.session_state.get("last_uploaded_name") != uploaded_file.name:
        for param_name in REQUIRED_COLUMNS:
            st.session_state.pop(f"map_{param_name}", None)
        st.session_state.last_uploaded_name = uploaded_file.name
        st.session_state.processed_df = None

    st.write("")
    st.subheader("Column Mapping")
    st.caption(
        "Type the exact name of the column in your file that holds each value below "
        "(check the list under 'Columns found in your file' for the exact spelling)."
    )

    with st.expander("Columns found in your file"):
        for col in raw_df.columns:
            st.write(f"- {col}")

    file_columns = list(raw_df.columns)

    typed_values = {}
    map_c1, map_c2 = st.columns(2)
    for i, param_name in enumerate(REQUIRED_COLUMNS):
        target = map_c1 if i % 2 == 0 else map_c2
        typed_values[param_name] = target.text_input(
            param_name, value="", key=f"map_{param_name}"
        )

    st.write("")
    process_clicked = st.button("Process File", type="primary", width='stretch')

    if process_clicked:
        rename_map, missing_parameters = build_rename_map(typed_values, file_columns)
        if missing_parameters:
            st.error(
                "Could not find a matching column for: " + ", ".join(missing_parameters)
                + ". Check the spelling against the column list above and try again."
            )
        else:
            mapped_df = raw_df.rename(columns=rename_map)
            mapped_df, invalid_numeric = sanitize_numeric_columns(mapped_df)
            dirty_columns = {col: n for col, n in invalid_numeric.items() if n > 0}
            if dirty_columns:
                details = ", ".join(f"{col} ({n})" for col, n in dirty_columns.items())
                st.warning(f"Non-numeric values were found and treated as missing in: {details}.")
            st.session_state.processed_df = process_dataframe(mapped_df)

    if "processed_df" in st.session_state and st.session_state.processed_df is not None:
        processed_df = st.session_state.processed_df

        invalid_dates = int(processed_df["Date/Time"].isna().sum())
        if invalid_dates:
            st.warning(
                f"{invalid_dates} row(s) have an invalid or unreadable Date/Time value. "
                "These rows are excluded from Hour, Day/Night, and the hourly chart."
            )

        st.write("")
        st.subheader("Processed Data")
        st.dataframe(safe_display_df(processed_df), width='stretch', height=350)

        csv_bytes = processed_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Processed CSV",
            data=csv_bytes,
            file_name="thermal_stability_processed.csv",
            mime="text/csv",
            width='stretch',
        )

        dq_counts, dq_total = data_quality_summary(processed_df)
        dq_issues = {k: v for k, v in dq_counts.items() if v > 0}
        if dq_issues:
            with st.expander(f"Data quality notes ({dq_total} rows processed)"):
                for label, count in dq_issues.items():
                    st.write(f"- {label}: {count} row(s)")

        st.write("")
        st.subheader("Summary")
        summary_table = build_classification_summary(processed_df)
        st.dataframe(summary_table, width='stretch')

        st.write("")
        st.subheader("Charts")

        tab1, tab2, tab3 = st.tabs(
            ["Stability by Hour", "Turbulence Distribution", "Stability by Wind Speed"]
        )
        with tab1:
            st.pyplot(chart_stability_by_hour(processed_df), width='stretch')
        with tab2:
            st.pyplot(chart_turbulence_distribution(processed_df), width='stretch')
        with tab3:
            st.pyplot(chart_stability_by_windspeed(processed_df), width='stretch')

def main():
    inject_css()

    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "processed_df" not in st.session_state:
        st.session_state.processed_df = None

    if st.session_state.page == "landing":
        page_landing()
    elif st.session_state.page == "manual":
        page_manual()
    elif st.session_state.page == "upload":
        page_upload()
    else:
        st.session_state.page = "landing"
        page_landing()

if __name__ == "__main__":
    main()