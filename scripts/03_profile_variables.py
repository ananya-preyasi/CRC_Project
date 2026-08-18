import pandas as pd

COHORT_FILE = "../outputs/cohort.csv"
OUTPUT_FILE = "../outputs/variable_profile.csv"

# HCUP special codes representing missing / invalid values
HCUP_MISSING_CODES = [-9, -99, -999, -9999]


def guess_variable_type(dtype, unique_values, total_rows, column_name):
    """
    Guess the type of variable based on its properties.
    """

    # Outcome / Exposure
    if column_name in ["CRC", "STEROID_EXPOSURE"]:
        return "Outcome / Exposure"

    # Identifiers
    if column_name in ["KEY_NIS", "HOSP_NIS"]:
        return "Identifier"

    if unique_values == total_rows:
        return "Identifier"

    # Survey design variables
    if column_name == "NIS_STRATUM":
        return "Survey Design Variable"

    # Diagnosis codes
    if column_name.startswith("I10_DX"):
        return "Diagnosis Code"

    # Procedure codes
    if column_name.startswith("I10_PR"):
        return "Procedure Code"

    # String variables
    if dtype == "object":
        return "Categorical (String)"

    # Constant variables
    if unique_values <= 1:
        return "Constant (Exclude)"

    # Binary variables
    if unique_values == 2:
        return "Binary"

    # Ordinal / Nominal candidates
    if unique_values <= 10:
        return "Ordinal / Nominal"

    # Otherwise assume continuous
    return "Continuous"


def main():

    print("Loading cohort...")
    df = pd.read_csv(COHORT_FILE, low_memory=False)

    total_rows = len(df)

    profile = []

    for col in df.columns:

        # Raw unique values (includes HCUP missing codes)
        raw_unique = df[col].nunique()

        # Valid unique values (ignores HCUP missing codes)
        if pd.api.types.is_numeric_dtype(df[col]):
            valid_values = df[col][~df[col].isin(HCUP_MISSING_CODES)]
        else:
            valid_values = df[col].dropna()

        valid_unique = valid_values.nunique()

        profile.append({

            "Variable": col,

            "Data Type": str(df[col].dtype),

            "Raw Unique Values": raw_unique,

            "Valid Unique Values": valid_unique,

            "Missing Values": df[col].isna().sum(),

            "Minimum": df[col].min() if df[col].dtype != "object" else "",

            "Maximum": df[col].max() if df[col].dtype != "object" else "",

            "Suggested Variable Type":
                guess_variable_type(
                    str(df[col].dtype),
                    valid_unique,
                    total_rows,
                    col
                )

        })

    profile_df = pd.DataFrame(profile)

    profile_df.to_csv(OUTPUT_FILE, index=False)

    print("\nVariable profile saved to:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()
