"""
06b_topk_selection_restricted.py

Companion to 06_topk_selection.py. DRG / DRG_NOPOA / MDC / MDC_NOPOA are
hospital-assigned billing/grouping codes computed FROM the discharge's own
diagnosis codes -- including the CRC diagnosis itself when CRC is the
principal diagnosis. Once DRG/DRG_NOPOA entered the primary Top-K model
(around K=4-5, depending on year), cross-validated AUC jumped to ~0.99+
almost immediately (see topk_utils.py for the full explanation). That is a
real result of the primary analysis, but it is not a genuine "these
admission characteristics predict CRC risk" signal -- it is close to
circular, the outcome leaking back in through a derived administrative code.

This script repeats the same Top-K ranking + cross-validated evaluation, but
over the 16 (or fewer, depending on year) candidate variables that remain
after excluding DRG, DRG_NOPOA, MDC, and MDC_NOPOA, so the AUC-vs-K curve
reflects only clinically/administratively interpretable predictors
(demographics, admission characteristics, diagnosis/procedure counts). This
is the more scientifically meaningful curve for informing which covariates
belong in the eventual STEROID_EXPOSURE-adjusted CRC model.

Output
------
outputs/topk_restricted_results_<year>.csv
outputs/topk_restricted_results_all_years.csv
outputs/topk_restricted_best_k_summary.csv
"""

import sys
import time

import pandas as pd
from joblib import Parallel, delayed

from common import BINARY_VARIABLES, CONTINUOUS_VARIABLES, COHORT_DIR, OUTPUT_DIR, YEARS
from topk_utils import evaluate_variable_set

EXCLUDED_TAUTOLOGICAL = {"DRG", "DRG_NOPOA", "MDC", "MDC_NOPOA"}


def load_restricted_ranking(year):
    ranking = pd.read_csv(f"{OUTPUT_DIR}/feature_screening_results_{year}.csv")
    ranking = ranking[~ranking["Variable"].isin(EXCLUDED_TAUTOLOGICAL)]
    ranking = ranking.sort_values("MI_Rank")
    return ranking["Variable"].tolist()


def evaluate_one_k(year, df, ranked_variables, k):
    t0 = time.time()
    variables = ranked_variables[:k]
    metrics = evaluate_variable_set(df, variables, CONTINUOUS_VARIABLES, BINARY_VARIABLES)
    metrics["year"] = year
    metrics["k"] = k
    metrics["variables"] = ", ".join(variables)
    metrics["runtime_seconds"] = round(time.time() - t0, 1)
    print(
        f"[{year}] K={k:2d} (restricted) "
        f"AUC={metrics['cv_auc_mean']:.4f}±{metrics['cv_auc_std']:.4f}  "
        f"PR-AUC={metrics['cv_pr_auc_mean']:.4f}  "
        f"BIC={metrics['bic']:.0f}  "
        f"({metrics['runtime_seconds']:.1f}s)",
        flush=True,
    )
    return metrics


def process_year(year):
    ranked_variables = load_restricted_ranking(year)
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
    year_df.to_csv(f"{OUTPUT_DIR}/topk_restricted_results_{year}.csv", index=False)
    return year_df


def combine_and_summarize():
    """Reads whichever per-year restricted result files exist and (re)builds
    the combined + best-K summary. Separate from the per-year loop so years
    can be run individually (see __main__ / module docstring) -- a single
    long-lived process running all 7 years in one go was observed to be
    killed by something external (not an OOM per dmesg) partway through on
    this shared server; short single-year invocations complete reliably."""
    all_results = []
    for year in YEARS:
        path = f"{OUTPUT_DIR}/topk_restricted_results_{year}.csv"
        try:
            all_results.append(pd.read_csv(path))
        except FileNotFoundError:
            print(f"[{year}] no restricted results file yet ({path}); skipping.")

    if not all_results:
        print("No restricted per-year results found yet; nothing to combine.")
        return

    combined = pd.concat(all_results, ignore_index=True)
    combined.to_csv(f"{OUTPUT_DIR}/topk_restricted_results_all_years.csv", index=False)
    print("\nSaved combined restricted Top-K results to outputs/topk_restricted_results_all_years.csv")

    best_rows = []
    for year, group in combined.groupby("year"):
        best_auc_row = group.loc[group["cv_auc_mean"].idxmax()]
        best_bic_row = group.loc[group["bic"].idxmin()]
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
    best_df.to_csv(f"{OUTPUT_DIR}/topk_restricted_best_k_summary.csv", index=False)
    print("\nBest-K summary (restricted):")
    print(best_df.to_string(index=False))


def run_years(years):
    for year in years:
        print(f"\n{'=' * 70}\nYear {year} (restricted: excluding {sorted(EXCLUDED_TAUTOLOGICAL)})\n{'=' * 70}", flush=True)
        process_year(year)


def main():
    requested_years = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else YEARS
    run_years(requested_years)
    combine_and_summarize()


if __name__ == "__main__":
    main()
