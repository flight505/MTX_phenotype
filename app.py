from typing import List

import pandas as pd
import streamlit as st

from src.constants import *
from src.dataset import generate_download_link
from src.dataset import load_infusion_times
from src.dataset import load_samples
from src.dataset import merge_samples_to_treatment
from src.dataset import remove_patients_with_duplicate_treatments
from src.diagnostics import DiagnoseTypes
from src.diagnostics import DiagnosticClasses
from src.visualization import visualize_detected
from src.visualization import visualize_detected_by_patient
from src.visualization import visualize_patient
from src.visualization import visualize_summary_detection


def main():
    initialize_headers()
    samples_df_buffer = st.sidebar.file_uploader(
        "Choose your samples file", type=["xlsx"]
    )
    infusion_times_buffer = st.sidebar.file_uploader(
        "Choose your infusion times file", type=["xlsx"]
    )

    if samples_df_buffer is None or infusion_times_buffer is None:
        st.info("Please specify samples and infusion time files in the sidebar")
        return

    # Reset file upload buffers to read the data again
    # https://discuss.streamlit.io/t/create-multiple-dataframes-from-csv-files-loaded-via-the-multi-file-uploader/6258/4
    samples_df_buffer.seek(0)
    infusion_times_buffer.seek(0)

    samples_df = load_samples(samples_df_buffer)
    infusion_times = load_infusion_times(infusion_times_buffer)

    # Careful ! Maybe some NOPHO_NR have duplicate INFNO at different dates.
    # Let's just filter them for now and log them in console
    clean_infusion_times = remove_patients_with_duplicate_treatments(infusion_times)

    # Merge samples to treatment times and define treatment number
    samples_with_treatment_no = merge_samples_to_treatment(
        samples_df, clean_infusion_times
    )
    preview_sample(
        samples_with_treatment_no[samples_with_treatment_no[INFUSION_NO] > 0]
    )

    selected_diagnostics = st.sidebar.multiselect(
        "Choose the diagnostics you want to study",
        options=range(0, len(DiagnosticClasses)),
        format_func=lambda i: DiagnosticClasses[i].name,
    )

    diagnostics = init_diagnostics(samples_with_treatment_no, selected_diagnostics)
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
    """Write Streamlit main panel and sidebar titles"""
    st.title("MTX App")
    st.markdown(
        "Graphs are interactive, scroll them to zoom or double-click to reset view"
    )
    st.sidebar.header("Configuration")


def preview_sample(df: pd.DataFrame):
    with st.beta_expander("Preview a random sample of 100 elements"):
        st.markdown("Samples data")
        st.dataframe(df.sample(100))


def init_diagnostics(
    df: pd.DataFrame, list_diagnostic_indices: List[int]
) -> List[DiagnoseTypes]:
    """For each index in list_diagnostic_indices, initialize an instance of Diagnostic class with the data"""
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
    st.altair_chart(visualize_summary_detection(diagnostics), use_container_width=True)


def visualize_diagnostic_samples(diagnostic_data: DiagnoseTypes):
    st.header(diagnostic_data.name)
    with st.beta_expander("Visualize all samples"):
        st.altair_chart(visualize_detected(diagnostic_data), use_container_width=True)


def visualize_diagnostic_positive_samples(
    diagnostic_data: DiagnoseTypes, detected_patient_ids: List[str]
):
    with st.beta_expander("Visualize all positive samples"):
        st.altair_chart(
            visualize_detected_by_patient(diagnostic_data, detected_patient_ids),
            use_container_width=True,
        )


def visualize_diagnostic_patient(
    diagnostic_data: DiagnoseTypes, detected_patient_ids: List[str]
):
    with st.beta_expander("Visualize samples for a specific patient"):
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
        .agg("max")
        .reset_index()
        .rename(columns={DETECTION: "PHONOTYPE"})
    )
    all_dfs["PHONOTYPE"] = all_dfs["PHONOTYPE"].astype(int)
    st.markdown(
        f"""
    * Number of patients in diagnostics : {len(all_dfs)}
    * Number of patients with positive phenotype : {len(all_dfs[all_dfs['PHONOTYPE'] == 1])}
    * Number of patients with negative phenotype : {len(all_dfs[all_dfs['PHONOTYPE'] == 0])}
    """
    )
    with st.beta_expander("Generate download link"):
        st.markdown(generate_download_link(all_dfs), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
