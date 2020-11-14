import base64
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st

from src.constants import *


@st.cache
def load_samples(xlsx_file_buffer: StringIO) -> pd.DataFrame:
    """Load file with blood samples"""

    def date_parser(d):
        return datetime.strptime(d, "%d/%m/%Y %H.%M")

    df = pd.read_excel(
        xlsx_file_buffer,
        parse_dates=[SAMPLE_TIME],
        date_parser=date_parser,
    )
    df = df.dropna(subset=[PATIENT_ID])
    df[PATIENT_ID] = df[PATIENT_ID].astype(int)
    df = df.drop(columns=["Unnamed: 0"])
    return df


@st.cache
def load_infusion_times(xlsx_file_buffer: StringIO) -> pd.DataFrame:
    """Load file with infusion times"""
    mtx_infusion_time = pd.read_excel(
        xlsx_file_buffer,
        usecols=[PATIENT_ID, INFUSION_NO, SEX, MP6_STOP, INF_STARTDATE, INF_STARTHOUR],
    )
    # Cheat: we extract the hour from INF_STARTHOUR
    # and inject this hour into INF_STARTDATE which has an hour of 00:00:00
    mtx_infusion_time[INF_STARTDATE] = (
        mtx_infusion_time[INF_STARTDATE].dt.strftime("%d-%m-%Y")
        + " "
        + mtx_infusion_time[INF_STARTHOUR]
    )
    mtx_infusion_time[INF_STARTDATE] = pd.to_datetime(
        mtx_infusion_time[INF_STARTDATE], format="%d-%m-%Y %H:%M:%S"
    )
    mtx_infusion_time = mtx_infusion_time.drop([INF_STARTHOUR], axis=1)
    mtx_infusion_time[PATIENT_ID] = mtx_infusion_time[PATIENT_ID].astype(int)
    mtx_infusion_time[INFUSION_NO] = mtx_infusion_time[INFUSION_NO].astype(str)

    return mtx_infusion_time


@st.cache(suppress_st_warning=True)
def remove_patients_with_duplicate_treatments(
    infusion_times: pd.DataFrame,
) -> pd.DataFrame:
    """Some patients have repeated INFNO treatment numbers, let's remove those patients for now"""
    df = infusion_times.copy()
    count_treatment_per_id = (
        df[PATIENT_ID].astype(str) + "_" + df[INFUSION_NO]
    ).value_counts()
    ids_with_duplicate_treatments = {
        s.split("_")[0]
        for s in count_treatment_per_id[count_treatment_per_id > 1].index.values
    }
    if len(ids_with_duplicate_treatments) != 0:
        st.warning(
            f"Patients have duplicate number treatments in infusion times "
            f"and were removed: {ids_with_duplicate_treatments}"
        )
    return df[~df[PATIENT_ID].isin(ids_with_duplicate_treatments)]


@st.cache
def merge_samples_to_treatment(samples_df, infusion_times_df):
    # Now that infusion times have no duplicates
    # We can pivot the infusion times dataset to make it easier to join to samples
    # Numeric columns are now INFNO: number of treatment
    pivot_infusion_times = infusion_times_df.pivot(
        index=PATIENT_ID, columns=INFUSION_NO, values=INF_STARTDATE
    ).reset_index()

    samples_with_infusion_times = samples_df.merge(
        pivot_infusion_times, on=PATIENT_ID, how="left", indicator=True
    )
    samples_with_infusion_times["_merge"] = samples_with_infusion_times[
        "_merge"
    ].astype(str)

    def date_to_treatment_no(s: pd.Series):
        if s["_merge"] == "left_only":
            return [None, None, None]
        elif not pd.isnull(s["8"]) and s[SAMPLE_TIME] > s["8"]:
            return [8, s["8"], s[SAMPLE_TIME] - s["8"]]
        elif not pd.isnull(s["7"]) and s[SAMPLE_TIME] > s["7"]:
            return [7, s["7"], s[SAMPLE_TIME] - s["7"]]
        elif not pd.isnull(s["6"]) and s[SAMPLE_TIME] > s["6"]:
            return [6, s["6"], s[SAMPLE_TIME] - s["6"]]
        elif not pd.isnull(s["5"]) and s[SAMPLE_TIME] > s["5"]:
            return [5, s["5"], s[SAMPLE_TIME] - s["5"]]
        elif not pd.isnull(s["4"]) and s[SAMPLE_TIME] > s["4"]:
            return [4, s["4"], s[SAMPLE_TIME] - s["4"]]
        elif not pd.isnull(s["3"]) and s[SAMPLE_TIME] > s["3"]:
            return [3, s["3"], s[SAMPLE_TIME] - s["3"]]
        elif not pd.isnull(s["2"]) and s[SAMPLE_TIME] > s["2"]:
            return [2, s["2"], s[SAMPLE_TIME] - s["2"]]
        elif not pd.isnull(s["1"]) and s[SAMPLE_TIME] > s["1"]:
            return [1, s["1"], s[SAMPLE_TIME] - s["1"]]
        elif not pd.isnull(s["1"]) and s[SAMPLE_TIME] < s["1"]:
            return [0, s["1"], s[SAMPLE_TIME] - s["1"]]
        else:
            return [None, None, None]

    # TODO: this apply method is probably the slowest of the app, can we vectorize this ?
    samples_with_infusion_times[
        [INFUSION_NO, INF_STARTDATE, DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE]
    ] = samples_with_infusion_times.apply(
        date_to_treatment_no, axis=1, result_type="expand"
    )
    samples_with_infusion_times[
        DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE
    ] = samples_with_infusion_times[DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE].astype(
        "timedelta64[h]"
    )

    samples_with_infusion_times = samples_with_infusion_times.drop(columns=["_merge"])

    # integrate MP6_stop and SEX separately so we can filter inaccurate data
    sex_per_patient = infusion_times_df.loc[infusion_times_df[SEX] != 0, [PATIENT_ID, SEX]].drop_duplicates()
    samples_with_infusion_times = samples_with_infusion_times.merge(sex_per_patient, on=PATIENT_ID)

    MP6_per_patient_treatment = infusion_times_df[[PATIENT_ID, INFUSION_NO, MP6_STOP]].drop_duplicates()
    MP6_per_patient_treatment[INFUSION_NO] = MP6_per_patient_treatment[INFUSION_NO].astype(float)
    samples_with_infusion_times = samples_with_infusion_times.merge(MP6_per_patient_treatment, on=[PATIENT_ID, INFUSION_NO])

    return samples_with_infusion_times


def generate_download_link(df: pd.DataFrame) -> str:
    csv_file = df.to_csv(index=False, sep=";")
    b64 = base64.b64encode(csv_file.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
