from typing import List

import pandas as pd
import streamlit as st

from src.constants import *
from src.dataset import generate_download_link, load_data
from src.diagnostics import DiagnoseTypes, DiagnosticClasses
from src.visualization import (
    visualize_detected,
    visualize_detected_by_patient,
    visualize_patient,
    visualize_summary_detection,
)


def main():
    initialize_headers()
    xlsx_file_buffer = st.sidebar.file_uploader("Choose your Excel file", type=["xlsx"])

    if xlsx_file_buffer is None:
        return

    df = load_data(xlsx_file_buffer)
    build_data_preview(df)

    selected_diagnostics = st.sidebar.multiselect(
        "Choose the diagnostics you want to study",
        options=range(0, len(DiagnosticClasses)),
        format_func=lambda i: DiagnosticClasses[i].name,
    )

    diagnostics = init_diagnostics(df, selected_diagnostics)
    run_diagnostics(diagnostics)

    if len(selected_diagnostics) != 0:
        visualize_summary(diagnostics)
        generate_download(diagnostics)

    for diagnostic_data in diagnostics:
        visualize_diagnostic_samples(diagnostic_data)

        detected_positive_patient_ids = diagnostic_data.get_detected_ids()
        if len(detected_positive_patient_ids) == 0:
            continue

        visualize_diagnostic_positive_samples(
            diagnostic_data, detected_positive_patient_ids
        )
        visualize_diagnostic_patient(diagnostic_data, detected_positive_patient_ids)

        st.markdown("---")


def initialize_headers():
    """Write Streamlit main panel and sidebar titles
    """
    st.title("MTX App")
    st.markdown(
        "Graphs are interactive, scroll them to zoom or double-click to reset view"
    )
    st.markdown("---")
    st.sidebar.header("Configuration")


def build_data_preview(df: pd.DataFrame):
    """Display Streamlit checkbox to preview the input Dataframe
    """
    if st.sidebar.checkbox("Data preview"):
        st.subheader("Previewing the first 100 rows")
        st.dataframe(df[:100])


def init_diagnostics(
    df: pd.DataFrame, list_diagnostic_indices: List[int]
) -> List[DiagnoseTypes]:
    """For each index in list_diagnostic_indices, initialize an instance of Diagnostic class with the data
    """
    return [
        DiagnosticClasses[selected_diagnostic_index](df)
        for selected_diagnostic_index in list_diagnostic_indices
    ]


def run_diagnostics(list_diagnostics: List[DiagnoseTypes]):
    """For each diagnostic instance, link Streamlit parameters in sidebar sliders to internal processing state
    Then run diagnostic logic to build DETECTION column
    """
    for diagnostic_data in list_diagnostics:
        diagnostic_data.update_params_in_sidebar()
        diagnostic_data.run_detection()


def visualize_summary(diagnostics: List[DiagnoseTypes]):
    st.header("Summary of diagnostics")
    st.altair_chart(visualize_summary_detection(diagnostics), use_container_width=True)


def visualize_diagnostic_samples(diagnostic_data: DiagnoseTypes):
    st.header(diagnostic_data.name)
    st.subheader("Visualize all samples")
    if st.checkbox("View", True, key=f"{diagnostic_data.name}_checkbox_all_samples"):
        st.altair_chart(visualize_detected(diagnostic_data), use_container_width=True)


def visualize_diagnostic_positive_samples(
    diagnostic_data: DiagnoseTypes, detected_patient_ids: List[str]
):
    st.subheader("Visualize all positive samples")
    if st.checkbox("View", key=f"{diagnostic_data.name}_checkbox_detected_samples"):
        st.altair_chart(
            visualize_detected_by_patient(diagnostic_data, detected_patient_ids),
            use_container_width=True,
        )


def visualize_diagnostic_patient(
    diagnostic_data: DiagnoseTypes, detected_patient_ids: List[str]
):
    st.subheader("Visualize samples for a specific patient")
    if st.checkbox("View", key=f"{diagnostic_data.name}_checkbox_patient_id"):
        selected_patient_id = st.selectbox(
            "Choose a detected patient ID (you can paste the ID you need) : ",
            detected_patient_ids,
            key=f"{diagnostic_data.name}_patient_id_slider",
        )
        st.altair_chart(
            visualize_patient(diagnostic_data, selected_patient_id),
            use_container_width=True,
        )


def generate_download(diagnostics: List[DiagnoseTypes]):
    all_dfs = (
        pd.concat([d.data[[PATIENT_ID, DETECTION]] for d in diagnostics])
        .groupby(PATIENT_ID)[DETECTION]
        .agg(PHONOTYPE=(DETECTION, "max"))
        .reset_index()
    )
    all_dfs["PHONOTYPE"] = all_dfs["PHONOTYPE"].astype(int)
    st.markdown(f"Number of patients in diagnostics : {len(all_dfs)}")
    st.markdown(
        f"Number of patients with positive phenotype : {len(all_dfs[all_dfs['PHONOTYPE'] == 1])}"
    )
    st.markdown(
        f"Number of patients with negative phenotype : {len(all_dfs[all_dfs['PHONOTYPE'] == 0])}"
    )

    st.markdown(generate_download_link(all_dfs), unsafe_allow_html=True)
    st.markdown("---")


if __name__ == "__main__":
    main()