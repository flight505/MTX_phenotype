"""Define classes which contain processing logic for diagnostics.

They expose Streamlit sliders to update their diagnostic detection
"""
from abc import ABC, abstractmethod
from typing import List, Union

import pandas as pd
import streamlit as st

from src.constants import *
from src.processing import is_streak_longer_than_duration


class AbstractDiagnose(ABC):
    """Any diagnostic should inherit from this class so main panel only need to use functions from the base class.
    It's a component which links Streamlit sliders to it's data and diagnostic logic.
    """

    def __init__(self):
        """For each diagnostic we'd like to only store the necessary subset of data."""
        self.data: pd.DataFrame = pd.DataFrame()

    @abstractmethod
    def update_params_in_sidebar(self) -> None:
        """This method displays/updates Streamlit sliders inside the Streamlit sidebar.
        Those should be linked to the diagnostic processing logic
        """
        pass

    @abstractmethod
    def run_detection(self) -> None:
        """Compute detections given Streamlit slider params

        This function is stateful and computes the DETECTION column to self.data.
        This column contains the diagnostic result as a boolean value.
        """
        pass

    def get_detected_ids(self) -> List[str]:
        """Return

        Returns
        -------
        A list of patient_ids with at least one positive diagnostic
        """
        if DETECTION not in self.data.columns:
            st.warning("Detection not found, did you compute it ?")
            return []
        d = self.data.groupby(PATIENT_ID)[DETECTION].max().reset_index()

        detected_positive_patient_ids = d.loc[d[DETECTION] == 1, PATIENT_ID].tolist()
        return detected_positive_patient_ids


class Diagnose1(AbstractDiagnose):
    name: str = "Neutropenia (NPU02902) Neutrofilocytter"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df.loc[
            df[P_CODE] == "NPU02902", [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE]
        ]
        self.param_concentration: st.DeltaGenerator = st.empty
        self.param_days: st.DeltaGenerator = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.param_concentration = st.sidebar.slider(
            "Concentration NPU02902 < threshold",
            min_value=0.0,
            max_value=10.0,
            value=0.5,
            step=0.1,
            format="%.1f x10^9 /L",
            key="D1c",
        )
        self.param_days = st.sidebar.slider(
            "> Number of days",
            min_value=0,
            max_value=30,
            value=10,
            step=1,
            format="%d days",
            key="D1d",
        )

    def run_detection(self):
        self.data[DETECTION] = self.data[VALUE] < self.param_concentration
        self.data[DETECTION] = is_streak_longer_than_duration(
            self.data, DETECTION, PATIENT_ID, SAMPLE_TIME, 24 * self.param_days
        ).astype(bool)


class Diagnose2(AbstractDiagnose):
    name: str = "Severe infection (NPU19748)"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df.loc[
            df[P_CODE] == "NPU19748",
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, REF_PATIENT],
        ]
        # clean REFTEXT which is mostly <8,0 to transform to 8.0
        # TODO : not checking how clean is the data !
        self.data[REF_PATIENT] = (
            self.data[REF_PATIENT]
            .apply(lambda n: n.replace("<", "").replace(",", "."))
            .astype(float)
        )
        self.param_concentration: st.DeltaGenerator = st.empty
        self.param_days: st.DeltaGenerator = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.param_concentration = st.sidebar.slider(
            "Concentration NPU19748 > threshold",
            min_value=0,
            max_value=400,
            value=100,
            step=10,
            format="%d mg/L",
            key="D2c",
        )
        self.param_days = st.sidebar.slider(
            "Days",
            min_value=0,
            max_value=180,
            value=7,
            step=1,
            format="%d days",
            key="D2d",
        )

    def run_detection(self) -> None:
        # CRP > threshold
        detection1 = self.data[[PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE]].copy()
        detection1[DETECTION] = self.data[VALUE] > self.param_concentration

        # or CRP > reftext for consecutive days
        # TODO : check "elevated" same as > reftext
        detection2 = self.data[
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, REF_PATIENT]
        ].copy()
        detection2[DETECTION] = detection2[VALUE] > detection2[REF_PATIENT]
        detection2[DETECTION] = is_streak_longer_than_duration(
            detection2, DETECTION, PATIENT_ID, SAMPLE_TIME, 24 * self.param_days
        )

        self.data[DETECTION] = (detection1[DETECTION] | detection2[DETECTION]).astype(
            bool
        )


class Diagnose3(AbstractDiagnose):
    name: str = "Neutropenia with infection"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df

    def update_params_in_sidebar(self):
        pass

    def run_detection(self) -> None:
        pass

    def get_detected_patients(self) -> List[str]:
        pass


