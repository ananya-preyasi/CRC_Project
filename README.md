# CRC_Project

Retrospective cohort study investigating the association between chronic corticosteroid exposure and colorectal cancer (CRC) in adults aged 18-49, using the HCUP National Inpatient Sample (NIS), years 2016-2023.

> For the full narrative history of the project (cohort definitions, exclusion criteria, the original single-year screening) see [`PROJECT_PROGRESS_REPORT.md`](PROJECT_PROGRESS_REPORT.md). This README covers the current state of the repository, including the multi-year Top-K feature-selection analysis described below.

## What this analysis answers

The 20 candidate variables identified in the original 2023-only feature screening (Section 8-11 of the progress report) were ranked by mutual information with the CRC outcome. The open question was: **how many of those top-ranked variables should actually go into the model** — and does the answer hold up across years? This repository now answers that by varying K (the number of top-ranked variables retained) from 1 up to the full candidate set, for every usable NIS year from 2016 to 2023, and scoring each K by cross-validated ROC-AUC / PR-AUC (plus AIC/BIC/pseudo-R² as a parsimony check). See [Section: Top-K methodology](#top-k-feature-selection-methodology) and [Section: Results](#results) below.

**Headline finding:** the first jump in AUC (K=1→3, AUC≈0.71→0.85) is driven by genuine, generalizable covariates (procedure count, diagnosis count, age). A second, much larger jump (AUC→0.998) appears the moment `DRG`/`DRG_NOPOA` enter — but that jump is **not a real predictive signal**: DRG is a hospital billing code computed from the discharge's own diagnosis list, so it is close to circular for a diagnosis-based outcome. A parallel "restricted" analysis that excludes `DRG`, `DRG_NOPOA`, `MDC`, `MDC_NOPOA` gives a more honest ceiling: **AUC ≈ 0.87-0.94** using 7-9 clinically interpretable variables. See the [DRG/MDC interpretive caveat](#a-necessary-caveat-drgmdc-and-circularity) for the full explanation — this is the single most important methodological finding of this stage of the project.

## Project Structure

```
CRC_Project/
├── outputs/
│   ├── cohort_build_summary.csv               # rows/CRC cases/exposure per year
│   ├── cohorts/                                # per-year reduced cohort CSVs (gitignored)
│   ├── feature_screening_results.csv           # original 2023-only screening (legacy)
│   ├── feature_screening_results_<year>.csv    # per-year screening, 2016-2023
│   ├── feature_screening_results_all_years.csv # stacked, with MI_Rank per year
│   ├── topk_results_<year>.csv                 # Top-K sweep, full 20-variable set
│   ├── topk_results_all_years.csv
│   ├── topk_best_k_summary.csv                 # best/elbow K per year (full set)
│   ├── topk_restricted_results_<year>.csv      # Top-K sweep, DRG/MDC excluded
│   ├── topk_restricted_results_all_years.csv
│   ├── topk_restricted_best_k_summary.csv      # best/elbow K per year (restricted set)
│   └── variable_profile.csv                    # 127-variable profiling (legacy, 2023 only)
├── figures/
│   ├── fig1_auc_vs_k.png                # CV ROC-AUC vs K, full variable set, all years
│   ├── fig2_prauc_vs_k.png              # CV PR-AUC vs K, full variable set, all years
│   ├── fig3_bic_vs_k.png                # BIC vs K, full variable set, all years
│   ├── fig4_auc_heatmap.png             # Year x K heatmap of AUC
│   ├── fig5_mi_rank_heatmap.png         # Variable x Year heatmap of MI rank
│   ├── fig6_best_k_summary.png          # Best K vs elbow K per year
│   ├── fig7_crc_rate_by_year.png        # CRC cases per 100k, by year (context)
│   ├── fig8_auc_vs_k_restricted.png     # CV ROC-AUC vs K, restricted set, all years
│   └── fig9_primary_vs_restricted.png   # Best AUC: full set vs restricted set
├── scripts/
│   ├── 00_check_dataset.py                    # [legacy, 2023 only] KEY_NIS uniqueness check
│   ├── 01_build_cohort.py                      # [legacy, 2023 only] original cohort builder
│   ├── 02_logistic_regression.py               # [legacy, 2023 only] initial multivariate model
│   ├── 03_feature_screening.py                 # [legacy, 2023 only] original screening pipeline
│   ├── 03_profile_variables.py                 # [legacy, 2023 only] 127-variable profiling
│   ├── feature_screening_utils.py              # chi-square / MI / logistic helpers (shared)
│   ├── common.py                                # shared config: years, paths, code lists, 20-var set
│   ├── 04_build_cohort_multi_year.py            # cohort builder generalized to 2016-2023
│   ├── 05_feature_screening_multi_year.py       # per-year screening (reuses feature_screening_utils.py)
│   ├── topk_utils.py                            # encoding + CV evaluation for the Top-K sweep
│   ├── 06_topk_selection.py                     # Top-K sweep, full 20-variable set
│   ├── 06b_topk_selection_restricted.py         # Top-K sweep, DRG/MDC-family excluded
│   ├── plot_style.py                            # shared matplotlib styling
│   └── 07_generate_figures.py                   # generates all 9 figures above
├── requirements.txt
├── README.md
├── PROJECT_PROGRESS_REPORT.md
└── .gitignore
```

## Data

| Property | Detail |
|----------|--------|
| Source | HCUP National Inpatient Sample (NIS) Core files, `/HCUP/<year>/NIS_<year>_Core.csv` |
| Years used | 2016, 2017, 2018, 2019, 2020, 2022, 2023 (7 years) |
| Year excluded | **2021** — `NIS_2021_Core.csv` on the source disk has only ~500,000 rows versus ~6.5-7.2 million for every other year, consistent with a truncated/incomplete file rather than a real sampling change. Confirmed with the project owner (2026-08-20) to exclude rather than silently analyze a non-representative year. |
| Population | Hospital admissions, ages 18-49, after CRC/exclusion/steroid-exposure logic identical to `01_build_cohort.py` (see progress report Section 4) |

**Per-year variable availability** (detected directly from each year's Core file header, not hardcoded):

| Variable(s) | Available |
|---|---|
| `I10_SERVICELINE`, `PCLASS_ORPROC` | 2019 onward (17 of the 20 candidate variables are available for 2016-2018) |
| `PL_NCHS2` | 2023 only, in this data pull (19 of 20 available for 2019-2022) |
| Diagnosis positions (`I10_DX1`...`I10_DXn`) | 30 positions in 2016, 40 positions from 2017 onward — the CRC/exclusion/steroid-exposure logic scans however many positions exist that year |
| Everything else | Available in all 7 years |

The cohort builder ([`04_build_cohort_multi_year.py`](scripts/04_build_cohort_multi_year.py)) reads only the columns it needs (diagnosis columns + the 20 candidate variables + `AGE`) instead of the full ~100-127 column Core file, and writes a reduced per-year cohort (`outputs/cohorts/cohort_<year>.csv`) containing only the candidate variables plus `CRC` and `STEROID_EXPOSURE` — no diagnosis codes or admission/hospital identifiers are retained downstream of that step. `outputs/cohorts/` is still row-level derived data and is excluded from version control, consistent with the handling of `cohort.csv` / `cohort_principal_dx.csv` in the original pipeline.

Rebuilding all 7 years from scratch also resolves the `cohort.csv` vs. `cohort_principal_dx.csv` discrepancy noted in progress report Section 13.1: the 2023 cohort produced by the unified `04_build_cohort_multi_year.py` has exactly 1,808,602 rows, matching the original `cohort_principal_dx.csv`, and is the version used throughout this multi-year analysis.

### Cohort size and CRC burden by year

| Year | Cohort (n) | CRC cases | CRC per 100k | Steroid-exposed |
|------|-----------:|----------:|--------------:|-----------------:|
| 2016 | 2,021,244 | 2,680 | 132.6 | 51,830 |
| 2017 | 1,987,850 | 2,669 | 134.3 | 51,657 |
| 2018 | 1,953,919 | 2,728 | 139.6 | 50,853 |
| 2019 | 1,928,260 | 2,746 | 142.4 | 50,571 |
| 2020 | 1,819,316 | 2,748 | 151.0 | 44,602 |
| 2022 | 1,788,156 | 2,868 | 160.4 | 43,675 |
| 2023 | 1,808,602 | 3,214 | 177.7 | 45,154 |

The CRC rate per 100,000 eligible admissions rises essentially every year, from 132.6 (2016) to 177.7 (2023) — a ~34% relative increase (see `fig7_crc_rate_by_year.png`). This is consistent with the literature on rising early-onset CRC incidence and is useful context, but it reflects diagnosed CRC among 18-49 hospital admissions in this cohort, not a population-level incidence estimate, and no adjustment for coding-practice changes over time has been made.

## Analysis Pipeline

| Step | Script | Description |
|------|--------|-------------|
| 0 | `00_check_dataset.py` | [legacy] Validates `KEY_NIS` uniqueness (2023 Core file) |
| 1 | `01_build_cohort.py` | [legacy] Original single-year (2023) cohort builder |
| 2 | `02_logistic_regression.py` | [legacy] Initial multivariate logistic regression (2023) |
| 3a | `03_profile_variables.py` | [legacy] Profiles all 127 variables (2023) |
| 3b | `03_feature_screening.py` | [legacy] Original 20-variable screening (2023) |
| **4** | **`04_build_cohort_multi_year.py`** | **Builds the cohort for every year 2016-2023 (2021 excluded)** |
| **5** | **`05_feature_screening_multi_year.py`** | **Repeats chi-square / MI / univariate logistic screening independently per year** |
| **6** | **`06_topk_selection.py`** | **Top-K sweep (K=1..20) with 5-fold CV AUC/PR-AUC + AIC/BIC, full variable set, per year** |
| **6b** | **`06b_topk_selection_restricted.py`** | **Same sweep excluding `DRG`/`DRG_NOPOA`/`MDC`/`MDC_NOPOA`** |
| **7** | **`07_generate_figures.py`** | **Generates all 9 figures from the outputs above** |

Steps 0-3 are left as-is (single-year, 2023) and are documented in full in the progress report. Steps 4-7 are the new multi-year Top-K work this README describes. Run order for steps 4-7: `04` → `05` → `06` and `06b` (independent of each other) → `07`.

### Environment

A dedicated conda environment was used (`crc_project`, Python 3.11) with the packages in `requirements.txt`, plus `scikit-learn>=1.3` specifically for `sklearn.preprocessing.TargetEncoder`. From `scripts/`:

```bash
conda create -n crc_project python=3.11
conda activate crc_project
pip install -r ../requirements.txt

python 04_build_cohort_multi_year.py
python 05_feature_screening_multi_year.py
python 06_topk_selection.py            # all 7 years; add year args e.g. `06_topk_selection.py 2023` to run one year
python 06b_topk_selection_restricted.py
python 07_generate_figures.py
```

**Practical note on long-running jobs on this server:** running all 7 years in a single `06_topk_selection.py` (or `06b_...py`) invocation was observed to be killed partway through (after ~6 of 7 years) by something external to this project — not an OOM per `dmesg` (checked), and reproducible across two independent long-running attempts. Both `06_topk_selection.py` and `06b_topk_selection_restricted.py` accept one or more years as CLI arguments (e.g. `python 06_topk_selection.py 2019 2020`) specifically so each year can be run as a separate, shorter-lived process if the monolithic run gets killed again; calling either script with no arguments processes all years and then rebuilds the combined/summary CSVs from whichever per-year files exist.

## Top-K Feature-Selection Methodology

### Ranking

For each year independently, the 20 candidate variables (or however many are available that year — see [Data](#data)) are ranked by mutual information with `CRC`, using the same chi-square / mutual-information / univariate-logistic screening as the original 2023 analysis (`feature_screening_utils.py`, unchanged). This produces a per-year `MI_Rank`. The rank order turns out to be **highly stable across all 7 years** (see `fig5_mi_rank_heatmap.png`): `I10_NPR`, `I10_NDX`, `AGE` are ranked 1-3 in every single year, and `DRG`/`DRG_NOPOA` and `MDC`/`MDC_NOPOA` are always ranked 4-5 and 6-7 (or adjacent) regardless of year.

### Sweeping K

For K = 1 up to the number of variables available that year, the top-K ranked variables are used to fit a logistic regression predicting `CRC`, evaluated via:

- **5-fold stratified cross-validated ROC-AUC and PR-AUC** (average precision) — the primary metrics. PR-AUC is reported alongside ROC-AUC because CRC prevalence is well under 1% in every year (see table above), and ROC-AUC alone can look deceptively strong under severe class imbalance.
- **AIC / BIC / McFadden's pseudo-R²** from a single full-sample fit — a parsimony check, since these penalize added parameters (BIC more heavily than AIC). Used to compute an alternate "best K by BIC" alongside "best K by AUC".
- An **elbow K**: the smallest K whose CV AUC is within 0.002 of that year's maximum — i.e. the simplest model that is statistically indistinguishable from the best one found.

### Encoding

The 20 variables mix continuous, binary, and categorical (nominal/ordinal) types with very different cardinalities:

| Bucket | Variables | Encoding |
|---|---|---|
| Continuous | `AGE`, `LOS`, `I10_NDX`, `I10_NPR` | Standardized (z-score) |
| Binary | `AWEEKEND`, `ELECTIVE`, `FEMALE`, `HCUP_ED`, `TRAN_IN` | Passthrough (0/1) |
| Low-cardinality nominal/ordinal (≤50 categories) | `AMONTH`, `DQTR`, `PAY1`, `ZIPINC_QRTL`, `PL_NCHS2`, `I10_SERVICELINE`, `PCLASS_ORPROC`, `MDC`, `MDC_NOPOA` | One-hot |
| High-cardinality nominal (>50 categories) | `DRG`, `DRG_NOPOA` (~750 codes each) | `sklearn.preprocessing.TargetEncoder` (internally cross-fitted smoothed mean CRC rate per category) |

The cardinality split is data-driven (checked at runtime), not hardcoded, so it adapts if a given year's data differs. `DRG`/`DRG_NOPOA` are target-encoded rather than one-hot encoded specifically to keep the design matrix tractable at large K — one-hot encoding two ~750-category variables would add ~1,500 columns to every model from K≈4 onward across ~1.8-2.0 million rows per year, which is both computationally wasteful and not really in the spirit of a "does adding this variable help" comparison.

Logistic regression is fit with `class_weight="balanced"` for the cross-validated AUC/PR-AUC metrics (standard practice given how rare CRC is in this age range); the single full-sample AIC/BIC/pseudo-R² fit uses a very lightly L2-penalized MLE (`alpha=1e-6`), which is numerically indistinguishable from unpenalized MLE when the design matrix is well-conditioned but remains stable once near-duplicate one-hot columns (see next section) make an unpenalized fit fail to converge.

## Results

### Full 20-variable set

`fig1_auc_vs_k.png`, `fig2_prauc_vs_k.png`, `fig3_bic_vs_k.png`, `fig4_auc_heatmap.png`

| Year | Best K (max AUC) | Best AUC | Best K by BIC | Elbow K | AUC at elbow K | Variables available |
|------|---:|---:|---:|---:|---:|---:|
| 2016 | 13 | 0.9979 | 7 | 7 | 0.9978 | 17 |
| 2017 | 12 | 0.9977 | 10 | 7 | 0.9976 | 17 |
| 2018 | 14 | 0.9977 | 10 | 7 | 0.9976 | 17 |
| 2019 | 13 | 0.9977 | 12 | 7 | 0.9975 | 19 |
| 2020 | 15 | 0.9979 | 6 | 6 | 0.9977 | 19 |
| 2022 | 15 | 0.9977 | 6 | 6 | 0.9976 | 19 |
| 2023 | 17 | 0.9976 | 6 | 6 | 0.9974 | 20 |

Every year shows the same shape: AUC starts around 0.71 (K=1, `I10_NPR` alone), climbs to ~0.85 by K=3 (adding `I10_NDX`, `AGE`), then jumps to ~0.995-0.998 the moment K=4 adds `DRG_NOPOA` (or `DRG`, depending on year — they are near-interchangeable, see progress report Section 11.2), and is essentially flat from K≈6-7 onward. BIC actually bottoms out at K=6-7 in every year (adding more variables past that point costs more BIC penalty than it buys in log-likelihood), so **"best K by BIC" and "elbow K" agree almost exactly** — both land at K=6 or K=7 in all 7 years.

### A necessary caveat: DRG/MDC and circularity

**This is the key methodological finding of this analysis.** `DRG` and `DRG_NOPOA` (Diagnosis Related Group) — and to a lesser extent `MDC`/`MDC_NOPOA` (Major Diagnostic Category) — are **hospital-assigned billing/grouping codes computed from the discharge's own diagnosis codes**, including the CRC diagnosis itself when CRC is the principal diagnosis. There is a GI-malignancy-specific DRG/MDC grouping, so once a patient's diagnoses are known, DRG/MDC already "know" whether this was a cancer admission. Including them in a model that predicts CRC from the same admission's characteristics is close to circular — it is not a genuine "these demographic/admission characteristics predict CRC risk" signal, it is closer to the outcome leaking back in through a derived administrative code.

The AUC≈0.998 ceiling reached in the full analysis above is a direct consequence of this. **It should not be reported or interpreted as "we can predict CRC with 99.8% AUC from admission characteristics."** It largely reflects that DRG/MDC are a near-restatement of the diagnosis list.

To give a scientifically meaningful answer to "how well do the clinically/administratively interpretable candidate variables predict CRC," `06b_topk_selection_restricted.py` repeats the identical sweep with `DRG`, `DRG_NOPOA`, `MDC`, `MDC_NOPOA` excluded from the candidate set.

### Restricted variable set (excludes DRG/DRG_NOPOA/MDC/MDC_NOPOA)

`fig8_auc_vs_k_restricted.png`, `fig9_primary_vs_restricted.png`

| Year | Best K (max AUC) | Best AUC | Best K by BIC | Elbow K | AUC at elbow K | Variables available |
|------|---:|---:|---:|---:|---:|---:|
| 2016 | 11 | 0.8730 | 8 | 7 | 0.8715 | 13 |
| 2017 | 11 | 0.8774 | 9 | 7 | 0.8761 | 13 |
| 2018 | 11 | 0.8778 | 8 | 7 | 0.8765 | 13 |
| 2019 | 13 | 0.9292 | 9 | 9 | 0.9288 | 15 |
| 2020 | 13 | 0.9336 | 9 | 8 | 0.9317 | 15 |
| 2022 | 13 | 0.9373 | 9 | 9 | 0.9366 | 15 |
| 2023 | 13 | 0.9371 | 10 | 8 | 0.9356 | 16 |

This is a much more defensible ceiling: **AUC ≈ 0.87-0.88 for 2016-2018, and ≈ 0.93-0.94 for 2019-2023**, using 7-9 variables. That step change lines up exactly with `I10_SERVICELINE` and `PCLASS_ORPROC` becoming available in 2019 — both variables rank in the restricted top-6 every year they exist, and both carry real, non-circular clinical information (service line and procedure classification are set largely independent of whether the diagnosis was CRC). This is a genuine, reproducible improvement in predictive information from 2019 onward, not an artifact.

The restricted-set elbow K (7 for 2016-2018, 8-9 for 2019-2023) corresponds to roughly this variable set, in MI-rank order:

- **2016-2018 (13 available variables):** `I10_NPR`, `I10_NDX`, `AGE`, `LOS`, `ELECTIVE`, `FEMALE`, `PAY1` (K=7)
- **2019-2023 (15-16 available variables):** `I10_NPR`, `I10_NDX`, `AGE`, `I10_SERVICELINE`, `LOS`, `PCLASS_ORPROC`, `ELECTIVE`, `PAY1`, `FEMALE` (K=7-9)

### Recommendation for the next modeling stage

Based on the above, for the eventual `CRC ~ STEROID_EXPOSURE + covariates` multivariable model:

1. **Do not include `DRG`, `DRG_NOPOA`, `MDC`, or `MDC_NOPOA`** as covariates in the adjusted STEROID_EXPOSURE model — they are close to circular with the outcome and would badly distort the STEROID_EXPOSURE odds ratio and its interpretation, not just inflate AUC.
2. **K ≈ 7-9 from the restricted ranking** is a reasonable, empirically-justified covariate set: `I10_NPR`, `I10_NDX`, `AGE`, `LOS`, `ELECTIVE`, `FEMALE`, `PAY1`, plus `I10_SERVICELINE`/`PCLASS_ORPROC` for years where available (2019+). This lines up with both the AUC-elbow and the BIC-minimizing K in nearly every year.
3. Note that `I10_NPR` and `I10_NDX` (procedure/diagnosis counts) are themselves partly downstream of the hospitalization's complexity/workup rather than pre-admission risk factors — worth a sensitivity analysis without them, since a "predictive" screening criterion (used here) and a "causally interpretable covariate" criterion (needed for the STEROID_EXPOSURE association) are not the same thing. This mirrors the general caveat already in progress report Section 9.4: univariate/predictive screening informs, but does not by itself determine, the final covariate set for a causal/associational model.

## Known Limitations

- **2021 excluded** — see [Data](#data). If a complete 2021 Core file becomes available, it can be added to `common.YEARS` and the whole pipeline (04→05→06→06b→07) re-run.
- **2016 has fewer diagnosis positions** (30 vs. 40 in 2017+), so the CRC/exclusion/steroid-exposure logic scans fewer diagnosis slots that year; this could very slightly undercount exclusions/exposure relative to later years.
- **`I10_SERVICELINE`, `PCLASS_ORPROC` unavailable 2016-2018; `PL_NCHS2` unavailable 2016-2022** (in this data pull) — the Top-K sweep for those years simply has fewer variables to rank/include, which is itself informative (see restricted-set results above) but means K is not on a perfectly common footing across all 7 years.
- **HCUP missing-value sentinel codes** (`-9`, `-99`, etc.) are **not** specially imputed or stripped in the Top-K encoding, consistent with how `03_feature_screening.py` already treated them — they are handled as literal category values for nominal variables, or left in place (then subject to row-wise `dropna()` only if truly `NaN`) for continuous variables.
- **AIC/BIC/pseudo-R² use a lightly L2-penalized single full-sample fit**, not a fully unpenalized MLE, because the unpenalized fit reliably fails to converge once near-duplicate one-hot pairs (e.g. `MDC` and `MDC_NOPOA` both present) are in the same model. This is documented in `topk_utils.py` and is a standard, low-bias workaround (`alpha=1e-6` is negligible next to typical logistic-regression coefficient scales).
- **No NIS survey-weighting** (`DISCWT`, `NIS_STRATUM`, `HOSP_NIS`) is incorporated into the Top-K models, consistent with the rest of the pipeline to date (see progress report Section 6.6/16.1) — these are unweighted, unclustered estimates.
- This stage is **predictive/screening**, not causal. The Top-K analysis identifies which covariates carry predictive information about CRC in this cohort; it does not establish that any of them (except by design, `STEROID_EXPOSURE`, which is not part of the 20-variable candidate set) cause or are risk factors for CRC.

## Dependencies

Install with:

```bash
pip install -r requirements.txt
```

- pandas, numpy, scipy — data handling and statistical tests
- scikit-learn (>=1.3, for `TargetEncoder`) — encoding, logistic regression, cross-validation
- statsmodels — univariate screening logistic regressions, AIC/BIC/pseudo-R² fits
- matplotlib, seaborn — figures
- joblib — parallelizes the Top-K sweep across K values within a year
- threadpoolctl — caps BLAS thread count per worker to avoid CPU oversubscription when joblib parallelizes across K (see `topk_utils.py`)

## Data Notes

- The raw HCUP NIS Core datasets are **not included** in this repository. They must be obtained separately from [HCUP](https://www.hcup-us.ahrq.gov/).
- Patient-level cohort files (`outputs/cohort.csv`, `outputs/cohort_principal_dx.csv`, `outputs/cohorts/cohort_<year>.csv`) are **excluded** from version control to protect patient privacy / data use agreement terms.
- Only summary-level outputs (variable/feature-screening results, Top-K sweep results, best-K summaries, cohort size summary, and figures) are tracked.
