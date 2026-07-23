import pandas as pd
from src.constants import NUMERIC_COLUMNS

def validate_upload(df: pd.DataFrame):
    errors = []

    if df is None or df.shape[1] == 0:
        errors.append("The uploaded file has no readable columns. Please check the file and try again.")
        return errors

    if df.empty:
        errors.append("The uploaded file is empty - it contains headers but no data rows.")
        return errors

    return errors


def sanitize_numeric_columns(df: pd.DataFrame):
    out = df.copy()
    invalid_counts = {}
    for col in NUMERIC_COLUMNS:
        if col not in out.columns:
            continue
        before_na = out[col].isna().sum()
        out[col] = pd.to_numeric(out[col], errors="coerce")
        after_na = out[col].isna().sum()
        invalid_counts[col] = int(after_na - before_na)
    return out, invalid_counts


def data_quality_summary(df: pd.DataFrame):
    total = len(df)
    counts = {
        "Invalid or unreadable Date/Time": int(df["Date/Time"].isna().sum()) if "Date/Time" in df else 0,
        "Ri - missing inputs or zero wind-speed difference": int(df["Ri"].isna().sum()) if "Ri" in df else 0,
        "Shear - missing or non-positive wind speed": int(df["Shear"].isna().sum()) if "Shear" in df else 0,
        "TI - zero or missing wind speed": int(df["TI"].isna().sum()) if "TI" in df else 0,
        "WS120 - missing shear": int(df["WS120"].isna().sum()) if "WS120" in df else 0,
        "Delta T - missing temperature": int(df["Delta T"].isna().sum()) if "Delta T" in df else 0,
    }
    return counts, total