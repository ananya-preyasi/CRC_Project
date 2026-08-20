# topk_utils.py
#
# NOTE: BLAS thread count is capped at fit time via threadpoolctl (see
# evaluate_variable_set) because this module is used from joblib-parallelized
# loops over (year, K); without a cap, each LogisticRegression / statsmodels
# fit spawns its own OpenBLAS thread pool, and dozens of those running
# concurrently causes severe CPU oversubscription and much slower wall-clock
# time than running single-threaded per worker.
#
# Utilities for the Top-K feature-selection evaluation (06_topk_selection.py).
#
# Design notes
# ------------
# The 20 screened candidate variables mix very different shapes:
#   - continuous (AGE, LOS, I10_NDX, I10_NPR)
#   - binary (AWEEKEND, ELECTIVE, FEMALE, HCUP_ED, TRAN_IN)
#   - low-cardinality nominal/ordinal (<=50 categories: AMONTH, DQTR, PAY1,
#     ZIPINC_QRTL, PL_NCHS2, I10_SERVICELINE, PCLASS_ORPROC, MDC, MDC_NOPOA)
#   - high-cardinality nominal (>50 categories: DRG, DRG_NOPOA, ~750 codes)
#
# One-hot encoding DRG/DRG_NOPOA directly would add ~750 sparse dummy
# columns per variable to every model from K=4 onward, which is expensive
# and not really in the spirit of a "vary K, compare cost vs benefit"
# exercise. Instead, high-cardinality nominal variables are encoded with
# scikit-learn's TargetEncoder (smoothed, internally cross-fitted mean CRC
# rate per category), which keeps them to a single numeric column while
# still capturing their category-level signal. Bucket assignment is
# data-driven (by observed cardinality), not hardcoded per variable, so it
# adapts automatically if a given year's data differs.
#
# Because CRC is rare (well under 1% of the 18-49 cohort in every year),
# LogisticRegression is fit with class_weight="balanced" for the
# cross-validated performance metrics (ROC-AUC, PR-AUC).
#
# IMPORTANT INTERPRETIVE CAVEAT: DRG / DRG_NOPOA (and to a lesser extent
# MDC / MDC_NOPOA) are hospital-assigned billing/grouping codes computed
# FROM the discharge's own diagnosis codes -- including the CRC diagnosis
# itself when CRC is the principal diagnosis. Once DRG/DRG_NOPOA enters the
# Top-K model, CV AUC jumps to ~0.99+ (see topk_best_k_summary.csv / fig1).
# That is not a genuine "these admission characteristics predict CRC risk"
# signal; it is close to circular (the label leaking back in through a
# derived administrative code). See 06_topk_selection.py's "restricted"
# variant, which drops DRG/DRG_NOPOA/MDC/MDC_NOPOA to show the AUC-vs-K
# curve for the clinically interpretable variables only.
#
# The single full-sample statsmodels fit used for AIC/BIC/McFadden's
# pseudo-R2 uses plain (unweighted) MLE, consistent with 02_logistic_regression.py and
# 03_feature_screening.py elsewhere in this repo.

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder
from threadpoolctl import threadpool_limits

HIGH_CARDINALITY_THRESHOLD = 50
N_CV_FOLDS = 5
RANDOM_STATE = 42


def _target_encoder_cv():
    # A fresh generator per TargetEncoder instance (sklearn >=1.9 wants a CV
    # splitter here rather than the deprecated shuffle/random_state kwargs).
    return StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)


def bucket_variables(df, variables, continuous_variables, binary_variables):
    """
    Split `variables` into continuous / binary / one-hot / target-encode
    buckets. Continuous and binary membership come from the fixed
    definitions in common.py; the nominal/ordinal split between one-hot and
    target-encoding is data-driven, based on observed cardinality in `df`.
    """
    continuous_cols, binary_cols, onehot_cols, target_cols = [], [], [], []

    for v in variables:
        if v in continuous_variables:
            continuous_cols.append(v)
        elif v in binary_variables:
            binary_cols.append(v)
        else:
            n_unique = df[v].nunique(dropna=True)
            if n_unique > HIGH_CARDINALITY_THRESHOLD:
                target_cols.append(v)
            else:
                onehot_cols.append(v)

    return continuous_cols, binary_cols, onehot_cols, target_cols


