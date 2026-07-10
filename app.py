# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Set up page configurations
st.set_page_config(
    page_title="Atmospheric Thermal Stability Tool — Richardson Number Method",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
    <style>
        /* General styling */
        .main {
            background-color: #0f1115;
            color: #e0e6ed;
        }
        .stMetric {
            background-color: #1a1d24;
            border: 1px solid #2d313d;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        .stMetric div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
            color: #00d4ff;
        }
        .stMetric div[data-testid="stMetricLabel"] {
            font-size: 0.9rem;
            color: #a0aec0;
            font-weight: 500;
        }
        /* Style standard buttons */
        .stButton>button {
            background-color: #00d4ff;
            color: #0f1115;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #00b3d6;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.4);
            color: #0f1115;
        }
        /* Custom card elements */
        .dashboard-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .dashboard-header h1 {
            color: #ffffff;
            margin: 0;
            font-size: 2.2rem;
        }
        .dashboard-header p {
            color: #d1d5db;
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        .info-card {
            background-color: #161920;
            border-left: 5px solid #00d4ff;
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- Load Modules & Setup Fallback -----------------
USING_FALLBACK = False
try:
    # Try importing Person A's calculation engine
    from src.method2_calc import process_data, REQUIRED_COLUMNS
except ImportError:
    # Set up Fallback Calculation Engine
    USING_FALLBACK = True
    
    REQUIRED_COLUMNS = [
        "Date/Time",
        "Ch2_Speed_59m_E [m/s]",
        "Ch2_Speed_59m_E_SD [m/s]",
        "Ch6_Speed_22m_E [m/s]",
        "Ch16_Temperature_59m_N [°C]",
        "Ch15_Temperature_22m_N [°C]"
    ]
    
    # Import individual calculators from calculations.py
    from src.calculations import (
        calculate_delta_t,
        calculate_shear,
        calculate_ws_bin,
        calculate_ti,
        calculate_ws120,
        calculate_ri,
        calculate_stability
    )

    def fallback_process_data(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
        """
        Processes raw df using functions in src/calculations.py
        """
        res = df.copy()
        
        # Mapped source columns
        c_dt = col_map["datetime"]
        c_ws59 = col_map["ws59"]
        c_ws59_sd = col_map["ws59_sd"]
        c_ws22 = col_map["ws22"]
        c_temp59 = col_map["temp59"]
        c_temp22 = col_map["temp22"]
        
        # Parse datetime and extract hour & day/night
        res["datetime"] = pd.to_datetime(res[c_dt], errors="coerce")
        res["hour"] = res["datetime"].dt.hour
        res["day_night"] = res["hour"].apply(lambda h: "Day" if pd.notna(h) and (6 <= h < 18) else "Night")
        
        # Convert columns to numeric, coercion replaces bad values with NaN
        u59 = pd.to_numeric(res[c_ws59], errors="coerce")
        u22 = pd.to_numeric(res[c_ws22], errors="coerce")
        u59_sd = pd.to_numeric(res[c_ws59_sd], errors="coerce")
        t59 = pd.to_numeric(res[c_temp59], errors="coerce")
        t22 = pd.to_numeric(res[c_temp22], errors="coerce")
        
        # 1. Delta T
        res["Delta T"] = calculate_delta_t(t59, t22)
        
        # 2. Wind Shear (row-by-row helper due to log logic)
        def run_shear(r):
            w59, w22 = r[c_ws59], r[c_ws22]
            try:
                if pd.isna(w59) or pd.isna(w22) or w59 <= 0 or w22 <= 0:
                    return np.nan
                val = calculate_shear(float(w59), float(w22))
                return float(val) if val != "" else np.nan
            except Exception:
                return np.nan
        res["Shear"] = res.apply(run_shear, axis=1)
        
        # 3. WS Bin
        res["WS Bin"] = u59.apply(lambda x: calculate_ws_bin(x) if pd.notna(x) else np.nan)
        
        # 4. Turbulence Intensity (TI)
        res["TI"] = calculate_ti(u59, u59_sd)
        
        # 5. WS@120m (power-law)
        res["WS 120"] = calculate_ws120(u59, res["Shear"])
        res["WS 120"] = pd.to_numeric(res["WS 120"], errors="coerce")
        
        # 6. Richardson Number (Ri)
        def run_ri(r):
            w59, w22, tm59, tm22 = r[c_ws59], r[c_ws22], r[c_temp59], r[c_temp22]
            try:
                if pd.isna(w59) or pd.isna(w22) or pd.isna(tm59) or pd.isna(tm22):
                    return np.nan
                # If wind speed difference is zero, Ri goes to infinity (let's keep it clean or return NaN)
                if abs(float(w59) - float(w22)) < 0.001:
                    return np.nan
                return calculate_ri(float(w59), float(w22), float(tm59), float(tm22))
            except Exception:
                return np.nan
        res["Ri"] = res.apply(run_ri, axis=1)
        
        # 7. Stability Classification
        def run_stability(val):
            if pd.isna(val):
                return "unknown"
            try:
                return calculate_stability(float(val))
            except Exception:
                return "unknown"
        res["stability"] = res["Ri"].apply(run_stability)
        
        return res

# Initialize uploaded_file
uploaded_file = None
if "main_uploader" in st.session_state and st.session_state.main_uploader is not None:
    uploaded_file = st.session_state.main_uploader
if "reuploader" in st.session_state and st.session_state.reuploader is not None:
    uploaded_file = st.session_state.reuploader

# ----------------- Header Section -----------------
st.markdown("""
    <div class="dashboard-header">
        <h1>Thermal Stability Analysis Tool</h1>
        <p>Method 2: Richardson Number (Ri) Atmospheric Classification & Wind Profile Extrapolation</p>
    </div>
""", unsafe_allow_html=True)

if uploaded_file is None:
    st.subheader("⚙️ Configuration & Upload")
    main_uploaded_file = st.file_uploader(
        "Drag and drop or click to upload your weather sensor data (CSV or Excel)",
        type=["csv", "xlsx"],
        key="main_uploader",
        help="Upload your weather sensor data file containing wind speeds and temperatures at different heights."
    )
    if main_uploaded_file is not None:
        uploaded_file = main_uploaded_file

if uploaded_file is None:
    # Landing page/Info when no file is uploaded
    st.markdown("""
        <div class="info-card">
            <h3>How to use this tool:</h3>
            <ol>
                <li>Prepare your <b>sensor data</b> in <b>CSV</b> or <b>Excel (.xlsx)</b> format.</li>
                <li>Ensure it contains measurements at two heights (e.g. 22 meters and 59 meters) for:
                    <ul>
                        <li>Date/Time stamps</li>
                        <li>Wind Speed (m/s) and standard deviation</li>
                        <li>Temperature (°C)</li>
                    </ul>
                </li>
                <li>Upload the file using the sidebar.</li>
                <li>If your column names don't match the defaults, use the <b>Column Mapper</b> in the sidebar to link them!</li>
                <li>Review stability counts, graphs, and download your processed results.</li>
            </ol>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("What is the Richardson Number Method?")
        st.write("""
            The **Richardson Number ($Ri$)** is a dimensionless parameter that measures the ratio of 
            buoyancy forces (thermal convection) to shear forces (mechanical wind mixing):
            
            $$Ri = \\frac{g \\cdot \\frac{\\partial \\theta}{\\partial z}}{T \\cdot \\left(\\frac{\\partial u}{\\partial z}\\right)^2}$$
            
            By classifying $Ri$, we divide atmospheric stability into states:
            * **Stable ($Ri > 0.1$)**: Prevents vertical movement. Smooth, layered wind.
            * **Neutral ($-0.1 \\le Ri \\le 0.1$)**: Mixing is driven entirely by wind shear.
            * **Unstable ($Ri < -0.1$)**: Bubbling, vertical convection. Turbulent wind.
        """)
    with col2:
        st.subheader("Typical Wind Mast Layout")
        # Visual diagram
        st.markdown("""
        ```text
        Height 2: 59m ──[Temp Sensor 2]──[ Wind Sensor 2] (u59, t59)
                       │
                       │   (Atmospheric Boundary Layer)
                       │
        Height 1: 22m ──[Temp Sensor 1]──[Wind Sensor 1] (u22, t22)
                       │
        Ground        ─┴──────────────────────────────────────────────
        ```
        """)

else:
    # --- Load Data with Encoding Fallback ---
    try:
        if uploaded_file.name.endswith(".csv"):
            # Try utf-8 first, fallback to cp1252/latin1
            try:
                raw_df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                raw_df = pd.read_csv(uploaded_file, encoding="cp1252")
        else:
            raw_df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.stop()

    with st.expander("⚙️ Dataset Configuration & Column Mapping", expanded=False):
        st.success(f"Successfully loaded {uploaded_file.name}")
        
        # Add a way to upload a different dataset inside the expander
        reupload_file = st.file_uploader(
            "Upload a different dataset (CSV or Excel)",
            type=["csv", "xlsx"],
            key="reuploader",
            help="Replace the current dataset by uploading a new one."
        )
        if reupload_file is not None:
            uploaded_file = reupload_file
            st.rerun()

        # Engine loading status
        if USING_FALLBACK:
            st.warning("Note: Using app-level calculations (Person A's `method2_calc` is not yet available)")
        else:
            st.success("Loaded calculation engine: `src.method2_calc`")

        # --- Column Mapping UI ---
        st.subheader("Sensor Column Mapping")
        st.write("Confirm which columns represent each metric:")

        # Automated Guessing Logic based on keywords
        cols = list(raw_df.columns)
        
        def guess_col(keywords, default):
            for col in cols:
                if any(k.lower() in col.lower() for k in keywords):
                    return col
            return default if default in cols else cols[0]

        dt_guess = guess_col(["date", "time", "timestamp"], "Date/Time")
        ws59_guess = guess_col(["speed_59m", "ws59", "speed_59", "ch2_speed"], "Ch2_Speed_59m_E [m/s]")
        ws59_sd_guess = guess_col(["speed_59m_sd", "ws59_sd", "ch2_speed_59m_e_sd"], "Ch2_Speed_59m_E_SD [m/s]")
        ws22_guess = guess_col(["speed_22m", "ws22", "speed_22", "ch6_speed"], "Ch6_Speed_22m_E [m/s]")
        t59_guess = guess_col(["temp_59", "temperature_59", "t59", "ch16_temp"], "Ch16_Temperature_59m_N [°C]")
        t22_guess = guess_col(["temp_22", "temperature_22", "t22", "ch15_temp"], "Ch15_Temperature_22m_N [°C]")

        # Select boxes in the expander
        mapped_dt = st.selectbox("Timestamp / Date-Time", cols, index=cols.index(dt_guess))
        mapped_ws59 = st.selectbox("Wind Speed 59m (u59)", cols, index=cols.index(ws59_guess))
        mapped_ws59_sd = st.selectbox("Wind Speed SD 59m (u59_sd)", cols, index=cols.index(ws59_sd_guess))
        mapped_ws22 = st.selectbox("Wind Speed 22m (u22)", cols, index=cols.index(ws22_guess))
        mapped_t59 = st.selectbox("Temperature 59m (t59)", cols, index=cols.index(t59_guess))
        mapped_t22 = st.selectbox("Temperature 22m (t22)", cols, index=cols.index(t22_guess))

        column_mapping = {
            "datetime": mapped_dt,
            "ws59": mapped_ws59,
            "ws59_sd": mapped_ws59_sd,
            "ws22": mapped_ws22,
            "temp59": mapped_t59,
            "temp22": mapped_t22
        }

        # Verify that the columns mapped actually exist and are distinct
        selected_cols = list(column_mapping.values())
        if len(set(selected_cols)) < len(selected_cols):
            st.warning("Note: Some fields map to the same column. Please check your selections.")

        # --- Data Cleaning and Validation ---
        st.subheader("Data Cleaning Options")
        handle_nans = st.selectbox(
            "Handle Missing Values (NaNs)",
            ["Drop Rows", "Interpolate (Fill Linear)"],
            index=0
        )

        clean_df = raw_df[selected_cols].copy()
        total_rows = len(clean_df)

        if handle_nans == "Drop Rows":
            processed_clean_df = clean_df.dropna()
            dropped_count = total_rows - len(processed_clean_df)
            if dropped_count > 0:
                st.info(f"Dropped {dropped_count} rows containing missing/NaN values.")
        else:
            # Interpolate numeric columns, forward-fill timestamps
            numeric_cols = [mapped_ws59, mapped_ws59_sd, mapped_ws22, mapped_t59, mapped_t22]
            processed_clean_df = clean_df.copy()
            processed_clean_df[numeric_cols] = processed_clean_df[numeric_cols].interpolate(method="linear").bfill().ffill()
            processed_clean_df = processed_clean_df.dropna(subset=[mapped_dt])
            st.info("Interpolated missing numeric data.")

    # Show warning if dataset is too small
    if len(processed_clean_df) == 0:
        st.error("No valid data remaining after filtering. Please verify your file or column mapping selections.")
        st.stop()

    # --- Calculations Execution ---
    with st.spinner("Calculating stability metrics and Richardson Number..."):
        if USING_FALLBACK:
            # Run fallback process
            result_df = fallback_process_data(processed_clean_df, column_mapping)
        else:
            try:
                result_df = process_data(processed_clean_df)
            except Exception as e:
                st.error(f"Failed to process with Person A's engine: {e}. Falling back to app calculations.")
                result_df = fallback_process_data(processed_clean_df, column_mapping)

    # ----------------- Dashboard Layout & Analytics -----------------
    st.success(f"Successfully processed {len(result_df)} rows!")

    # Calculate key metrics
    # Drop "unknown" if stability had calculations errors
    valid_stability = result_df[result_df["stability"] != "unknown"]
    total_valid = len(valid_stability)
    
    stable_count = len(valid_stability[valid_stability["stability"].isin(["stable", "strongly stable"])])
    neutral_count = len(valid_stability[valid_stability["stability"] == "neutral"])
    unstable_count = len(valid_stability[valid_stability["stability"].isin(["unstable", "strongly unstable"])])

    pct_stable = (stable_count / total_valid * 100) if total_valid > 0 else 0
    pct_neutral = (neutral_count / total_valid * 100) if total_valid > 0 else 0
    pct_unstable = (unstable_count / total_valid * 100) if total_valid > 0 else 0

    avg_ws59 = result_df[mapped_ws59].mean()
    avg_ws120 = result_df["WS 120"].mean() if "WS 120" in result_df.columns else np.nan
    avg_ti = result_df["TI"].mean() if "TI" in result_df.columns else np.nan

    # KPI Metrics Row
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    kpi1.metric("Total Hours", f"{round(len(result_df) * 10 / 60, 1)} hrs", help="Based on 10-minute intervals")
    kpi2.metric("Stable Atmosphere", f"{pct_stable:.1f}%", f"{stable_count} intervals")
    kpi3.metric("Neutral Atmosphere", f"{pct_neutral:.1f}%", f"{neutral_count} intervals")
    kpi4.metric("Unstable Atmosphere", f"{pct_unstable:.1f}%", f"{unstable_count} intervals")
    kpi5.metric("Avg Wind Speed (59m)", f"{avg_ws59:.2f} m/s", f"Avg 120m: {avg_ws120:.2f} m/s" if pd.notna(avg_ws120) else None)

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visual Dashboard", "📈 Wind Profile & Turbulence", "📋 Processed Data Table", "⚙️ Export & Settings"])

    with tab1:
        col_charts_left, col_charts_right = st.columns([1, 1])

        with col_charts_left:
            st.subheader("Atmospheric Stability Distribution")
            
            # stability distribution pie chart
            counts = result_df["stability"].value_counts().reset_index()
            counts.columns = ["Stability Class", "Count"]
            
            # Map colors for nice presentation
            color_map = {
                "strongly stable": "#1e3a8a",
                "stable": "#3b82f6",
                "neutral": "#6b7280",
                "unstable": "#f97316",
                "strongly unstable": "#ef4444",
                "unknown": "#374151"
            }
            
            fig_pie = px.pie(
                counts, 
                names="Stability Class", 
                values="Count",
                color="Stability Class",
                color_discrete_map=color_map,
                hole=0.4
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6ed",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_charts_right:
            st.subheader("Day vs. Night Stability Profile")
            # Day vs night comparison bar chart
            dn_counts = result_df.groupby(["day_night", "stability"]).size().reset_index(name="Count")
            
            fig_bar = px.bar(
                dn_counts,
                x="day_night",
                y="Count",
                color="stability",
                barmode="group",
                color_discrete_map=color_map,
                labels={"day_night": "Time of Day", "Count": "Number of Intervals", "stability": "Stability Class"}
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6ed",
                xaxis=dict(gridcolor="#2d313d"),
                yaxis=dict(gridcolor="#2d313d")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Time series plot
        st.subheader("Richardson Number ($Ri$) and Temp Gradient Time Series")
        
        # We need to let user filter range of Ri because inf / massive values skew plot
        ri_cap = st.slider("Cap Ri plot range for readability", 0.5, 10.0, 2.0, 0.5)
        
        # Filter for plotting to avoid massive vertical scaling
        plot_df = result_df.copy()
        plot_df["ri_clipped"] = plot_df["Ri"].clip(-ri_cap, ri_cap)

        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=plot_df["datetime"], 
            y=plot_df["ri_clipped"], 
            mode="lines", 
            name="Richardson Number (Ri)",
            line=dict(color="#00d4ff", width=1.5)
        ))
        
        # Add temperature gradient if calculated
        if "Delta T" in plot_df.columns:
            fig_line.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["Delta T"],
                mode="lines",
                name="Temp Gradient (ΔT/100m)",
                line=dict(color="#ef4444", width=1.0),
                yaxis="y2"
            ))

        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e0e6ed",
            xaxis=dict(title="Time", gridcolor="#2d313d"),
            yaxis=dict(title="Richardson Number (Clipped)", gridcolor="#2d313d"),
            yaxis2=dict(
                title="Temperature Gradient (°C/100m)",
                overlaying="y",
                side="right"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        col_wind_left, col_wind_right = st.columns([1, 1])

        with col_wind_left:
            st.subheader("Average Wind Profile (Shear Extrapolation)")
            # Plot wind profile: 22m, 59m, and 120m
            heights = [22, 59, 120]
            avg_speeds = [
                result_df[mapped_ws22].mean(),
                result_df[mapped_ws59].mean(),
                avg_ws120 if pd.notna(avg_ws120) else np.nan
            ]
            
            fig_profile = go.Figure()
            fig_profile.add_trace(go.Scatter(
                x=avg_speeds,
                y=heights,
                mode="lines+markers",
                line=dict(color="#00d4ff", width=3, dash="dash"),
                marker=dict(size=10, color=["#f59e0b", "#10b981", "#ef4444"]),
                name="Measured / Extrapolated"
            ))
            
            fig_profile.update_layout(
                xaxis_title="Average Wind Speed (m/s)",
                yaxis_title="Height Above Ground (m)",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e0e6ed",
                xaxis=dict(gridcolor="#2d313d"),
                yaxis=dict(gridcolor="#2d313d", range=[0, 130])
            )
            st.plotly_chart(fig_profile, use_container_width=True)
            st.info("The 120m wind speed is extrapolated from 59m speed using the calculated power-law shear exponent.")

        with col_wind_right:
            st.subheader("Turbulence Intensity (TI) vs. Wind Speed")
            # TI vs Wind Speed scatter
            if "TI" in result_df.columns:
                # Sample the dataset if it's very large for smoother rendering
                sample_size = min(3000, len(result_df))
                scatter_df = result_df.sample(sample_size, random_state=42)
                
                fig_scatter = px.scatter(
                    scatter_df,
                    x=mapped_ws59,
                    y="TI",
                    color="stability",
                    color_discrete_map=color_map,
                    opacity=0.6,
                    labels={mapped_ws59: "Wind Speed at 59m (m/s)", "TI": "Turbulence Intensity (TI)"}
                )
                fig_scatter.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#e0e6ed",
                    xaxis=dict(gridcolor="#2d313d"),
                    yaxis=dict(gridcolor="#2d313d", range=[0, 1])
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.write("Turbulence Intensity calculations not available.")

    with tab3:
        st.subheader("Processed Results (First 100 rows)")
        st.write("Below is a preview of the raw and derived parameters. Click column names to sort.")
        
        # Display table with scroll bars
        display_cols = ["datetime", "hour", "day_night", mapped_ws59, mapped_ws22, "Delta T", "Shear", "TI", "Ri", "stability", "WS 120"]
        display_cols = [c for c in display_cols if c in result_df.columns]
        st.dataframe(result_df[display_cols].head(100), use_container_width=True)

    with tab4:
        st.subheader("Export Results")
        st.write("You can download the full processed dataset with all added physical metrics.")
        
        # Create CSV download button
        csv_data = result_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Processed Data as CSV",
            data=csv_data,
            file_name="processed_thermal_stability_method2.csv",
            mime="text/csv"
        )
        
        st.subheader("Environment Details")
        st.write(f"**Calculator Mode:** {'Fallback Engine' if USING_FALLBACK else 'Standard Engine (Person A)'}")
        st.write(f"**Number of records processed:** {len(result_df)}")
        st.write(f"**Active mappings:**")
        st.json(column_mapping)