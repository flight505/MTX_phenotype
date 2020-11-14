"""All constants, mostly name of columns from initial dataframe used in the computation of diagnostics

    from src.constants import *
    print(DETECTION)
"""

########################################################################
# Samples file
########################################################################
SAMPLE_TIME = "REALSAMPLECOLLECTIONTIME"
P_CODE = "OL_INVER_IUPAC_CDE"
PATIENT_ID = "NOPHO_NR"
VALUE = "INTERNAL_REPLY_NUM"
REF_PATIENT = "REFTEXT"

########################################################################
# Infusion times file
########################################################################
INFUSION_NO = "INFNO"
INF_STARTDATE = "MTX_INFDATE"
INF_STARTHOUR = "MTX_INF_START"
SEX = "SEX"
MP6_STOP = "MP6_POST_STOP"

########################################################################
# Computed in app
########################################################################
DETECTION = "detection"
DIFFERENCE_SAMPLETIME_TO_INF_STARTDATE = "HOUR_DIFF_SAMPLE_INF"