def build_pipeline(continuous_cols, binary_cols, onehot_cols, target_cols):
    """
    Builds a Pipeline(ColumnTransformer -> LogisticRegression) for the given
    variable buckets. Empty buckets are omitted from the ColumnTransformer.
    """
    transformers = []
    if continuous_cols:
        transformers.append(("continuous", StandardScaler(), continuous_cols))
    if binary_cols:
        transformers.append(("binary", "passthrough", binary_cols))
    if onehot_cols:
        transformers.append((
            "onehot",
            OneHotEncoder(handle_unknown="ignore"),
            onehot_cols,
        ))
    if target_cols:
        transformers.append((
            "target",
            TargetEncoder(target_type="binary", cv=_target_encoder_cv()),
            target_cols,
        ))

    preprocessor = ColumnTransformer(transformers, remainder="drop")
    # max_iter is deliberately modest: once DRG/MDC-derived features enter
    # (see module docstring), the classes become almost perfectly separable
    # and lbfgs can grind through hundreds of iterations chasing a marginal
    # tolerance improvement instead of stopping once ranking quality (AUC) has
    # long since stabilized. A capped budget keeps runtime bounded across the
    # (year, K) grid without materially changing the reported AUC/PR-AUC.
    model = LogisticRegression(
        max_iter=200,
        class_weight="balanced",
        solver="lbfgs",
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def full_sample_statsmodels_fit(X_encoded, y):
    """
    Fits a logistic regression on the already-encoded design matrix for
    descriptive AIC / BIC / McFadden's pseudo-R2, via a very lightly
    L2-penalized MLE (alpha=1e-6, i.e. numerically indistinguishable from
    unpenalized MLE for well-conditioned K, but numerically stable when it
    isn't).

    An unpenalized sm.Logit(...).fit() was tried first during development,
    but at higher K the design matrix routinely contains near-duplicate
    one-hot pairs (MDC vs MDC_NOPOA, DRG vs DRG_NOPOA both entering the same
    model -- see the module docstring), which makes Newton-Raphson/BFGS spend
    minutes failing to converge before any fallback runs. Going straight to
    the penalized fit avoids that wasted compute entirely and is stable at
    every K. AIC/BIC/pseudo-R2 are computed from its log-likelihood in the
    usual way; this is a descriptive complement to the primary cross-validated
    AUC/PR-AUC metrics, not a held-out estimate.
    """
    X_const = sm.add_constant(np.asarray(X_encoded), has_constant="add")
    n_params = X_const.shape[1]
    n_obs = X_const.shape[0]

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg_result = sm.Logit(y, X_const).fit_regularized(
                alpha=1e-6, L1_wt=0.0, disp=False, maxiter=200
            )
            null_llf = sm.Logit(y, np.ones((n_obs, 1))).fit(disp=False, maxiter=50).llf
        llf = reg_result.llf
        aic = -2 * llf + 2 * n_params
        bic = -2 * llf + n_params * np.log(n_obs)
        pseudo_r2 = 1 - llf / null_llf
        return {"aic": aic, "bic": bic, "pseudo_r2_mcfadden": pseudo_r2, "converged": True}
    except Exception:
        return {"aic": np.nan, "bic": np.nan, "pseudo_r2_mcfadden": np.nan, "converged": False}



def evaluate_variable_set(df, variables, continuous_variables, binary_variables,
                           outcome="CRC", n_folds=N_CV_FOLDS):
    """
    Evaluates a logistic regression model built from `variables` predicting
    `outcome`, via stratified k-fold cross-validation (ROC-AUC, PR-AUC) plus
    a full-sample fit (AIC/BIC/pseudo-R2). Rows with missing values in any
    of the selected variables or the outcome are dropped (consistent with
    the dropna() convention used throughout feature_screening_utils.py).
    """
    subset = df[variables + [outcome]].dropna()
    y = subset[outcome].astype(int).to_numpy()
    X = subset[variables]

    n_obs = len(subset)
    n_cases = int(y.sum())

    if n_cases < n_folds or (len(y) - n_cases) < n_folds:
        return {
            "n_obs": n_obs, "n_cases": n_cases, "n_encoded_features": np.nan,
            "cv_auc_mean": np.nan, "cv_auc_std": np.nan,
            "cv_pr_auc_mean": np.nan, "cv_pr_auc_std": np.nan,
            "aic": np.nan, "bic": np.nan, "pseudo_r2_mcfadden": np.nan,
            "converged": False,
            "n_continuous": 0, "n_binary": 0, "n_onehot": 0, "n_target_encoded": 0,
        }

    continuous_cols, binary_cols, onehot_cols, target_cols = bucket_variables(
        X, variables, continuous_variables, binary_variables
    )
    pipeline = build_pipeline(continuous_cols, binary_cols, onehot_cols, target_cols)

    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_STATE)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # n_jobs=1 (and BLAS pinned to 1 thread below): parallelism happens
        # one level up, across (year, K) combinations in 06_topk_selection.py.
        # Nesting parallel CV folds *and* a parallel outer loop oversubscribes
        # the machine's cores and is dramatically slower in practice.
        with threadpool_limits(limits=1):
            cv_results = cross_validate(
                pipeline, X, y, cv=cv,
                scoring=["roc_auc", "average_precision"],
                n_jobs=1,
            )

    # Full-sample encoded matrix for AIC/BIC/pseudo-R2 (descriptive, not held-out).
    preprocessor = ColumnTransformer(
        [t for t in [
            ("continuous", StandardScaler(), continuous_cols) if continuous_cols else None,
            ("binary", "passthrough", binary_cols) if binary_cols else None,
            ("onehot", OneHotEncoder(handle_unknown="ignore"), onehot_cols) if onehot_cols else None,
            ("target", TargetEncoder(target_type="binary", cv=_target_encoder_cv()), target_cols) if target_cols else None,
        ] if t is not None],
        remainder="drop",
    )
    with threadpool_limits(limits=1):
        X_encoded = preprocessor.fit_transform(X, y)
        if hasattr(X_encoded, "toarray"):
            X_encoded = X_encoded.toarray()
        sm_fit = full_sample_statsmodels_fit(X_encoded, y)

    return {
        "n_obs": n_obs,
        "n_cases": n_cases,
        "n_encoded_features": X_encoded.shape[1],
        "cv_auc_mean": float(np.mean(cv_results["test_roc_auc"])),
        "cv_auc_std": float(np.std(cv_results["test_roc_auc"])),
        "cv_pr_auc_mean": float(np.mean(cv_results["test_average_precision"])),
        "cv_pr_auc_std": float(np.std(cv_results["test_average_precision"])),
        "aic": sm_fit["aic"],
        "bic": sm_fit["bic"],
        "pseudo_r2_mcfadden": sm_fit["pseudo_r2_mcfadden"],
        "converged": sm_fit["converged"],
        "n_continuous": len(continuous_cols),
        "n_binary": len(binary_cols),
        "n_onehot": len(onehot_cols),
        "n_target_encoded": len(target_cols),
    }
