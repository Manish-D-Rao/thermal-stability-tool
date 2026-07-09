# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from src.method2_calc import process_data, REQUIRED_COLUMNS

st.set_page_config(page_title="Thermal Stability Tool — Method 2", layout="wide")
st.title("Thermal Stability Classification — Richardson Number Method")

uploaded_file = st.file_uploader("Upload sensor data (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    # --- Read file ---
    if uploaded_file.name.endswith(".csv"):
        raw_df = pd.read_csv(uploaded_file)
    else:
        raw_df = pd.read_excel(uploaded_file)

    # --- Validate columns ---
    missing = [c for c in REQUIRED_COLUMNS if c not in raw_df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    # --- Process ---
    with st.spinner("Calculating stability metrics..."):
        result_df = process_data(raw_df)

    st.success(f"Processed {len(result_df)} rows.")

    # --- Data table ---
    st.subheader("Processed data")
    st.dataframe(result_df.head(50))

    # --- Stability distribution pie chart ---
    st.subheader("Stability distribution")
    counts = result_df["stability"].value_counts().reset_index()
    counts.columns = ["stability", "count"]
    fig_pie = px.pie(counts, names="stability", values="count")
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Time series of Ri ---
    st.subheader("Richardson number over time")
    fig_line = px.line(result_df, x="datetime", y="ri")
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Day vs night comparison ---
    st.subheader("Day vs night stability")
    dn = result_df.groupby(["day_night", "stability"]).size().reset_index(name="count")
    fig_bar = px.bar(dn, x="day_night", y="count", color="stability", barmode="group")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Download button ---
    st.download_button(
        "Download results as CSV",
        result_df.to_csv(index=False),
        file_name="processed_stability_data.csv",
    )
else:
    st.info("Upload a file to get started.")