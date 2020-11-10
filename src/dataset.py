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


def load_infusion_times(xlsx_file_buffer: StringIO) -> pd.DataFrame:
    """Load file with infusion times"""
    mtx_infusion_time = pd.read_excel(
        xlsx_file_buffer,
        usecols=[PATIENT_ID, INFUSION_NO, INF_STARTDATE, INF_STARTHOUR],
    )
    # Cheat: we extract the hour from INF_STARTHOUR, which in current Excel file have a fake date prefixed
    # and inject this hour into INF_STARTDATE which has an hour of 00:00:00
    mtx_infusion_time[INF_STARTDATE] = (
        mtx_infusion_time[INF_STARTDATE].dt.strftime("%d/%m/%Y")
        + " "
        + mtx_infusion_time[INF_STARTHOUR].dt.strftime("%H:%M:%S")
    )
    mtx_infusion_time[INF_STARTDATE] = pd.to_datetime(
        mtx_infusion_time[INF_STARTDATE], format="%d/%m/%Y %H:%M:%S"
    )
    mtx_infusion_time = mtx_infusion_time.drop([INF_STARTHOUR], axis=1)
    mtx_infusion_time[PATIENT_ID] = mtx_infusion_time[PATIENT_ID].astype(int)
    mtx_infusion_time[INFUSION_NO] = mtx_infusion_time[INFUSION_NO].astype(str)

    return mtx_infusion_time


def remove_patients_with_duplicate_treatments(infusion_times: pd.DataFrame) -> pd.DataFrame:
    """Some patients have repeated INFNO treatment numbers, let's remove them for now"""
    df = infusion_times.copy()
    count_treatment_per_id = (df[PATIENT_ID].astype(str) + "_" + df[INFUSION_NO]).value_counts()
    ids_with_duplicate_treatments = {
        s.split("_")[0]
        for s in count_treatment_per_id[count_treatment_per_id > 1].index.values
    }
    print(
        "BEWARE: some patients have duplicate number treatments in infusion times and were removed: ",
        ids_with_duplicate_treatments
    )
    return df[~df[PATIENT_ID].isin(ids_with_duplicate_treatments)]


def generate_download_link(df: pd.DataFrame) -> str:
    csv_file = df.to_csv(index=False, sep=";")
    b64 = base64.b64encode(csv_file.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
