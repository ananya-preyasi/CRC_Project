"""
03_feature_screening.py

Performs automated feature screening on the HCUP cohort.

Continuous Variables
--------------------
• Univariate Logistic Regression
• Mutual Information

Binary Variables
----------------
• Chi-square Test
• Univariate Logistic Regression
• Mutual Information

Nominal / Ordinal Variables
---------------------------
• Chi-square Test
• Mutual Information

Output
------
feature_screening_results.csv
"""

import os
import time

import numpy as np
import pandas as pd

from feature_screening_utils import (
    run_chi_square,
    run_mutual_information,
    run_univariate_logistic_regression,
)

# ==========================================================
# File Paths
# ==========================================================

COHORT_FILE = "../outputs/cohort.csv"

OUTPUT_FILE = "../outputs/feature_screening_results.csv"

# ==========================================================
# Candidate Variables
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

# ==========================================================
# Manual Variable Types
# ==========================================================

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

# ==========================================================
# Variable Type Groups
# ==========================================================

CONTINUOUS_TYPES = {"Continuous"}

BINARY_TYPES = {"Binary"}

MULTICATEGORY_TYPES = {"Nominal", "Ordinal"}

# ==========================================================
# Helper Functions
# ==========================================================

def print_header(title):
    """
    Prints a formatted section header.
    """

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def validate_configuration():
    """
    Performs basic validation before starting
    the feature screening pipeline.
    """

    # Check cohort file

    if not os.path.exists(COHORT_FILE):

        raise FileNotFoundError(
            f"Cohort file not found:\n{COHORT_FILE}"
        )

    # Check output directory

    output_directory = os.path.dirname(OUTPUT_FILE)

    os.makedirs(output_directory, exist_ok=True)

    # Check every variable has a defined type

    missing = [

        variable

        for variable in CANDIDATE_VARIABLES

        if variable not in VARIABLE_TYPES

    ]

    if missing:

        raise ValueError(

            "The following variables do not have "
            f"a defined type:\n{missing}"

        )

    # Check type names

    valid_types = {

        "Continuous",
        "Binary",
        "Nominal",
        "Ordinal"

    }

    invalid = [

        variable

        for variable, variable_type
        in VARIABLE_TYPES.items()

        if variable_type not in valid_types

    ]

    if invalid:

        raise ValueError(

            "Invalid variable type found for:\n"
            f"{invalid}"

        )
# ==========================================================
# Main Function
# ==========================================================

