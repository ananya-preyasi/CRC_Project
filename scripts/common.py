# common.py
#
# Shared configuration for the multi-year (2016-2023) CRC / corticosteroid
# analysis pipeline. Centralizes paths, code lists, and the 20-variable
# candidate set so scripts 04-07 stay consistent with each other and with
# the original single-year (2023) pipeline in 01-03.

import os

# ==========================================================
# Paths
# ==========================================================

HCUP_DIR = "/home/samiran2/Ramen/1_ramen/ddd/HCUP"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_DIR, "outputs")
COHORT_DIR = os.path.join(OUTPUT_DIR, "cohorts")
FIGURE_DIR = os.path.join(PROJECT_DIR, "figures")

for _d in (OUTPUT_DIR, COHORT_DIR, FIGURE_DIR):
    os.makedirs(_d, exist_ok=True)

# ==========================================================
# Years covered
# ==========================================================
# 2021 is excluded: NIS_2021_Core.csv on disk has ~500,000 rows versus
# ~6.5-7.2 million for every other year (2016-2020, 2022-2023), consistent
# with a truncated/incomplete source file rather than a genuine sampling
# change. Confirmed with the user (2026-08-20) to exclude 2021 rather than
# silently include a non-representative year.

ALL_CORE_YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
EXCLUDED_YEARS = {2021: "Source NIS_2021_Core.csv is truncated (~500K rows vs ~7M expected)"}
YEARS = [y for y in ALL_CORE_YEARS if y not in EXCLUDED_YEARS]


def core_file(year):
    return os.path.join(HCUP_DIR, str(year), f"NIS_{year}_Core.csv")


# ==========================================================
# Cohort definition codes (identical to scripts/01_build_cohort.py)
# ==========================================================

CRC_CODES = ["C18", "C19", "C20"]

EXCLUSION_CODES = [
    "D12",
    "C21",
    "C78.5",
    "D13.91",
    "Z15.09",
    "Q85.89",
    "K50",
    "K51",
]

STEROID_EXPOSURE_CODES = [
    "Z79.52",
    "M05",
    "M06",
    "M32",
    "M30",
    "M31",
    "M35.3",
    "M33",
    "M33.2",
    "L40.5",
    "M07",
    "D86",
    "G35",
    "N04",
    "K75.4",
    "Z94",
    "K50",
    "K51",
]

# ==========================================================
# 20 candidate variables (screened in Section 8-11 of the
# progress report, using the 2023 cohort)
# ==========================================================

CANDIDATE_VARIABLES = [
    "AGE",
    "AMONTH",
    "AWEEKEND",
    "DQTR",
    "DRG",
    "DRG_NOPOA",
    "ELECTIVE",
    "FEMALE",
    "HCUP_ED",
    "I10_NDX",
    "I10_NPR",
    "I10_SERVICELINE",
    "LOS",
    "MDC",
    "MDC_NOPOA",
    "PAY1",
    "PCLASS_ORPROC",
    "PL_NCHS2",
    "TRAN_IN",
    "ZIPINC_QRTL",
]

# Variable type used for univariate screening (chi-square / MI / logistic).
# Matches scripts/03_feature_screening.py.
VARIABLE_TYPES = {
    "AGE": "Continuous",
    "AMONTH": "Ordinal",
    "AWEEKEND": "Binary",
    "DQTR": "Ordinal",
    "DRG": "Nominal",
    "DRG_NOPOA": "Nominal",
    "ELECTIVE": "Binary",
    "FEMALE": "Binary",
    "HCUP_ED": "Binary",
    "I10_NDX": "Continuous",
    "I10_NPR": "Continuous",
    "I10_SERVICELINE": "Nominal",
    "LOS": "Continuous",
    "MDC": "Nominal",
    "MDC_NOPOA": "Nominal",
    "PAY1": "Nominal",
    "PCLASS_ORPROC": "Nominal",
    "PL_NCHS2": "Ordinal",
    "TRAN_IN": "Binary",
    "ZIPINC_QRTL": "Ordinal",
}

CONTINUOUS_VARIABLES = {v for v, t in VARIABLE_TYPES.items() if t == "Continuous"}
BINARY_VARIABLES = {v for v, t in VARIABLE_TYPES.items() if t == "Binary"}

# Known per-year availability gaps in the NIS Core file layout:
#   - I10_SERVICELINE, PCLASS_ORPROC: introduced in the 2019 Core file
#   - PL_NCHS2: only present in the 2023 Core file (in this data pull)
# The cohort builder detects availability directly from each year's header,
# so this dict is informational / used for the README narrative only.
KNOWN_AVAILABILITY_NOTES = {
    "I10_SERVICELINE": "Available 2019 onward",
    "PCLASS_ORPROC": "Available 2019 onward",
    "PL_NCHS2": "Available 2023 only (in this data pull)",
}
