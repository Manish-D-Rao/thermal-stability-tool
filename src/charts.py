import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from src.constants import (
    STABILITY_ORDER, COLOR_GRID, COLOR_TEXT, COLOR_STABLE,
    COLOR_NEUTRAL_HOURLY, COLOR_UNSTABLE, COLOR_WINDSPEED,
    COLOR_DAY, COLOR_NIGHT, COLOR_NEUTRAL_WSBIN
)


def _style_axis(ax, show_grid=True):
    ax.set_facecolor("white")
    if show_grid:
        ax.grid(True, axis="y", color=COLOR_GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color("#B8C0C9")
    ax.tick_params(colors=COLOR_TEXT, labelsize=9)
    ax.xaxis.label.set_color(COLOR_TEXT)
    ax.xaxis.label.set_fontsize(10)
    ax.yaxis.label.set_color(COLOR_TEXT)
    ax.yaxis.label.set_fontsize(10)
    ax.title.set_color(COLOR_TEXT)


def chart_stability_by_hour(df: pd.DataFrame):
    hours = list(range(24))
    stability_col = "Stability_3cat" if "Stability_3cat" in df.columns else "Stability"
    grouped = df.groupby("Hour")[stability_col].value_counts().unstack(fill_value=0)
    grouped = grouped.reindex(index=hours, columns=STABILITY_ORDER, fill_value=0)
    totals = grouped.sum(axis=1).replace(0, np.nan)
    pct = grouped.div(totals, axis=0).fillna(0) * 100

    avg_wind_speed = df.groupby("Hour")["Ch2_Speed_59m_E [m/s]"].mean().reindex(hours)

    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    bottom = np.zeros(len(hours))
    colors = {"Stable": COLOR_STABLE, "Neutral": COLOR_NEUTRAL_HOURLY, "Unstable": COLOR_UNSTABLE}
    for band in STABILITY_ORDER:
        if band in grouped.columns:
            ax.bar(hours, pct[band], bottom=bottom, label=band, color=colors[band], width=0.75)
            bottom += pct[band].values

    ax.set_title("Atmospheric Stability by Hour of Day", fontsize=13, fontweight="bold")
    ax.set_xlabel("Hour of the Day")
    ax.set_ylabel("Time (%)")
    ax.set_xticks(hours)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    _style_axis(ax)

    ax2 = ax.twinx()
    ax2.plot(hours, avg_wind_speed, color=COLOR_WINDSPEED, linewidth=1.8, label="Wind Speed")
    ax2.set_ylabel("Wind Speed (m/s)")
    ax2.yaxis.label.set_color(COLOR_TEXT)
    ax2.yaxis.label.set_fontsize(10)
    ax2.tick_params(colors=COLOR_TEXT, labelsize=9)
    _style_axis(ax2, show_grid=False)
    ax2.spines["top"].set_visible(False)

    bar_handles, bar_labels = ax.get_legend_handles_labels()
    line_handles, line_labels = ax2.get_legend_handles_labels()
    ax.legend(
        bar_handles + line_handles, bar_labels + line_labels,
        loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False, fontsize=9,
    )
    fig.tight_layout()
    return fig


def chart_turbulence_distribution(df: pd.DataFrame):
    ws_bins = [round(0.5 * i, 1) for i in range(1, 41)]

    day_df = df[df["Day/Night"] == "Day"]
    night_df = df[df["Day/Night"] == "Night"]

    day_ti = day_df.groupby("WS Bin")["TI"].mean().reindex(ws_bins)
    night_ti = night_df.groupby("WS Bin")["TI"].mean().reindex(ws_bins)

    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    ax.plot(ws_bins, day_ti, linewidth=1.8, color=COLOR_DAY, label="Day")
    ax.plot(ws_bins, night_ti, linewidth=1.8, color=COLOR_NIGHT, label="Night")

    ax.set_title("Turbulence Distribution", fontsize=13, fontweight="bold")
    ax.set_xlabel("Wind Speed (m/s)")
    ax.set_ylabel("TI (%)")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=9)
    _style_axis(ax)
    fig.tight_layout()
    return fig


def chart_stability_by_windspeed(df: pd.DataFrame):
    ws_bins = [round(0.5 * i, 1) for i in range(0, 41)]

    stability_col = "Stability_3cat" if "Stability_3cat" in df.columns else "Stability"
    grouped = df.groupby("WS Bin")[stability_col].value_counts().unstack(fill_value=0)
    grouped = grouped.reindex(index=ws_bins, columns=STABILITY_ORDER, fill_value=0)
    total_all = grouped.values.sum()
    pct = (grouped / total_all * 100) if total_all else grouped * 0

    fig, ax = plt.subplots(figsize=(9, 4.2), dpi=150)
    bottom = np.zeros(len(ws_bins))
    colors = {"Stable": COLOR_STABLE, "Neutral": COLOR_NEUTRAL_WSBIN, "Unstable": COLOR_UNSTABLE}
    for band in STABILITY_ORDER:
        if band in grouped.columns:
            ax.bar(ws_bins, pct[band], bottom=bottom, label=band, color=colors[band], width=0.4)
            bottom += pct[band].values

    ax.set_title("Wind Speed and Stability Distribution", fontsize=13, fontweight="bold")
    ax.set_xlabel("Wind Speed (m/s)")
    ax.set_ylabel("Frequency Distribution (%)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=3, frameon=False, fontsize=9)
    _style_axis(ax)
    fig.tight_layout()
    return fig