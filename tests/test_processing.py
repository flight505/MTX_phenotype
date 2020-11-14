import pandas as pd

from pandas.testing import assert_series_equal

from src.constants import *
from src.processing import compute_streaks_of_detection
from src.processing import is_streak_longer_than_duration


def test_compute_streaks():
    data = {
        PATIENT_ID: [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        DETECTION: [False, False, True, True, True, True, True, False, True, True],
        SAMPLE_TIME: [
            # Patient 0
            pd.Timestamp("1970-01-01 00:00:00"),  # streak 1
            pd.Timestamp("1970-01-01 01:00:00"),  # streak 1
            pd.Timestamp("1970-01-01 02:00:00"),  # streak 2
            pd.Timestamp("1970-01-01 03:00:00"),  # streak 2
            pd.Timestamp("1970-01-01 04:00:00"),  # streak 2
            # Patient 1
            pd.Timestamp("1970-01-01 00:00:00"),  # streak 1
            pd.Timestamp("1970-01-01 01:00:00"),  # streak 1
            pd.Timestamp("1970-01-01 02:00:00"),  # streak 2
            pd.Timestamp("1970-01-01 03:00:00"),  # streak 3
            pd.Timestamp("1970-01-01 04:00:00"),  # streak 3
        ],
    }
    df = pd.DataFrame(data)
    streaks = compute_streaks_of_detection(df, DETECTION, PATIENT_ID, SAMPLE_TIME)
    assert_series_equal(
        streaks, pd.Series([1, 1, 2, 2, 2, 1, 1, 2, 3, 3], name="streak_id")
    )


def test_is_streak_longer_than_duration():
    data = {
        PATIENT_ID: [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        DETECTION: [True, True, True, True, False, True, True, False, True, True],
        SAMPLE_TIME: [
            # Patient 0
            pd.Timestamp("1970-01-01 00:00:00"),  # streak 1 -> streak of 3h
            pd.Timestamp("1970-01-01 01:00:00"),  # streak 1 -> streak of 3h
            pd.Timestamp("1970-01-01 02:00:00"),  # streak 1 -> streak of 3h
            pd.Timestamp("1970-01-01 03:00:00"),  # streak 1 -> streak of 3h
            pd.Timestamp("1970-01-01 04:00:00"),  # streak 2
            # Patient 1
            pd.Timestamp("1970-01-01 00:00:00"),  # streak 1 -> negative long streak
            pd.Timestamp("1970-01-01 04:00:00"),  # streak 1 -> negative long streak
            pd.Timestamp("1970-01-01 08:00:00"),  # streak 2
            pd.Timestamp("1970-01-01 09:00:00"),  # streak 3 -> streak of 4h
            pd.Timestamp("1970-01-01 13:00:00"),  # streak 3 -> streak of 4h
        ],
    }
    df = pd.DataFrame(data)
    long_streaks = is_streak_longer_than_duration(
        df, DETECTION, PATIENT_ID, SAMPLE_TIME, 2
    )
    assert_series_equal(
        long_streaks,
        pd.Series(
            [True, True, True, True, False, True, True, False, True, True]
        ), check_names=False
    )
