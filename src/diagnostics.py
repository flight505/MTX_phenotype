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
            df[P_CODE] == "NPU02902", [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP]
        ]
        self.param_concentration = st.empty
        self.param_days = st.empty

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
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, REF_PATIENT, SEX, MP6_STOP],
        ]
        # clean REFTEXT which is mostly <8,0 to transform to 8.0
        # TODO : not checking how clean is the data !
        self.data[REF_PATIENT] = (
            self.data[REF_PATIENT]
            .apply(lambda n: n.replace("<", "").replace(",", "."))
            .astype(float)
        )
        self.param_concentration = st.empty
        self.param_days = st.empty

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
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
        ]
        self.param_concentration_liver = st.empty
        self.param_concentration_koagulation = st.empty
        self.param_concentration_bilirubin = st.empty

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
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
        ]
        self.param_concentration = st.empty

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
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
        ]
        self.param_concentration = st.empty
        self.param_hours = st.empty

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
            [PATIENT_ID, SAMPLE_TIME, P_CODE, VALUE, SEX, MP6_STOP],
        ].dropna(subset=[VALUE])

        self.param_times = st.empty

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


class DME(AbstractDiagnose):
    name: str = "DME"
    CREA_code: str = "NPU18016"
    MTX_code: str = "NPU02739"

    THRESHOLD_CREA_INCREASE_FROM_PREV_SAMPLE = (
        0.3 * 88.42
    )  # to convert mg/dl to μmol/l, multiply by 88.4
    THRESHOLD_CREA_INCREASE_ABOVE_BASELINE = 1.5
    THRESHOLD_MTX_36H = 20.0
    THRESHOLD_MTX_42H = 10.0
    THRESHOLD_MTX_48H = 2.0

    def __init__(self, df: pd.DataFrame):
        super().__init__()

        self.data: pd.DataFrame = (
            df.loc[
                (df[P_CODE].isin([self.CREA_code, self.MTX_code]))
                & (df[INFUSION_NO].notnull()),
                [
                    PATIENT_ID,
                    SAMPLE_TIME,
                    P_CODE,
                    VALUE,
                    INFUSION_NO,
                    DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE,
                    SEX,
                    MP6_STOP,
                ],
            ]
            .dropna(subset=[VALUE])
            .sort_values([PATIENT_ID, P_CODE, SAMPLE_TIME])
        )

        self.threshold_crea_previous_sample = st.empty
        self.threshold_crea_above_baseline = st.empty
        self.threshold_mtx_36h = st.empty
        self.threshold_mtx_42h = st.empty
        self.threshold_mtx_48h = st.empty

    def update_params_in_sidebar(self):
        st.sidebar.markdown(f"**Parameters for {self.name}**")
        self.threshold_crea_previous_sample = st.sidebar.slider(
            "Select threshold CREA increase compared to previous sample",
            0.0,
            5 * self.THRESHOLD_CREA_INCREASE_FROM_PREV_SAMPLE,
            self.THRESHOLD_CREA_INCREASE_FROM_PREV_SAMPLE,
        )
        self.threshold_crea_above_baseline = st.sidebar.slider(
            "Select threshold CREA increase fold above baseline",
            0.0,
            5 * self.THRESHOLD_CREA_INCREASE_ABOVE_BASELINE,
            self.THRESHOLD_CREA_INCREASE_ABOVE_BASELINE,
        )
        self.threshold_mtx_36h = st.sidebar.slider(
            "Select threshold MTX between 36h - 42h",
            0.0,
            5 * self.THRESHOLD_MTX_36H,
            self.THRESHOLD_MTX_36H,
        )
        self.threshold_mtx_42h = st.sidebar.slider(
            "Select threshold MTX between 42h - 48h",
            0.0,
            5 * self.THRESHOLD_MTX_42H,
            self.THRESHOLD_MTX_42H,
        )
        self.threshold_mtx_48h = st.sidebar.slider(
            "Select threshold MTX after 48h",
            0.0,
            5 * self.THRESHOLD_MTX_48H,
            self.THRESHOLD_MTX_48H,
        )

    def run_detection(self) -> None:

        # for baseline CREA, we take all samples before first infusion time, which is INFNO = 0
        # then patients have multiple values so we take the closest to first infusion
        # which is max value of difference time to infusion
        baseline_crea = self.data.loc[
            (self.data[P_CODE] == self.CREA_code) & (self.data[INFUSION_NO] == 0),
            [PATIENT_ID, VALUE, DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE],
        ]
        baseline_crea = baseline_crea.loc[
            baseline_crea.groupby(PATIENT_ID)[
                DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE
            ].idxmax(),
            [PATIENT_ID, VALUE],
        ].rename(columns={VALUE: "baseline_crea"})
        self.data = self.data.merge(baseline_crea, on=PATIENT_ID)

        # For criteria one, need to shift the data so previous sample is in current sample
        # by patient, treatment number and p_code
        self.data["prev_value"] = self.data.groupby([PATIENT_ID, INFUSION_NO, P_CODE])[
            VALUE
        ].shift()

        # Criteria 1 : Increase in plasma creatinine by > 0.3 compared to previous sample
        criteria_one = (
            (self.data[INFUSION_NO] != 0)
            & (self.data[P_CODE] == self.CREA_code)
            & (self.data["prev_value"].notnull())
            & (
                self.data[VALUE] - self.data["prev_value"]
                > self.threshold_crea_previous_sample
            )
        )

        # Criteria 2 : Increase of 1.5 fold above baseline
        criteria_two = (
            (self.data[INFUSION_NO] != 0)
            & (self.data[P_CODE] == self.CREA_code)
            & (
                self.data[VALUE] / self.data["baseline_crea"]
                > self.threshold_crea_above_baseline
            )
        )

        # Criteria 3 : between 36 and 42 hours > 20 µM
        criteria_three = (
            (self.data[INFUSION_NO] != 0)
            & (self.data[P_CODE] == self.MTX_code)
            & (self.data[DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE] >= 36)
            & (self.data[DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE] < 42)
            & (self.data[VALUE] > self.threshold_mtx_36h)
        )

        # Criteria 4 : between 42 and 48 hours > 10 µM
        criteria_four = (
            (self.data[INFUSION_NO] != 0)
            & (self.data[P_CODE] == self.MTX_code)
            & (self.data[DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE] >= 42)
            & (self.data[DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE] < 48)
            & (self.data[VALUE] > self.threshold_mtx_42h)
        )

        # Criteria 5 : longer than 48 hours > 3 µM
        criteria_five = (
            (self.data[INFUSION_NO] != 0)
            & (self.data[P_CODE] == self.MTX_code)
            & (self.data[DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE] > 48)
            & (self.data[VALUE] > self.threshold_mtx_48h)
        )

        # Detection = Criteria 1 or 2 + at least one of criteria 3,4,5
        self.data[DETECTION] = False
        self.data.loc[
            (criteria_one | criteria_two)
            & (criteria_three | criteria_four | criteria_five),
            DETECTION,
        ] = True


# choose classes to expose to main app
DiagnosticClasses = [
    Diagnose1,
    Diagnose2,
    Diagnose4,
    Diagnose6,
    Diagnose8,
    Diagnose9,
    DME,
]
DiagnoseTypes = Union[
    Diagnose1, Diagnose2, Diagnose4, Diagnose6, Diagnose8, Diagnose9, DME
]
