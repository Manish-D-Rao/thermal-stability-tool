import pandas as pd

HEIGHT_UPPER = 59
HEIGHT_LOWER = 22
DELTA_Z = HEIGHT_UPPER - HEIGHT_LOWER
EXTRAPOLATION_HEIGHT = 105
GRAVITY = 9.81

STABILITY_ORDER = ["Stable", "Neutral", "Unstable"]
STABILITY_ORDER_5CAT = ["strongly unstable", "unstable", "neutral", "stable", "strongly stable"]

COLOR_STABLE = "#ED7D31"
COLOR_UNSTABLE = "#FFC000"
COLOR_NEUTRAL_HOURLY = "#4472C4"
COLOR_NEUTRAL_WSBIN = "#A5A5A5"
COLOR_WINDSPEED = "#A5A5A5"
COLOR_DAY = "#4472C4"
COLOR_NIGHT = "#ED7D31"
COLOR_GRID = "#E3E6EA"
COLOR_TEXT = "#33414E"

REQUIRED_COLUMNS = [
    "Date/Time",
    "Ch2_Speed_59m_E [m/s]",
    "Ch2_Speed_59m_E_SD [m/s]",
    "Ch6_Speed_22m_E [m/s]",
    "Ch6_Speed_22m_E_SD [m/s]",
    "Ch16_Temperature_59m_N [°C]",
    "Ch16_Temperature_59m_N_SD [°C]",
    "Ch15_Temperature_22m_N [°C]",
    "Ch15_Temperature_22m_N_SD [°C]",
]
NUMERIC_COLUMNS = [c for c in REQUIRED_COLUMNS if c != "Date/Time"]