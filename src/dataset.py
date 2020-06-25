import base64
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st

from src.constants import *


@st.cache
def load_data(xlsx_file_buffer: StringIO) -> pd.DataFrame:
    def date_parser(d):
        return datetime.strptime(d, "%d/%m/%Y %H.%M")

    df = pd.read_excel(
        xlsx_file_buffer, parse_dates=[SAMPLE_TIME], date_parser=date_parser,
    )
    df = df.dropna(subset=[PATIENT_ID])
    df[PATIENT_ID] = df[PATIENT_ID].astype(int)
    df = df.drop(columns=["Unnamed: 0"])
    return df


def generate_download_link(df: pd.DataFrame) -> str:
    csv_file = df.to_csv(index=False, sep=";")
    b64 = base64.b64encode(csv_file.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}">Download CSV File</a> (right-click and save as &lt;some_name&gt;.csv)'
