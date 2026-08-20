"""
05_feature_screening_multi_year.py

Repeats the univariate feature-screening pipeline (chi-square / mutual
information / univariate logistic regression - see 03_feature_screening.py)
independently for every year's cohort produced by
04_build_cohort_multi_year.py.

Each year is screened using only whichever of the 20 candidate variables
are present in that year's Core file (see common.KNOWN_AVAILABILITY_NOTES).
Results are sorted by mutual information (descending) per year, matching
the convention of the original single-year script, and additionally
annotated with each variable's MI-based rank within that year -- this rank
is what 06_topk_selection.py uses to build the Top-K variable sets.

Output
------
outputs/feature_screening_results_<year>.csv   (one per year)
outputs/feature_screening_results_all_years.csv (stacked, with a Year column)
"""

import time

import numpy as np
import pandas as pd

from feature_screening_utils import (
    run_chi_square,
    run_mutual_information,
    run_univariate_logistic_regression,
)
from common import (
    COHORT_DIR,
    OUTPUT_DIR,
    VARIABLE_TYPES,
    YEARS,
)

CONTINUOUS_TYPES = {"Continuous"}
BINARY_TYPES = {"Binary"}
MULTICATEGORY_TYPES = {"Nominal", "Ordinal"}


def screen_year(year):
    t0 = time.time()
    df = pd.read_csv(f"{COHORT_DIR}/cohort_{year}.csv", low_memory=False)

    candidate_vars = [v for v in VARIABLE_TYPES if v in df.columns]

    results = []
    for variable in candidate_vars:
        variable_type = VARIABLE_TYPES[variable]
        result = {"Variable": variable, "Type": variable_type, "Tests Performed": ""}

        if variable_type in CONTINUOUS_TYPES:
            result["Tests Performed"] = "Univariate Logistic Regression, Mutual Information"
            result.update(run_univariate_logistic_regression(df, variable))
            result.update(run_mutual_information(df, variable, discrete=False))
            result["chi_square"] = np.nan
            result["chi_square_p"] = np.nan

        elif variable_type in BINARY_TYPES:
            result["Tests Performed"] = "Chi-square, Univariate Logistic Regression, Mutual Information"
            result.update(run_chi_square(df, variable))
            result.update(run_univariate_logistic_regression(df, variable))
            result.update(run_mutual_information(df, variable, discrete=True))

        elif variable_type in MULTICATEGORY_TYPES:
            result["Tests Performed"] = "Chi-square, Mutual Information"
            result.update(run_chi_square(df, variable))
            result.update(run_mutual_information(df, variable, discrete=True))
            result["odds_ratio"] = np.nan
            result["ci_lower"] = np.nan
            result["ci_upper"] = np.nan
            result["logistic_p"] = np.nan

        results.append(result)

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values("mutual_information", ascending=False, na_position="last")
    results_df["MI_Rank"] = range(1, len(results_df) + 1)

    numeric_columns = results_df.select_dtypes(include=np.number).columns
    results_df[numeric_columns] = results_df[numeric_columns].round(4)

    results_df.insert(0, "Year", year)
    results_df.to_csv(f"{OUTPUT_DIR}/feature_screening_results_{year}.csv", index=False)

    elapsed = time.time() - t0
    print(f"[{year}] screened {len(results_df)} variables in {elapsed:.1f}s "
          f"(n={len(df):,}, CRC={int(df['CRC'].sum())})")
    return results_df


def main():
    all_results = []
    for year in YEARS:
        all_results.append(screen_year(year))

    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(f"{OUTPUT_DIR}/feature_screening_results_all_years.csv", index=False)
    print(f"\nSaved combined multi-year screening results "
          f"({len(combined)} rows) to outputs/feature_screening_results_all_years.csv")


if __name__ == "__main__":
    main()
