"""
06_topk_selection.py

Implements the Top-K feature-selection methodology described in Section 14
of the progress report, for every year 2016-2020, 2022-2023:

  1. Rank that year's candidate variables by mutual information (descending) -
     using that year's own screening results from
     05_feature_screening_multi_year.py (each year gets its own ranking,
     computed the same way as the original 2023-only screening).
  2. For K = 1 .. (number of variables available that year):
       - Take the top-K ranked variables.
       - Fit a logistic regression model predicting CRC from those K
         variables (encoding described in topk_utils.py).
       - Evaluate via 5-fold stratified cross-validation: ROC-AUC and
         PR-AUC (average precision - CRC is a rare outcome, so PR-AUC is
         reported alongside AUC rather than in place of it).
       - Also fit on the full sample once for AIC / BIC / McFadden's
         pseudo-R2, which penalize added variables and are read alongside
         AUC to judge whether an AUC gain from adding a variable is
         "worth it" in information-criterion terms.
  3. Record the best K per year by cross-validated AUC (and separately by
     BIC, which tends to prefer smaller K since it penalizes added
     parameters more than AIC does).

(year, K) combinations are evaluated in parallel with joblib.

Output
------
outputs/topk_results_<year>.csv   (one row per K, per year)
outputs/topk_results_all_years.csv (stacked)
outputs/topk_best_k_summary.csv   (best K per year, by AUC and by BIC)
"""

import sys
import time

import pandas as pd
from joblib import Parallel, delayed

from common import (
    BINARY_VARIABLES,
    CONTINUOUS_VARIABLES,
    COHORT_DIR,
    OUTPUT_DIR,
    YEARS,
)
from topk_utils import evaluate_variable_set


def load_ranking(year):
    ranking = pd.read_csv(f"{OUTPUT_DIR}/feature_screening_results_{year}.csv")
    ranking = ranking.sort_values("MI_Rank")
    return ranking["Variable"].tolist()


def evaluate_one_k(year, df, ranked_variables, k):
    t0 = time.time()
    variables = ranked_variables[:k]
    metrics = evaluate_variable_set(
        df, variables, CONTINUOUS_VARIABLES, BINARY_VARIABLES
    )
    metrics["year"] = year
    metrics["k"] = k
    metrics["variables"] = ", ".join(variables)
    metrics["runtime_seconds"] = round(time.time() - t0, 1)
    print(
        f"[{year}] K={k:2d} "
        f"AUC={metrics['cv_auc_mean']:.4f}±{metrics['cv_auc_std']:.4f}  "
        f"PR-AUC={metrics['cv_pr_auc_mean']:.4f}  "
        f"BIC={metrics['bic']:.0f}  "
        f"features(encoded)={metrics['n_encoded_features']}  "
        f"({metrics['runtime_seconds']:.1f}s)"
    )
    return metrics


def process_year(year):
    ranked_variables = load_ranking(year)
    df = pd.read_csv(f"{COHORT_DIR}/cohort_{year}.csv", low_memory=False)
    n_vars = len(ranked_variables)

    results = Parallel(n_jobs=min(n_vars, 20))(
        delayed(evaluate_one_k)(year, df, ranked_variables, k)
        for k in range(1, n_vars + 1)
    )

    year_df = pd.DataFrame(results)
    ordered_cols = ["year", "k", "cv_auc_mean", "cv_auc_std", "cv_pr_auc_mean",
                     "cv_pr_auc_std", "aic", "bic", "pseudo_r2_mcfadden",
                     "n_obs", "n_cases", "n_encoded_features", "n_continuous",
                     "n_binary", "n_onehot", "n_target_encoded", "converged",
                     "runtime_seconds", "variables"]
    year_df = year_df[[c for c in ordered_cols if c in year_df.columns]]
    year_df.to_csv(f"{OUTPUT_DIR}/topk_results_{year}.csv", index=False)
    return year_df


def combine_and_summarize():
    """
    Reads whichever per-year outputs/topk_results_<year>.csv files exist for
    common.YEARS and (re)builds the combined file + best-K summary. Kept
    separate from run_years() so years can be run one at a time in separate
    (shorter-lived) processes -- see the module docstring / __main__ block --
    without re-running years that already finished.
    """
    all_results = []
    for year in YEARS:
        path = f"{OUTPUT_DIR}/topk_results_{year}.csv"
        try:
            all_results.append(pd.read_csv(path))
        except FileNotFoundError:
            print(f"[{year}] no results file yet ({path}); skipping in combined summary.")

    if not all_results:
        print("No per-year results found yet; nothing to combine.")
        return

    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(f"{OUTPUT_DIR}/topk_results_all_years.csv", index=False)
    print(f"\nSaved combined Top-K results ({combined['year'].nunique()} years) "
          f"to outputs/topk_results_all_years.csv")

    # Best K per year: by max CV AUC, and by min BIC (parsimony-favoring).
    best_rows = []
    for year, group in combined.groupby("year"):
        best_auc_row = group.loc[group["cv_auc_mean"].idxmax()]
        best_bic_row = group.loc[group["bic"].idxmin()]
        # "Elbow" K: smallest K within 0.002 AUC of the best AUC for that year
        # (i.e. simplest model that is within noise of the top performer).
        auc_threshold = best_auc_row["cv_auc_mean"] - 0.002
        elbow_row = group[group["cv_auc_mean"] >= auc_threshold].sort_values("k").iloc[0]

        best_rows.append({
            "year": year,
            "best_k_by_auc": int(best_auc_row["k"]),
            "best_auc": round(best_auc_row["cv_auc_mean"], 4),
            "best_k_by_bic": int(best_bic_row["k"]),
            "auc_at_best_bic_k": round(best_bic_row["cv_auc_mean"], 4),
            "elbow_k": int(elbow_row["k"]),
            "auc_at_elbow_k": round(elbow_row["cv_auc_mean"], 4),
            "n_variables_available": int(group["k"].max()),
        })

    best_df = pd.DataFrame(best_rows).sort_values("year")
    best_df.to_csv(f"{OUTPUT_DIR}/topk_best_k_summary.csv", index=False)
    print("\nBest-K summary:")
    print(best_df.to_string(index=False))


def run_years(years):
    for year in years:
        print(f"\n{'=' * 70}\nYear {year}\n{'=' * 70}")
        process_year(year)


def main():
    # Optional: pass one or more years as CLI args to process only those
    # years (e.g. `python 06_topk_selection.py 2019 2020`), then recombine.
    # With no args, processes every year in common.YEARS. Running years
    # individually keeps each invocation shorter-lived, which sidesteps an
    # observed issue where the single monolithic multi-year run was killed
    # partway through (see PROJECT_PROGRESS_REPORT.md addendum).
    requested_years = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else YEARS
    run_years(requested_years)
    combine_and_summarize()


if __name__ == "__main__":
    main()