class Diagnose4(AbstractDiagnose):
    name: str = "Severe hepatic effects elevated liver enzyme (NPU19651)"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df.loc[
            df[P_CODE].isin(["NPU19651", "NPU01684", "NPU01370"]),
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE],
        ]
        self.param_concentration_liver: st.DeltaGenerator = st.empty
        self.param_concentration_koagulation: st.DeltaGenerator = st.empty
        self.param_concentration_bilirubin: st.DeltaGenerator = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.param_concentration_liver = st.sidebar.slider(
            "Concentration NPU19651 > threshold",
            min_value=0,
            max_value=100,
            value=45,
            step=1,
            format="%d U/I",
            key="D4l",
        )
        self.param_concentration_koagulation = st.sidebar.slider(
            "Ratio affected NPU01684 < threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            step=0.11,
            key="D4l",
        )
        self.param_concentration_bilirubin = st.sidebar.slider(
            "Concentration NPU01370 > threshold",
            min_value=0,
            max_value=100,
            value=40,
            step=1,
            format="%d μm",
            key="D4l",
        )

    def run_detection(self) -> None:
        # study NPU19651
        detection1 = self.data.loc[
            self.data[P_CODE] == "NPU19651",
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE],
        ].copy()
        detection1[DETECTION] = detection1[VALUE] > self.param_concentration_liver
        detection1 = detection1[[PATIENT_ID, SAMPLE_TIME, DETECTION]]

        # study NPU01684 or NPU01370
        detection2 = self.data.loc[
            self.data[P_CODE].isin(["NPU01684", "NPU01370"]),
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE],
        ].copy()
        detection2 = detection2.pivot_table(
            index=[PATIENT_ID, SAMPLE_TIME], columns=P_CODE, values=VALUE
        ).reset_index()
        detection2[DETECTION] = (
            detection2["NPU01684"] < self.param_concentration_koagulation
        ) | (detection2["NPU01370"] > self.param_concentration_bilirubin)
        detection2 = detection2[[PATIENT_ID, SAMPLE_TIME, DETECTION]]

        # merge detections, positive if positive for both detection1 and detection2 at same date
        detection = detection1.merge(
            detection2, on=[PATIENT_ID, SAMPLE_TIME], how="outer"
        )
        detection[DETECTION] = detection[f"{DETECTION}_x"] & detection[f"{DETECTION}_y"]
        detection = detection[[PATIENT_ID, SAMPLE_TIME, DETECTION]]

        # merge back to data
        self.data = self.data.merge(detection, on=[PATIENT_ID, SAMPLE_TIME], how="left")
        self.data[DETECTION] = self.data[DETECTION].astype(bool)


class Diagnose5(AbstractDiagnose):
    name: str = "Post-treatment toxicity in high-risk ALL"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df

    def update_params_in_sidebar(self):
        pass

    def run_detection(self) -> None:
        pass


class Diagnose6(AbstractDiagnose):
    name: str = "Renal toxicity (NPU18016)"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df.loc[
            df[P_CODE] == "NPU18016",
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE],
        ]
        self.param_concentration: st.DeltaGenerator = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.param_concentration = st.sidebar.slider(
            "Concentration NPU18016 > threshold",
            min_value=0,
            max_value=1000,
            value=150,
            step=10,
            format="%d μmol/L",
            key="D6c",
        )

    def run_detection(self) -> None:
        self.data[DETECTION] = (self.data[VALUE] > self.param_concentration).astype(
            bool
        )


class Diagnose7(AbstractDiagnose):
    name: str = "Plasma albumin and creatinine"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df

    def update_params_in_sidebar(self):
        pass

    def run_detection(self) -> None:
        pass


class Diagnose8(AbstractDiagnose):
    name: str = "Thrombocytopenia (NPU03568)"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df.loc[
            df[P_CODE] == "NPU03568",
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE],
        ]
        self.param_concentration: st.DeltaGenerator = st.empty
        self.param_hours: st.DeltaGenerator = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.param_concentration = st.sidebar.slider(
            "Concentration NPU03568 < threshold",
            min_value=0.0,
            max_value=50.0,
            value=10.0,
            step=0.1,
            format="%.1f x10^9 /L",
            key="D8c",
        )
        self.param_hours = st.sidebar.slider(
            "> Number of hours",
            min_value=24,
            max_value=24 * 5,
            value=24 * 3,
            step=1,
            format="%d hours",
            key="D8h",
        )

    def run_detection(self) -> None:
        self.data[DETECTION] = self.data[VALUE] < self.param_concentration
        self.data[DETECTION] = is_streak_longer_than_duration(
            self.data, DETECTION, PATIENT_ID, SAMPLE_TIME, self.param_hours
        ).astype(bool)


class Diagnose9(AbstractDiagnose):
    name: str = "Pankreatit"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.data: pd.DataFrame = df.loc[
            df[P_CODE].isin(["NPU19652", "NPU19653", "DNK05451", "NPU19748"]),
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE],
        ].dropna(subset=[VALUE])

        self.param_times: st.DeltaGenerator = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.param_times = st.sidebar.slider(
            "Threshold times over normal value",
            min_value=1.0,
            max_value=6.0,
            value=3.0,
            step=0.2,
            format="x%.1f",
            key="D9t",
        )

    def run_detection(self) -> None:
        detection = (
            self.data.copy()
            .pivot_table(index=[PATIENT_ID, SAMPLE_TIME], columns=P_CODE, values=VALUE)
            .reset_index()
        )

        NPU19652_normal_limit = 120
        NPU19653_normal_limit = 36
        DNK05451_normal_limit = 190
        NPU19748_normal_limit = 100

        detection[DETECTION] = (
            (detection["NPU19652"] > NPU19652_normal_limit * self.param_times)
            | (detection["NPU19653"] > NPU19653_normal_limit * self.param_times)
            | (detection["DNK05451"] > DNK05451_normal_limit * self.param_times)
        ) & (detection["NPU19748"] > NPU19748_normal_limit)

        detection = detection[[PATIENT_ID, SAMPLE_TIME, DETECTION]]
        self.data = self.data.merge(detection, on=[PATIENT_ID, SAMPLE_TIME], how="left")
        self.data[DETECTION] = self.data[DETECTION].astype(bool)


# choose classes to expose to main app
DiagnosticClasses = [Diagnose1, Diagnose2, Diagnose4, Diagnose6, Diagnose8, Diagnose9]
DiagnoseTypes = Union[Diagnose1, Diagnose2, Diagnose4, Diagnose6, Diagnose8, Diagnose9]
