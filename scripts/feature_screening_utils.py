# feature_screening_utils.py

#Utility functions for performing feature screening on the HCUP cohort.

import numpy as np
import pandas as pd

from scipy.stats import chi2_contingency
from sklearn.feature_selection import mutual_info_classif
import statsmodels.api as sm


def run_chi_square(df, predictor, outcome="CRC"):
    """
    Performs a Chi-square test between a categorical predictor
    and the binary outcome.
    """

    subset = df[[predictor, outcome]].dropna()

    contingency_table = pd.crosstab(
        subset[predictor],
        subset[outcome]
    )

    try:

        chi2, p, _, _ = chi2_contingency(contingency_table)

        return {
            "chi_square": chi2,
            "chi_square_p": p
        }

    except Exception:

        return {
            "chi_square": np.nan,
            "chi_square_p": np.nan
        }


def run_mutual_information(
    df,
    predictor,
    outcome="CRC",
    discrete=True
):
    """
    Computes Mutual Information between a predictor
    and the binary outcome.
    """

    subset = df[[predictor, outcome]].dropna()

    X = subset[[predictor]]
    y = subset[outcome].astype(int)

    mi = mutual_info_classif(
        X,
        y,
        discrete_features=discrete,
        random_state=42
    )[0]

    return {
        "mutual_information": mi
    }


def run_univariate_logistic_regression(
    df,
    predictor,
    outcome="CRC"
):
    """
    Performs univariate logistic regression.
    """

    subset = df[[predictor, outcome]].dropna()

    if subset[outcome].nunique() < 2:

        return {
            "odds_ratio": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "logistic_p": np.nan
        }

    X = sm.add_constant(subset[predictor])
    y = subset[outcome].astype(int)

    try:

        model = sm.Logit(y, X).fit(disp=False)

        coefficient = model.params[predictor]

        odds_ratio = np.exp(coefficient)

        ci = np.exp(
            model.conf_int().loc[predictor]
        )

        p_value = model.pvalues[predictor]

        return {
            "odds_ratio": odds_ratio,
            "ci_lower": ci.iloc[0],
            "ci_upper": ci.iloc[1],
            "logistic_p": p_value
        }

    except Exception:

        return {
            "odds_ratio": np.nan,
            "ci_lower": np.nan,
            "ci_upper": np.nan,
            "logistic_p": np.nan
        }
