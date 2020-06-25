"""Helper class to compute diagnostics on input dataframe
"""
from datetime import datetime

import numpy as np
import pandas as pd


def compute_streaks_of_detection(
    df: pd.DataFrame,
    column_variable: str,
    column_patient_id: str,
    column_date: datetime,
):
    """Compute streaks of column_variable column
    """
    df = df.sort_values([column_patient_id, column_date])
    df["shifted_detection"] = df.groupby(column_patient_id)[column_variable].shift(1)
    df["start_of_streak"] = df[column_variable].ne(df[f"shifted_{column_variable}"])
    df["streak_id"] = df.groupby(column_patient_id)["start_of_streak"].cumsum()
    return df["streak_id"]


def is_streak_longer_than_duration(
    df: pd.DataFrame,
    column_variable: str,
    column_patient_id: str,
    column_date: str,
    longer_than_n_hours: int,
):
    """Get duration of each streak of successive values in column_variable column,
    and return True if duration exceeds longer_than_n_hours, False otherwise, in a new column.

    column_variable is generally the detection variable so we see if long streak of positive diagnostic
    """
    data = df.copy()
    data["streak_id"] = compute_streaks_of_detection(
        data, column_variable, column_patient_id, column_date
    )

    # Group elements in the same streak together to compute duration of streak and if it's a positive or negative one
    group_streaks_by_patient = (
        data.groupby([column_patient_id, "streak_id"])[[column_date, column_variable]]
        .agg(
            min_date=(column_date, "min"),
            max_date=(column_date, "max"),
            is_streak_positive=(column_variable, "first"),
        )
        .reset_index()
    )
    group_streaks_by_patient["streak_duration"] = (
        group_streaks_by_patient["max_date"] - group_streaks_by_patient["min_date"]
    ) / np.timedelta64(1, "h")

    group_streaks_by_patient[column_variable] = (
        group_streaks_by_patient["streak_duration"] > longer_than_n_hours
    ) & group_streaks_by_patient["is_streak_positive"]

    # Left join the data with the table of long positive streaks
    res = (
        data.reset_index()
        .merge(
            group_streaks_by_patient, on=[column_patient_id, "streak_id"], how="left"
        )
        .set_index("index")
    )

    return res[f"{column_variable}_x"] & res[f"{column_variable}_y"]
