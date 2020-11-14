"""Define classes that return Altair/Plotly/Matplotlib figures
"""
from typing import List

import altair as alt
import pandas as pd
import plotly.express as px
import plotly.io as pio

from src.constants import *
from src.diagnostics import DiagnoseTypes

pio.templates.default = "plotly_white"


def visualize_detected(diagnostic: DiagnoseTypes) -> alt.Chart:
    """Plot all records diagnosed as positive.

    Parameters
    ----------
    diagnostic
        A Diagnostic class

    Returns
    -------
    callable
        An Altair chart
    """
    # TODO: check speed when over 5000 elements
    source = diagnostic.data.copy()
    chart = (
        alt.Chart(source)
        .mark_point(filled=True)
        .encode(
            x=alt.X(f"{SAMPLE_TIME}:T", title="Date"),
            y=alt.Y(f"{VALUE}:Q", title="value"),
            color=alt.Color(f"{DETECTION}:N", scale=alt.Scale(domain=[0, 1])),
            opacity=alt.condition(alt.datum[DETECTION], alt.value(1.0), alt.value(0.2)),
            row=alt.Row(f"{P_CODE}:N", title=""),
            tooltip=[PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
        )
        .interactive()
    )
    return chart


def visualize_detected_by_patient(
    diagnostic: DiagnoseTypes, detected_patient_ids: str
) -> alt.Chart:
    """Plot all records for the list of patient_ids. Each patient_id should all have one positive diagnostic.

    Parameters
    ----------
    diagnostic
        A Diagnostic class

    detected_patient_ids
        List of patient_ids with at least a positive diagnostic

    Returns
    -------
    callable
        An Altair chart
    """
    source = diagnostic.data.copy()
    source = source[source[PATIENT_ID].isin(detected_patient_ids)]

    chart = (
        alt.Chart(source)
        .mark_point(filled=True, size=80)
        .encode(
            x=alt.X(f"{SAMPLE_TIME}:T", title="Date"),
            y=alt.Y(f"{VALUE}:Q", title="value"),
            color=alt.Color(f"{PATIENT_ID}:N", title="Patient ID"),
            row=alt.Row(f"{P_CODE}:N", title=""),
            tooltip=[PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
        )
        .interactive()
    )
    return chart


def visualize_patient(diagnostic: DiagnoseTypes, patient_id: str) -> alt.Chart:
    """Plot all records for the given patient_id, with color by diagnostic result.
    The ID should have at least one positive diagnostic.

    Parameters
    ----------
    diagnostic
        A Diagnostic class

    patient_id
        A patient_id that has a positive diagnostic

    Returns
    -------
    callable
        An Altair chart
    """
    source = diagnostic.data.copy()
    source = source[source[PATIENT_ID] == patient_id]
    base = alt.Chart(source).encode(
        x=alt.X(f"{SAMPLE_TIME}:T", title="Date"),
        y=alt.Y(f"{VALUE}:Q", title="value"),
        tooltip=[PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
    )
    line = base.mark_line(size=1)
    points = base.mark_point(filled=True, size=90).encode(
        color=alt.Color(f"{DETECTION}:N", scale=alt.Scale(domain=[0, 1]))
    )
    chart = (line + points).facet(row=f"{P_CODE}:N").interactive()
    return chart


def visualize_summary_detection(diagnostics: List[DiagnoseTypes]) -> alt.Chart:
    """Plot number of positive/negative patient IDS per diagnostic

    Parameters
    ----------
    diagnostics
        A diagnostic instance.

    Returns
    -------
        Altair chart
    """

    def format_row(diagnostic: DiagnoseTypes):
        n_patients = len(diagnostic.data[PATIENT_ID].unique())
        n_patients_with_positive = len(
            diagnostic.data.loc[diagnostic.data["detection"] == 1, PATIENT_ID].unique()
        )
        row = {
            "name": diagnostic.name,
            "patients with all negative diagnostic": n_patients
            - n_patients_with_positive,
            "patients with one positive diagnostic": n_patients_with_positive,
        }
        return row

    rows = [format_row(diagnostic) for diagnostic in diagnostics]

    source = pd.DataFrame(rows).melt(
        id_vars="name", var_name="type", value_name="number_of_patients"
    )
    chart = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x=alt.X("number_of_patients:Q", title="Number of patients"),
            y=alt.Y("name:N", title="Diagnostic", axis=alt.Axis(labelAngle=0)),
            color=alt.Color("type:N", sort=["ok", "detected"]),
            tooltip=["name", "type", "number_of_patients"],
        )
        .properties(title="Summary report")
        .interactive()
    )
    return chart


def beta_visualize_dme(samples_with_treatment_no: pd.DataFrame, nopho_nr):
    data = samples_with_treatment_no[
        (samples_with_treatment_no[P_CODE] == "NPU02739")
        & (samples_with_treatment_no[PATIENT_ID] == nopho_nr)
    ].copy()
    data[INFUSION_NO] = data[INFUSION_NO].astype(str)
    fig = (
        px.scatter(
            data,
            x=DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE,
            y=VALUE,
            color=INFUSION_NO,
            hover_data=[
                PATIENT_ID,
                INFUSION_NO,
                SAMPLE_TIME,
                INF_STARTDATE,
                DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE,
                VALUE,
            ],
        )
        .update_traces(mode="lines+markers", marker=dict(size=6), line=dict(width=1))
        .update_layout(yaxis_type="log")
    )
    return fig
