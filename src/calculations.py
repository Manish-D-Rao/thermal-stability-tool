import math
import numpy as np
import pandas as pd


def calculate_delta_t(t1, t2):
    return ((t1 - t2) / (59 - 22)) * 100


def calculate_shear(u1, u2):
    if not u1 or not u2:
        return np.nan
    return math.log(u1 / u2) / math.log(59 / 22)


def calculate_ws_bin(u):
    return round(u * 2) / 2


def calculate_ti(u, u_SD):
    if u == 0:
        return np.nan
    return u_SD / u


def calculate_ws120(u, shear):
    if pd.isna(shear) or shear == "":
        return np.nan
    return round((u * ((105 / 59) ** shear)), 2)


def calculate_ri(u59, u22, t59, t22):
    g = 9.81

    t_upper = t59 + 273.15
    t_lower = t22 + 273.15

    delta_z = 59 - 22

    temp_gradient = (t_upper - t_lower) / (delta_z + 9.8)

    wind_diff = u59 - u22

    if wind_diff == 0:
        return np.nan

    ri = (g * temp_gradient * delta_z ** 2) / (t_lower * wind_diff ** 2)

    return round(ri, 2)


def calculate_stability(ri):
    if pd.isna(ri):
        return np.nan
    if ri < -0.2:
        return "strongly unstable"
    elif -0.2 <= ri < -0.1:
        return "unstable"
    elif -0.1 <= ri < 0.1:
        return "neutral"
    elif 0.1 <= ri < 0.25:
        return "stable"
    else:
        return "strongly stable"


def _stability_to_3cat(stability):
    """Map 5-category stability to 3-category for chart compatibility."""
    if pd.isna(stability):
        return np.nan
    mapping = {
        "strongly unstable": "Unstable",
        "unstable": "Unstable",
        "neutral": "Neutral",
        "stable": "Stable",
        "strongly stable": "Stable",
    }
    return mapping.get(stability, np.nan)


def process_dataframe(df: pd.DataFrame):
    """Process uploaded dataframe with all calculations."""
    out = df.copy()

    # Parse Date/Time
    out["Date/Time"] = pd.to_datetime(out["Date/Time"], errors="coerce")
    out["Hour"] = out["Date/Time"].dt.hour
    out["Day/Night"] = out["Date/Time"].apply(
        lambda x: "Day" if 6 <= x.hour < 18 else "Night" if pd.notna(x) else np.nan
    )

    # Extract raw values
    ws59 = out["Ch2_Speed_59m_E [m/s]"]
    ws59_sd = out["Ch2_Speed_59m_E_SD [m/s]"]
    ws22 = out["Ch6_Speed_22m_E [m/s]"]
    t59 = out["Ch16_Temperature_59m_N [°C]"]
    t22 = out["Ch15_Temperature_22m_N [°C]"]

    # Calculate all metrics
    out["Delta T"] = ((t59 - t22) / (59 - 22)) * 100
    out["Shear"] = np.where(
        (ws59 > 0) & (ws22 > 0),
        np.log(ws59 / ws22) / np.log(59 / 22),
        np.nan
    )
    out["WS Bin"] = (ws59 * 2).round() / 2
    out["TI"] = np.where(ws59 != 0, ws59_sd / ws59, np.nan)
    out["WS120"] = np.where(
        out["Shear"].notna(),
        (ws59 * ((105 / 59) ** out["Shear"])).round(2),
        np.nan
    )

    # Ri calculation
    g = 9.81
    t_upper = t59 + 273.15
    t_lower = t22 + 273.15
    delta_z = 59 - 22
    temp_gradient = (t_upper - t_lower) / (delta_z + 9.8)
    wind_diff = ws59 - ws22
    out["Ri"] = np.where(
        wind_diff != 0,
        (g * temp_gradient * delta_z ** 2 / (t_lower * wind_diff ** 2)).round(2),
        np.nan
    )

    # Stability (5 categories)
    out["Stability"] = out["Ri"].apply(calculate_stability)
    # 3-category for charts
    out["Stability_3cat"] = out["Stability"].apply(_stability_to_3cat)

    return out


def build_classification_summary(df: pd.DataFrame):
    """Build summary table of stability classifications."""
    counts = df["Stability"].value_counts().to_dict()
    total = len(df)

    order = ["strongly unstable", "unstable", "neutral", "stable", "strongly stable"]
    rows = []
    for cat in order:
        cnt = counts.get(cat, 0)
        pct = (cnt / total * 100) if total > 0 else 0
        rows.append({
            "Stability": cat.title(),
            "Count": cnt,
            "Percentage": f"{pct:.1f}%"
        })
    return pd.DataFrame(rows)