def main():

    overall_start = time.time()

    # ------------------------------------------------------
    # Validate configuration
    # ------------------------------------------------------

    print_header("Validating Configuration")

    validate_configuration()

    print("Configuration successfully validated.")

    # ------------------------------------------------------
    # Load cohort
    # ------------------------------------------------------

    print_header("Loading Cohort")

    df = pd.read_csv(

        COHORT_FILE,

        low_memory=False

    )

    print(f"Cohort loaded successfully.")

    print(f"Number of patients : {len(df):,}")

    print(f"Number of variables: {len(df.columns)}")

    # ------------------------------------------------------
    # Initialize results
    # ------------------------------------------------------

    results = []

    total_variables = len(CANDIDATE_VARIABLES)

    print_header("Starting Feature Screening")

    # ------------------------------------------------------
    # Loop through every candidate variable
    # ------------------------------------------------------

    for index, variable in enumerate(

        CANDIDATE_VARIABLES,

        start=1

    ):

        print(

            f"\n[{index}/{total_variables}] {variable}"

        )

        variable_start = time.time()

        # ----------------------------------------------
        # Check variable exists
        # ----------------------------------------------

        if variable not in df.columns:

            print(

                f"Column '{variable}' not found."

            )

            print("Skipping...")

            continue

        # ----------------------------------------------
        # Get variable type
        # ----------------------------------------------

        variable_type = VARIABLE_TYPES[variable]

        print(

            f"Variable Type : {variable_type}"

        )

        # ----------------------------------------------
        # Initialize result dictionary
        # ----------------------------------------------

        result = {

            "Variable": variable,

            "Type": variable_type,

            "Tests Performed": ""

        }

        try:

            # --------------------------------------------------
            # Continuous Variables
            # --------------------------------------------------

            if variable_type in CONTINUOUS_TYPES:

                result["Tests Performed"] = (
                    "Univariate Logistic Regression, "
                    "Mutual Information"
                )

                # Logistic Regression

                result.update(

                    run_univariate_logistic_regression(
                        df,
                        variable
                    )

                )

                # Mutual Information

                result.update(

                    run_mutual_information(
                        df,
                        variable,
                        discrete=False
                    )

                )

                # Not applicable

                result["chi_square"] = np.nan
                result["chi_square_p"] = np.nan

            # --------------------------------------------------
            # Binary Variables
            # --------------------------------------------------

            elif variable_type in BINARY_TYPES:

                result["Tests Performed"] = (
                    "Chi-square, "
                    "Univariate Logistic Regression, "
                    "Mutual Information"
                )

                # Chi-square

                result.update(

                    run_chi_square(
                        df,
                        variable
                    )

                )

                # Logistic Regression

                result.update(

                    run_univariate_logistic_regression(
                        df,
                        variable
                    )

                )

                # Mutual Information

                result.update(

                    run_mutual_information(
                        df,
                        variable,
                        discrete=True
                    )

                )

            # --------------------------------------------------
            # Nominal / Ordinal Variables
            # --------------------------------------------------

            elif variable_type in MULTICATEGORY_TYPES:

                result["Tests Performed"] = (
                    "Chi-square, "
                    "Mutual Information"
                )

                # Chi-square

                result.update(

                    run_chi_square(
                        df,
                        variable
                    )

                )

                # Mutual Information

                result.update(

                    run_mutual_information(
                        df,
                        variable,
                        discrete=True
                    )

                )

                # Logistic Regression not performed

                result["odds_ratio"] = np.nan
                result["ci_lower"] = np.nan
                result["ci_upper"] = np.nan
                result["logistic_p"] = np.nan

            else:

                raise ValueError(

                    f"Unknown variable type: {variable_type}"

                )

            # --------------------------------------------------
            # Store Results
            # --------------------------------------------------

            results.append(result)

            # --------------------------------------------------
            # Runtime
            # --------------------------------------------------

            elapsed = time.time() - variable_start

            print(

                f"Completed successfully in "
                f"{elapsed:.2f} seconds."

            )

        except Exception as e:

            print(
                f"Error while processing {variable}"
            )

            print(e)

            continue

    # ==========================================================
    # Create Results DataFrame
    # ==========================================================

    print_header("Preparing Results")

    results_df = pd.DataFrame(results)

    if results_df.empty:

        print("No results were generated.")

        return

    # ==========================================================
    # Sort Results
    # ==========================================================

    results_df = results_df.sort_values(

        by="mutual_information",

        ascending=False,

        na_position="last"

    )

    # ==========================================================
    # Round Numerical Columns
    # ==========================================================
    numeric_columns = results_df.select_dtypes(
       include=np.number
     ).columns

    results_df[numeric_columns] = (

        results_df[numeric_columns]

        .round(4)

    )

    # ==========================================================
    # Save Results
    # ==========================================================

    results_df.to_csv(

        OUTPUT_FILE,

        index=False

    )

    # ==========================================================
    # Final Summary
    # ==========================================================

    total_runtime = time.time() - overall_start

    print_header("Feature Screening Completed")

    print(f"Variables Successfully Screened : {len(results_df)}")

    print(f"Output File                  : {OUTPUT_FILE}")

    print(f"Total Runtime                : {total_runtime:.2f} seconds")

    pd.set_option("display.max_columns", None)

    pd.set_option("display.width", 200)

    pd.set_option("display.max_colwidth", None)

    print("\nFeature Screening Results")

#    print("-" * 140)

    summary_columns = [


        "Variable",
        "Type",
        "mutual_information",
        "chi_square",
        "chi_square_p",
        "odds_ratio",
        "ci_lower",
        "ci_upper",
        "logistic_p"

    ]

    print(
        
        results_df[summary_columns]

        .to_string(index=False)
    )

# ==========================================================
# Entry Point
# ==========================================================

if __name__ == "__main__":

    main()

