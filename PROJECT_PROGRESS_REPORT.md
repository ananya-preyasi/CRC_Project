# CRC Research Project — Progress Report

> **Project:** Association Between Chronic Corticosteroid Exposure and Colorectal Cancer in Adults Aged 18–49
> **Data Source:** HCUP National Inpatient Sample (NIS) 2023
> **Date:** 2026-08-18
> **Document Status:** Working draft — for review by research supervisor

---

## 1. Problem Statement and Research Objective

### 1.1 Clinical Background

Colorectal cancer (CRC) is a major cause of morbidity and mortality worldwide. While CRC incidence has been declining in older populations due to screening, rising incidence in younger adults (under age 50) has become a significant public health concern. Understanding modifiable or clinically relevant risk factors in this younger age group is an active area of research.

Chronic corticosteroid use is widespread across a range of autoimmune, inflammatory, and rheumatological conditions. Corticosteroids have complex immunomodulatory effects and their long-term use has been associated with various adverse outcomes. Whether chronic corticosteroid exposure is associated with colorectal cancer risk in younger adults is not well established.

### 1.2 Research Question

This project uses a retrospective cohort design based on the HCUP National Inpatient Sample (NIS) 2023 to investigate:

**Is chronic corticosteroid exposure associated with colorectal cancer (CRC) in adults aged 18–49, after adjusting for age, sex, insurance payer, income quartile, and elective admission status?**

> **Note:** A formal a priori hypothesis statement (e.g., directional hypothesis) is not currently documented in the repository. The hypothesis wording should be confirmed from project discussions. [Requires confirmation from project discussion]

### 1.3 Intended Variable Roles

| Role | Variable(s) | Description |
|------|-------------|-------------|
| **Outcome** | `CRC` | Binary indicator for colorectal cancer |
| **Primary Exposure** | `STEROID_EXPOSURE` | Binary indicator for chronic corticosteroid exposure |
| **Covariates** | `AGE`, `FEMALE`, `ELECTIVE`, `PAY1`, `ZIPINC_QRTL` | Demographic and admission characteristics used as adjustment variables |

### 1.4 Study Design

- **Design:** Retrospective observational study using HCUP NIS 2023 inpatient admission data.
- **Population:** Hospitalized adults aged 18–49 in the United States, 2023
- **Data source:** HCUP National Inpatient Sample (NIS) 2023 Core file
- **Unit of observation:** Individual hospital admission (each row represents one admission, identified by `KEY_NIS`)

---

## 2. Dataset

### 2.1 HCUP NIS 2023

The National Inpatient Sample (NIS) is the largest publicly available all-payer inpatient care database in the United States, maintained by the Healthcare Cost and Utilization Project (HCUP). The NIS is designed to approximate a 20% stratified sample of community hospitals in the US, producing national estimates of hospital utilization, outcomes, and costs.

The 2023 NIS Core file contains one row per hospital discharge (admission). Each row includes up to 40 diagnosis fields and 25 procedure fields coded in ICD-10-CM/PCS, along with patient demographics, admission characteristics, hospital identifiers, and discharge information.

### 2.2 File Used

| Property | Detail |
|----------|--------|
| File | `NIS_2023_Core.csv` |
| Location | External lab-server NIS dataset (path not included in repository) |
| Approximate size | ~1.83 million rows (age-filtered subset after initial processing) |
| Format | CSV |

> The raw HCUP data files are **not included** in the GitHub repository due to data use agreements and file size.

### 2.3 Key Variables in the Dataset

**Identifiers and survey design:**

| Variable | Description |
|----------|-------------|
| `KEY_NIS` | Unique admission identifier |
| `HOSP_NIS` | Hospital identifier |
| `NIS_STRATUM` | NIS stratum (survey design variable) |
| `DISCWT` | Discharge weight (survey weight) |

**Diagnosis and procedure fields:**

| Variables | Description |
|-----------|-------------|
| `I10_DX1` through `I10_DX40` | Up to 40 ICD-10-CM diagnosis codes per admission |
| `I10_PR1` through `I10_PR25` | Up to 25 ICD-10-PCS procedure codes per admission |
| `I10_NDX` | Number of diagnoses recorded |
| `I10_NPR` | Number of procedures recorded |

**Demographics and admission characteristics:**

| Variable | Description |
|----------|-------------|
| `AGE` | Patient age in years |
| `FEMALE` | Sex (binary) |
| `ELECTIVE` | Elective admission indicator |
| `PAY1` | Primary expected payer |
| `ZIPINC_QRTL` | Patient's zip code median household income quartile |
| `LOS` | Length of stay |
| `AWEEKEND` | Weekend admission indicator |
| `HCUP_ED` | Emergency department indicator |
| `I10_SERVICELINE` | Service line |
| `MDC` / `MDC_NOPOA` | Major Diagnostic Category |
| `DRG` / `DRG_NOPOA` | Diagnosis Related Group |
| `PL_NCHS2` | Patient location (NCHS urban-rural classification) |
| `TRAN_IN` / `TRAN_OUT` | Transfer in / transfer out indicators |

---

## 3. Initial Data Validation

### 3.1 Purpose

Before beginning cohort construction, a basic validation step was performed to confirm that each row in the NIS Core file represents a unique hospital admission — as expected by the dataset design.

### 3.2 Script

`scripts/00_check_dataset.py`

### 3.3 What Was Checked

The script loads the `KEY_NIS` and `HOSP_NIS` columns from the raw NIS Core file and verifies:

1. Whether every `KEY_NIS` value is unique (i.e., no duplicate admissions)
2. If duplicates exist, how many there are and what they look like

### 3.4 Implementation Notes

- The script runs at the module level (no `main()` function or `if __name__ == "__main__"` guard), meaning it would execute if imported as a module.
- Output is printed to the console only; no files are written.
- The script does not perform any transformations or produce any persistent artifacts.

### 3.5 Output

The validation confirmed whether each row represents a unique hospital admission. [The exact console output from the most recent run is not stored in the repository; results should be confirmed from the execution log if needed.] [Requires confirmation from project discussion]

---

## 4. Cohort Construction

### 4.1 Overview

The cohort construction script (`01_build_cohort.py`) reads the raw NIS 2023 Core file and applies a series of sequential filters and flagging operations to produce an analysis-ready cohort.

### 4.2 Pipeline

```
Raw NIS 2023 Core file (~44M rows in full NIS)
        ↓
   Age Restriction (18–49)
        ↓
   CRC Case Identification (principal diagnosis)
        ↓
   Exclusion Criteria (all 40 diagnosis positions)
        ↓
   Steroid Exposure Identification (all 40 diagnosis positions)
        ↓
   Save cohort_principal_dx.csv (~1,808,602 rows)
```

### 4.3 Step-by-Step Detail

#### Step 1: Load NIS Core

All columns of the NIS 2023 Core CSV are loaded into memory using `pandas.read_csv`. This includes all 127 variables (diagnosis codes, procedure codes, demographics, hospital identifiers, etc.).

#### Step 2: Age Restriction

**What:** Only patients aged 18 to 49 years (inclusive) are retained.

**Why:** The study focuses on young-to-middle-aged adults, a population for whom rising CRC incidence is of particular concern and for whom chronic corticosteroid exposure may be a relevant clinical factor.

**How:** Filtered using `AGE >= 18 AND AGE <= 49`.

**Result:** This reduces the full NIS dataset to approximately 1.83 million admissions. This is the **total analysis cohort** — not a CRC-only cohort. It includes both CRC cases and non-CRC admissions within the 18–49 age range.

> **Important:** The ~1.8 million rows in `cohort.csv` (~1,833,376) and `cohort_principal_dx.csv` (~1,808,602) represent the age-filtered population, not the number of CRC patients. The actual number of CRC cases within this cohort is determined by the subsequent CRC identification step and has not been reported in the current repository output.

#### Step 3: CRC Case Identification

**What:** A binary outcome variable `CRC` is created, set to `True` for admissions where the principal diagnosis code (`I10_DX1`) starts with a CRC-related ICD-10 code.

**Why:** CRC is the study outcome. Using the principal diagnosis ensures that CRC is the primary reason for the hospital admission.

**How:** The `I10_DX1` column is checked for codes starting with:

| ICD-10 Code | Anatomical Site |
|-------------|----------------|
| `C18` | Colon (all sub-sites) |
| `C19` | Rectosigmoid junction |
| `C20` | Rectum |

Missing values in `I10_DX1` are treated as empty strings before the prefix check.

**Design choice:** CRC is identified **only from the principal diagnosis (`I10_DX1`)**, not from any of the 40 diagnosis positions. This means admissions where CRC appears as a secondary diagnosis (e.g., a patient admitted for a CRC-related complication such as bowel obstruction or hemorrhage, where CRC is coded in a secondary position) are **not** classified as CRC cases under the current definition.

> This is a deliberate methodological choice. Its implications should be reviewed; it is possible that some clinically relevant CRC cases are excluded from the outcome definition. [Requires confirmation from project discussion]

#### Step 4: Exclusion Criteria

**What:** Admissions meeting any of the following exclusion criteria are removed from the cohort, regardless of the diagnosis position in which the code appears.

**Why:** These exclusions remove conditions that could confound the association between corticosteroid exposure and CRC, or that represent non-CRC neoplasms, hereditary syndromes, or conditions that independently require chronic corticosteroid treatment.

**How:** Each of the 40 diagnosis columns (`I10_DX1` through `I10_DX40`) is checked for codes starting with any exclusion prefix. If any diagnosis position matches, the admission is excluded.

| ICD-10 Prefix | Clinical Meaning |
|---------------|-----------------|
| `D12` | Benign neoplasm of colon |
| `C21` | Malignant neoplasm of anus |
| `C78.5` | Secondary malignant neoplasm of large intestine |
| `D13.91` | Colonic polyps (neoplastic, benign) |
| `Z15.09` | Genetic susceptibility to other malignant neoplasm |
| `Q85.89` | Other phakomatoses (e.g., Peutz-Jeghers syndrome) |
| `K50` | Crohn's disease (regional enteritis) |
| `K51` | Ulcerative colitis |

**Note on `K50` and `K51`:** Crohn's disease and ulcerative colitis are included as exclusion criteria because they are indications for chronic corticosteroid use and are independently associated with CRC risk. Including patients with IBD could introduce confounding in the analysis of steroid exposure and CRC. However, these same codes (`K50`, `K51`) also appear in the steroid exposure code list (see Section 5). The implications of this overlap are discussed in Section 13.

**Note on execution order:** Exclusions are applied *before* the steroid exposure flag is created. This means patients with IBD (K50/K51) are removed from the cohort before the steroid exposure variable is computed.

#### Step 5: Steroid Exposure Identification

**What:** A binary variable `STEROID_EXPOSURE` is created, set to `True` for admissions where any of the 40 diagnosis columns starts with a steroid-exposure-related ICD-10 code.

**Why:** This is the primary exposure variable of interest. Since NIS does not include pharmacy data, ICD-10 diagnosis codes for conditions that require chronic corticosteroid therapy are used as a proxy for corticosteroid exposure.

**How:** Each of the 40 diagnosis columns is checked for codes starting with any of the following prefixes:

| ICD-10 Code | Clinical Condition |
|-------------|-------------------|
| `Z79.52` | Long-term current use of corticosteroids |
| `M05` | Rheumatoid arthritis with rheumatoid factor |
| `M06` | Other rheumatoid arthritis |
| `M32` | Systemic lupus erythematosus |
| `M30` | Polyarteritis nodosa |
| `M31` | Other necrotizing vasculopathies |
| `M35.3` | Polymyalgia rheumatica |
| `M33` | Dermatopolymyositis |
| `M33.2` | Polymyositis |
| `L40.5` | Arthropathic psoriasis (psoriatic arthritis) |
| `M07` | Psoriatic and enteropathic arthropropathy |
| `D86` | Sarcoidosis |
| `G35` | Multiple sclerosis |
| `N04` | Nephrotic syndrome |
| `K75.4` | Autoimmune hepatitis (IgG4-related) |
| `Z94` | Organ transplant status (immunosuppression) |
| `K50` | Crohn's disease |
| `K51` | Ulcerative colitis |

**Note on `K50` and `K51`:** These IBD codes appear in both the exclusion and steroid exposure code lists. Because exclusions are applied before steroid exposure identification, IBD patients should be removed from the cohort before the steroid exposure flag is assigned. The effect of this ordering requires confirmation. [Requires confirmation from project discussion]

**Interpretation caveat:** The `STEROID_EXPOSURE` variable identifies patients with conditions associated with chronic corticosteroid use, not patients with confirmed corticosteroid prescriptions. This is a standard approach for administrative data studies where pharmacy records are unavailable, but it represents an indirect measure of exposure.

### 4.4 Output File

| Property | Detail |
|----------|--------|
| File | `outputs/cohort_principal_dx.csv` |
| Rows | ~1,808,602 |
| Columns | 127 original NIS columns + `CRC` (bool) + `STEROID_EXPOSURE` (bool) = 129 total |

---

## 5. Outcome and Exposure Definitions

### 5.1 Outcome: CRC

| Property | Detail |
|----------|--------|
| Variable name | `CRC` |
| Data type | Boolean (`True` / `False`) |
| Definition | `True` if `I10_DX1` starts with `C18`, `C19`, or `C20` |
| Interpretation | Admission with colorectal cancer as the principal diagnosis |

### 5.2 Primary Exposure: STEROID_EXPOSURE

| Property | Detail |
|----------|--------|
| Variable name | `STEROID_EXPOSURE` |
| Data type | Boolean (`True` / `False`) |
| Definition | `True` if any of `I10_DX1` through `I10_DX40` starts with any of the 18 steroid-exposure-related ICD-10 prefixes listed in Section 4.3, Step 5 |
| Interpretation | Admission for a condition associated with chronic corticosteroid use |

### 5.3 The K50/K51 Overlap Issue

**Observation:** The ICD-10 codes `K50` (Crohn's disease) and `K51` (ulcerative colitis) appear in **both** the `EXCLUSION_CODES` list and the `STEROID_EXPOSURE_CODES` list in the cohort construction script.

**Current execution order:**
1. Age restriction
2. CRC identification
3. **Exclusion criteria applied** (removes patients with K50 or K51 in any diagnosis position)
4. **Steroid exposure flag created** (checks for K50/K51 among other codes)

Because exclusions are applied *before* the steroid exposure flag, patients with a K50 or K51 code should be removed from the cohort before the `STEROID_EXPOSURE` variable is computed. In practice, this means the K50/K51 codes in the steroid exposure list should not match any patients who remain in the cohort.

**This execution order should be confirmed as intentional.** The presence of these codes in the steroid exposure list may be a legacy artifact or may serve as a safeguard if the processing order ever changes. [Requires confirmation from project discussion]

---

## 6. Initial Multivariate Logistic Regression

### 6.1 Overview

An initial multivariate logistic regression model was fit to estimate the association between chronic corticosteroid exposure and CRC, adjusting for a set of demographic and admission characteristics.

### 6.2 Script

`scripts/02_logistic_regression.py`

### 6.3 Model Specification

```
CRC ~ STEROID_EXPOSURE + AGE + FEMALE + ELECTIVE + PAY1 + ZIPINC_QRTL
```

| Variable | Role | Data Type | Coding |
|----------|------|-----------|--------|
| `CRC` | Dependent variable (outcome) | Boolean → integer (0/1) | 1 = CRC, 0 = No CRC |
| `STEROID_EXPOSURE` | Primary independent variable (exposure) | Boolean → integer (0/1) | 1 = Exposed, 0 = Not exposed |
| `AGE` | Covariate | Continuous | Age in years |
| `FEMALE` | Covariate | Binary | 1 = Female, 0 = Male |
| `ELECTIVE` | Covariate | Binary | 1 = Elective admission, 0 = Non-elective |
| `PAY1` | Covariate | Nominal | Primary expected payer (categorical) |
| `ZIPINC_QRTL` | Covariate | Ordinal | Zip-code median household income quartile |

A constant term (intercept) is included via `sm.add_constant()`.

### 6.4 Why Logistic Regression

Logistic regression is appropriate here because:
- The outcome (`CRC`) is binary
- The goal is to estimate the odds ratio for the primary exposure while adjusting for covariates
- Logistic regression naturally produces odds ratios, confidence intervals, and p-values for each predictor
- It is the standard approach for binary outcome analysis in epidemiological studies using administrative data

### 6.5 What the Script Computes

1. **Fits** a logistic regression model using `statsmodels.api.sm.Logit`
2. **Prints** the full model summary (coefficients, standard errors, z-statistics, p-values, pseudo R-squared)
3. **Computes** odds ratios by exponentiating the model coefficients (`np.exp(results.params)`)
4. **Computes** 95% confidence intervals for the odds ratios
5. **Prints** a table of odds ratios, confidence intervals, and p-values

### 6.6 What Has NOT Been Implemented

The following diagnostic and methodological elements are **not currently computed** by this script:

| Element | Status |
|---------|--------|
| Convergence diagnostics | Not implemented (beyond the default `results.summary()`) |
| Goodness-of-fit testing (e.g., Hosmer-Lemeshow) | Not implemented |
| Area Under the ROC Curve (AUC) | Not implemented |
| Classification accuracy at various thresholds | Not implemented |
| Calibration assessment | Not implemented |
| Variance Inflation Factor (VIF) / multicollinearity diagnostics | Not implemented |
| NIS survey design integration (sample weights, strata, clustering) | Not implemented |
| Robust or clustered standard errors | Not implemented |
| Sensitivity or subgroup analyses | Not implemented |

The current output is an initial, unweighted regression result. Whether survey-weighted analysis, model diagnostics, and sensitivity analyses are required before drawing conclusions should be determined by the research team.

### 6.7 Transition to Systematic Variable Screening

The initial logistic regression described above was an exploratory baseline analysis using a predefined set of six independent variables. Following review, concerns were raised that the variables included in that initial model were not sufficiently justified and that the broader set of available variables in the dataset should be examined more systematically before finalising the variable set for multivariable modelling.

As a result, the analysis moved back to the full set of 127 variables in the cohort dataset, which were profiled for data types, missingness, and variability (Section 7). Based on project discussion, 20 candidate variables were then identified for formal feature screening (Section 8). These 20 variables were screened using mutual information, chi-square tests, and univariate logistic regression as appropriate for their variable types (Sections 9–11).

The purpose of this screening stage is to provide a more systematic, evidence-based foundation for deciding which variables should enter the subsequent multivariable modelling stage. Feature screening does not replace logistic regression; rather, it informs the variable selection process that will precede the final multivariable model. The current next step is to determine a systematic Top-K feature-selection methodology by varying the number of retained variables and evaluating the resulting model (Section 14).

---

## 7. Variable Profiling

### 7.1 Purpose

Before selecting candidate variables for feature screening, all 127 variables in the cohort dataset were profiled to understand their data types, unique value distributions, missingness patterns, and appropriate variable type classifications. This profiling provides the foundation for determining which statistical tests are appropriate for each variable during feature screening.

### 7.2 Script

`scripts/03_profile_variables.py`

### 7.3 What Was Computed

For each of the 127 variables in the cohort, the script computes:

| Metric | Description |
|--------|-------------|
| Data type | The pandas dtype (e.g., `int64`, `float64`, `object`) |
| Raw unique values | Number of distinct values including HCUP missing codes |
| Valid unique values | Number of distinct values after excluding HCUP missing codes (`-9`, `-99`, `-999`, `-9999`) and `NaN` |
| Missing values | Count of `NaN` entries |
| Minimum | Minimum value (numeric variables only) |
| Maximum | Maximum value (numeric variables only) |
| Suggested variable type | Heuristic classification based on the rules below |

### 7.4 Classification Rules

The heuristic classifier assigns each variable to one of the following categories based on its properties:

| Priority | Condition | Classification |
|----------|-----------|---------------|
| 1 | Variable is `CRC` or `STEROID_EXPOSURE` | Outcome / Exposure |
| 2 | Variable is `KEY_NIS` or `HOSP_NIS` | Identifier |
| 3 | Number of valid unique values equals total rows | Identifier |
| 4 | Variable is `NIS_STRATUM` | Survey Design Variable |
| 5 | Variable name starts with `I10_DX` | Diagnosis Code |
| 6 | Variable name starts with `I10_PR` | Procedure Code |
| 7 | Data type is `object` (string) | Categorical (String) |
| 8 | Unique values ≤ 1 | Constant (Exclude) |
| 9 | Unique values = 2 | Binary |
| 10 | Unique values ≤ 10 | Ordinal / Nominal |
| 11 | Otherwise | Continuous |

### 7.5 Key Findings from Profiling

| Category | Count | Examples |
|----------|-------|----------|
| Total variables | 127 | — |
| Identifiers | 2 | `HOSP_NIS`, `KEY_NIS` |
| Constants (no variation) | 2 | `AGE_NEONATE`, `YEAR` |
| Survey design variable | 1 | `NIS_STRATUM` |
| Diagnosis code columns | 40 | `I10_DX1` through `I10_DX40` |
| Procedure code columns | 25 | `I10_PR1` through `I10_PR25` |
| Binary variables | several | `AWEEKEND`, `I10_DELIVERY`, `I10_MULTINJURY`, `PL_NCHS2`, `DRGVER` |
| Continuous variables | several | `AGE` (range 18–49), `LOS`, `I10_NDX`, `I10_NPR`, `DISCWT`, `TOTCHG_2023` |
| Ordinal/Nominal variables | several | `PAY1`, `ZIPINC_QRTL`, `ELECTIVE`, `FEMALE`, `I10_SERVICELINE` |
| Outcome/Exposure | 2 | `CRC`, `STEROID_EXPOSURE` |

**HCUP missing codes:** Many variables contain HCUP-specific missing/invalid codes (`-9`, `-99`, `-999`, `-9999`). The profiling script distinguishes between raw unique values (including these codes) and valid unique values (excluding them). Variables such as `AGE_NEONATE` have a raw unique value of 1 but a valid unique value of 0, because the only value present is the HCUP missing code `-9`.

### 7.6 Output

| Property | Detail |
|----------|--------|
| File | `outputs/variable_profile.csv` |
| Rows | 127 (one per variable) |
| Columns | Variable, Data Type, Raw Unique Values, Valid Unique Values, Missing Values, Minimum, Maximum, Suggested Variable Type |

This output is tracked in the repository.

> **Distinction:** The 127 variables profiled here include all NIS Core variables (diagnosis codes, procedure codes, identifiers, survey design variables, etc.). The subsequent feature screening step focuses on a subset of 20 candidate variables that were selected for their potential relevance to the research question (see Section 8).

---

## 8. Identification of Candidate Variables

### 8.1 From 127 to 20

The variable profiling step described in Section 7 characterized all 127 variables in the dataset. For the feature screening step, a set of 20 candidate variables was selected for formal statistical evaluation against the CRC outcome.

### 8.2 The 20 Candidate Variables

| Variable | Type | Description |
|----------|------|-------------|
| `AGE` | Continuous | Patient age in years |
| `AMONTH` | Ordinal | Admission month |
| `AWEEKEND` | Binary | Weekend admission indicator |
| `DQTR` | Ordinal | Discharge quarter |
| `DRG` | Nominal | Diagnosis Related Group |
| `DRG_NOPOA` | Nominal | DRG (diagnosis present on admission not considered) |
| `ELECTIVE` | Binary | Elective admission indicator |
| `FEMALE` | Binary | Sex |
| `HCUP_ED` | Binary | Emergency department indicator |
| `I10_NDX` | Continuous | Number of diagnoses |
| `I10_NPR` | Continuous | Number of procedures |
| `I10_SERVICELINE` | Nominal | Service line |
| `LOS` | Continuous | Length of stay |
| `MDC` | Nominal | Major Diagnostic Category |
| `MDC_NOPOA` | Nominal | MDC (diagnosis present on admission not considered) |
| `PAY1` | Nominal | Primary expected payer |
| `PCLASS_ORPROC` | Nominal | Procedure class (operating room) |
| `PL_NCHS2` | Ordinal | Patient location (NCHS urban-rural) |
| `TRAN_IN` | Binary | Transfer-in indicator |
| `ZIPINC_QRTL` | Ordinal | Zip-code income quartile |

### 8.3 Rationale for Variable Selection

> The repository documents the final set of 20 screened variables, but the complete historical rationale for narrowing the 127 profiled variables to these 20 is not encoded in the current repository. The reasoning behind excluding specific variables (e.g., all 40 individual diagnosis code columns, all 25 procedure code columns, identifiers, and survey design variables) and retaining these specific 20 should be confirmed from project discussions. [Requires confirmation from project discussion]

**Observations about the selected set:**
- All individual diagnosis codes (`I10_DX1`–`I10_DX40`) and procedure codes (`I10_PR1`–`I10_PR25`) are excluded — these are high-dimensional categorical variables not suitable for standard screening methods
- Identifiers (`KEY_NIS`, `HOSP_NIS`) are excluded
- The survey design variable (`NIS_STRATUM`) is excluded
- The outcome (`CRC`) and exposure (`STEROID_EXPOSURE`) are excluded from the screening predictor set (they are the variables being studied)
- Constants (`AGE_NEONATE`, `YEAR`) are excluded
- The resulting 20 variables are a mix of demographic, clinical, and hospital-level characteristics

---

## 9. Feature Screening Methodology

### 9.1 Purpose

Feature screening evaluates each candidate variable's association with the CRC outcome using appropriate univariate statistical tests. The goal is to quantify how much information each variable carries about the outcome, which informs downstream variable selection for the multivariable model.

### 9.2 Statistical Methods Applied

The choice of screening method depends on the variable type:

| Variable Type | Mutual Information | Chi-square | Univariate Logistic Regression |
|---------------|:------------------:|:----------:|:-----------------------------:|
| Continuous | Yes | No | Yes |
| Binary | Yes | Yes | Yes |
| Nominal | Yes | Yes | No |
| Ordinal | Yes | Yes | No |

### 9.3 Method Descriptions

#### Mutual Information (MI)

**What it measures:** Mutual Information quantifies the amount of information shared between a predictor variable and the outcome. It measures the reduction in uncertainty about the outcome given knowledge of the predictor.

**Interpretation:**
- MI ≥ 0; larger values indicate greater shared information (stronger dependency) between the predictor and outcome
- MI = 0 indicates complete statistical independence
- **MI values should not be interpreted as probabilities or percentages.** They are measured in units of information (nats, given the `sklearn` implementation used here)
- Raw MI values are primarily interpretable **comparatively** within the same analysis — a variable with MI = 0.03 provides more information about CRC than a variable with MI = 0.001, but the absolute magnitude does not have a standardized clinical meaning

**Implementation:** `sklearn.feature_selection.mutual_info_classif` with `random_state=42` for reproducibility.

**For continuous predictors:** MI is computed with `discrete_features=False`, treating the predictor as continuous.
**For categorical/binary predictors:** MI is computed with `discrete_features=True`, treating the predictor as discrete.

#### Chi-square Test of Independence

**What it measures:** The chi-square test evaluates whether there is a statistically significant association between a categorical predictor and the binary outcome. It compares the observed frequencies in a contingency table to the frequencies expected under the null hypothesis of independence.

**Interpretation:**
- A larger chi-square statistic indicates a greater departure from independence (i.e., a stronger observed association)
- **Raw chi-square statistics are not directly comparable across variables with different numbers of categories.** A variable with 5 categories will tend to produce larger chi-square values than a variable with 2 categories, all else being equal, because of the higher degrees of freedom
- The p-value provides evidence against the null hypothesis of independence
- The chi-square test does not indicate the direction or magnitude of association — only that an association exists

**Implementation:** `scipy.stats.chi2_contingency` applied to a contingency table of the predictor versus CRC status.

#### Univariate Logistic Regression

**What it measures:** A logistic regression model with a single predictor and the binary CRC outcome. This estimates the log-odds of CRC associated with a one-unit change in the predictor (or, for binary predictors, the difference between the two categories).

**Outputs:**
- **Odds Ratio (OR):** The multiplicative effect on the odds of CRC per one-unit increase in the predictor
  - OR > 1: Higher odds of CRC associated with higher values of the predictor
  - OR = 1: No association between the predictor and CRC odds
  - OR < 1: Lower odds of CRC associated with higher values of the predictor
- **95% Confidence Interval (CI):** The range within which the true population OR is expected to lie with 95% confidence. If the CI includes 1.0, the association is not statistically significant at the 0.05 level
- **P-value:** Evidence against the null hypothesis that the true OR = 1 (no association). A smaller p-value provides stronger evidence against the null

**For continuous predictors:** The OR represents the change in odds per one-unit increase in the predictor variable.
**For binary predictors:** The OR represents the ratio of odds between the two categories.

**Implementation:** `statsmodels.api.sm.Logit` with constant term, fitted via maximum likelihood.

### 9.4 Important Interpretive Notes

1. **Statistical significance ≠ practical importance.** A very small p-value (e.g., p < 0.001) indicates strong statistical evidence against the null hypothesis, but does not by itself indicate a large or clinically meaningful effect size. With ~1.8 million observations, even very small associations can be statistically significant.

2. **Effect size is separate from statistical evidence.** The odds ratio (magnitude of association) and the p-value (evidence against the null) should be interpreted together, not interchangeably.

3. **Univariate screening ≠ causal inference.** Feature screening identifies univariate associations and shared information. It does not establish causal relationships, account for confounding, or determine the final variable set for the multivariable model.

4. **Chi-square statistics are not directly comparable across variables** with different numbers of categories or different degrees of freedom. They should be interpreted within their category structure.

5. **MI values are comparable within this analysis** but their absolute magnitudes do not have a universal clinical interpretation.

---

## 10. Feature Screening Implementation

### 10.1 Scripts

| Script | Role |
|--------|------|
| `scripts/03_feature_screening.py` | Main screening pipeline: orchestrates variable iteration, validation, and output |
| `scripts/feature_screening_utils.py` | Utility functions: `run_chi_square`, `run_mutual_information`, `run_univariate_logistic_regression` |

### 10.2 Input

| Property | Detail |
|----------|--------|
| File | `outputs/cohort.csv` |
| Rows | ~1,833,376 |
| Columns | 129 (including `CRC` and `STEROID_EXPOSURE`) |

> **Note:** `03_feature_screening.py` reads from `cohort.csv`, while `01_build_cohort.py` writes to `cohort_principal_dx.csv`. See Section 13 for discussion of this discrepancy.

### 10.3 Missing Value Handling

All three utility functions handle missing values by applying `.dropna()` on the subset containing the predictor and outcome variables. This means:
- Patients with missing values in the predictor or outcome are excluded from that specific variable's screening analysis
- Different variables may have different effective sample sizes depending on their missingness patterns
- No imputation is performed

### 10.4 Configuration Validation

Before screening, `03_feature_screening.py` performs the following checks:
- Verifies the cohort file exists
- Creates the output directory if needed
- Confirms that every candidate variable has an assigned type in the `VARIABLE_TYPES` dictionary
- Confirms all assigned types are valid (one of: Continuous, Binary, Nominal, Ordinal)

### 10.5 Processing Loop

For each of the 20 candidate variables, the script:
1. Checks whether the variable exists in the dataset (skips if not found)
2. Looks up the variable's type from the hardcoded `VARIABLE_TYPES` dictionary
3. Applies the appropriate combination of statistical tests based on type
4. Collects results into a dictionary
5. Appends the result to a results list

### 10.6 Output

| Property | Detail |
|----------|--------|
| File | `outputs/feature_screening_results.csv` |
| Rows | 20 (one per candidate variable) |
| Sorting | By `mutual_information` in descending order |
| Rounding | All numeric columns rounded to 4 decimal places |

**Columns in the output CSV:**

| Column | Description |
|--------|-------------|
| `Variable` | Variable name |
| `Type` | Variable type (Continuous, Binary, Nominal, Ordinal) |
| `Tests Performed` | Description of which tests were applied |
| `odds_ratio` | Odds ratio from univariate logistic regression (NaN if not applicable) |
| `ci_lower` | Lower bound of 95% CI for OR (NaN if not applicable) |
| `ci_upper` | Upper bound of 95% CI for OR (NaN if not applicable) |
| `logistic_p` | P-value from logistic regression (NaN if not applicable) |
| `mutual_information` | Mutual information score |
| `chi_square` | Chi-square statistic (NaN if not applicable) |
| `chi_square_p` | Chi-square p-value (NaN if not applicable) |

---

## 11. Feature Screening Results

### 11.1 Complete Results Table

All 20 candidate variables, sorted by mutual information in descending order:

| Rank | Variable | Type | MI | Chi-square | Chi-sq p | OR | CI Lower | CI Upper | Logistic p |
|------|----------|------|----|-----------|----------|----|---------|---------|------------|
| 1 | I10_NPR | Continuous | 0.0343 | — | — | 1.1099 | 1.1029 | 1.1170 | 0.0 |
| 2 | I10_NDX | Continuous | 0.0186 | — | — | 1.0663 | 1.0629 | 1.0697 | 0.0 |
| 3 | AGE | Continuous | 0.0164 | — | — | 1.1584 | 1.1540 | 1.1628 | 0.0 |
| 4 | DRG | Nominal | 0.0099 | 251,517.5398 | 0.0 | — | — | — | — |
| 5 | DRG_NOPOA | Nominal | 0.0099 | 251,472.8179 | 0.0 | — | — | — | — |
| 6 | MDC | Nominal | 0.0057 | 43,210.9684 | 0.0 | — | — | — | — |
| 7 | MDC_NOPOA | Nominal | 0.0057 | 43,201.7196 | 0.0 | — | — | — | — |
| 8 | I10_SERVICELINE | Nominal | 0.0033 | 12,532.6714 | 0.0 | — | — | — | — |
| 9 | LOS | Continuous | 0.0013 | — | — | 1.0131 | 1.0117 | 1.0144 | 0.0 |
| 10 | FEMALE | Binary | 0.0004 | 1,677.5372 | 0.0 | 0.6306 | 0.6168 | 0.6448 | 0.0 |
| 11 | PAY1 | Nominal | 0.0003 | 987.0019 | 0.0 | — | — | — | — |
| 12 | PCLASS_ORPROC | Nominal | 0.0002 | 952.3872 | 0.0 | — | — | — | — |
| 13 | ELECTIVE | Binary | 0.0001 | 327.2888 | 0.0 | 1.4687 | 1.3983 | 1.5425 | 0.0 |
| 14 | ZIPINC_QRTL | Ordinal | 0.0001 | 207.1746 | 0.0 | — | — | — | — |
| 15 | AWEEKEND | Binary | 0.0 | 158.9850 | 0.0 | 0.6564 | 0.6147 | 0.7010 | 0.0 |
| 16 | PL_NCHS2 | Ordinal | 0.0 | 26.7959 | 0.0 | — | — | — | — |
| 17 | HCUP_ED | Binary | 0.0 | 19.8025 | 0.0005 | 0.9686 | 0.9363 | 1.0021 | 0.0657 |
| 18 | TRAN_IN | Binary | 0.0 | 18.4865 | 0.0003 | 1.0014 | 0.9733 | 1.0303 | 0.9233 |
| 19 | AMONTH | Ordinal | 0.0 | 13.4171 | 0.3395 | — | — | — | — |
| 20 | DQTR | Ordinal | 0.0 | 8.5990 | 0.0719 | — | — | — | — |

> "—" indicates the test was not applicable for that variable type (e.g., logistic regression not performed for nominal/ordinal variables; chi-square not computed for continuous variables).

### 11.2 Summary Observations

The following observations describe patterns in the screening results. **These are univariate findings and do not establish causal associations or determine the final variable set.**

1. **Highest MI variables:** `I10_NPR` (number of procedures, MI = 0.0343), `I10_NDX` (number of diagnoses, MI = 0.0186), and `AGE` (MI = 0.0164) have the highest mutual information with CRC, suggesting these variables share the most information with the outcome among the 20 screened.

2. **DRG/DRG_NOPOA and MDC/MDC_NOPOA:** These nominal variables have very large chi-square statistics (~251,000 and ~43,000 respectively), but this is expected given their high dimensionality (many categories). Their chi-square statistics are not directly comparable to those of variables with fewer categories. The near-identical values between DRG and DRG_NOPOA (and MDC and MDC_NOPOA) suggest these variable pairs carry highly overlapping information.

3. **Continuous variables with logistic regression:**
   - `AGE`: OR = 1.16 per year increase, suggesting higher age (within the 18–49 range) is associated with higher odds of CRC
   - `I10_NPR`: OR = 1.11 per additional procedure
   - `I10_NDX`: OR = 1.07 per additional diagnosis
   - `LOS`: OR = 1.01 per additional day — small per-day effect, but potentially meaningful over longer stays

4. **Binary variables with logistic regression:**
   - `FEMALE`: OR = 0.63, suggesting lower odds of CRC in females compared to males
   - `ELECTIVE`: OR = 1.47, suggesting higher odds of CRC in elective admissions
   - `AWEEKEND`: OR = 0.66, suggesting lower odds of CRC in weekend admissions
   - `HCUP_ED`: OR = 0.97, p = 0.0657 — does not reach the conventional 0.05 significance threshold
   - `TRAN_IN`: OR = 1.00, p = 0.9233 — no evidence of association

5. **Temporal variables:** `AMONTH` and `DQTR` have the lowest chi-square statistics and highest p-values (0.3395 and 0.0719), suggesting weak or no evidence of seasonal/quarterly patterns in CRC admissions.

### 11.3 Scope of Interpretation

Feature screening identifies univariate associations and shared information between individual predictors and the outcome. It does not:
- Establish causal relationships
- Account for confounding between variables
- Determine the final multivariable feature set
- Replace formal model-building or clinical judgment

The screening results inform, but do not dictate, subsequent variable selection decisions.

---

## 12. Interpretation Framework

This section provides a concise reference for interpreting the screening results presented in Section 11.

### 12.1 Mutual Information (MI)

| Interpretation | Meaning |
|---------------|---------|
| Higher MI | Greater shared information between the predictor and CRC outcome |
| MI = 0 | Complete statistical independence |
| Comparative use | Variables can be ranked by MI to compare their relative information content |

MI values should not be treated as probabilities or percentages. They are measures of statistical dependence, interpretable primarily in relative terms within the same analysis.

### 12.2 Chi-square Statistic

| Interpretation | Meaning |
|---------------|---------|
| Larger statistic | Greater departure from independence between categorical predictor and outcome |
| Caveat | Raw statistics depend on the contingency table structure and degrees of freedom; not directly comparable across variables with different category counts |

### 12.3 P-value

| Interpretation | Meaning |
|---------------|---------|
| Smaller p-value | Stronger evidence against the null hypothesis of no association |
| p < 0.05 | Conventionally considered statistically significant |
| Do not interpret | A small p-value does NOT imply a large effect size |

With ~1.8 million observations, even very small associations will tend to produce very small p-values. Statistical significance should be interpreted alongside effect size (OR) and confidence intervals.

### 12.4 Odds Ratio (OR)

| OR Value | Interpretation |
|----------|---------------|
| OR > 1 | Higher odds of CRC associated with higher values of the predictor |
| OR = 1 | No association between the predictor and CRC odds |
| OR < 1 | Lower odds of CRC associated with higher values of the predictor |

**For continuous predictors:** The OR represents the change in odds per one-unit increase in the predictor.
**For binary predictors:** The OR represents the ratio of odds between the two categories.

### 12.5 Confidence Interval (CI)

The 95% confidence interval provides the range within which the true population OR is expected to lie with 95% confidence. If the CI includes 1.0, the association is not statistically significant at the 0.05 level. Narrower intervals indicate more precise estimates.

### 12.6 Distinguishing Key Concepts

| Concept | What it tells you | What it does NOT tell you |
|---------|-------------------|--------------------------|
| **Effect size** (OR magnitude) | How strong the association is | Whether the association is statistically reliable |
| **Statistical evidence** (p-value) | How strong the evidence against the null is | How large or important the effect is |
| **Precision** (CI width) | How precisely the effect is estimated | Whether the effect is clinically meaningful |
| **Information content** (MI) | How much the predictor tells you about the outcome | Whether the predictor causes the outcome |

---

## 13. Important Data and Methodological Issues Identified

### 13.1 Cohort File Discrepancy: `cohort.csv` vs. `cohort_principal_dx.csv`

**What is observed:**
- `01_build_cohort.py` writes its output to `outputs/cohort_principal_dx.csv` (~1,808,602 rows)
- `02_logistic_regression.py` reads from `outputs/cohort_principal_dx.csv` (consistent with the cohort builder)
- `03_profile_variables.py` and `03_feature_screening.py` read from `outputs/cohort.csv` (~1,833,376 rows)

**Structural comparison:** Based on header inspection, `cohort.csv` and `cohort_principal_dx.csv` appear to have identical column structures. However, they differ in row count by approximately 24,774 rows.

**What is unknown:**
- Whether `cohort.csv` was created by a separate script not currently in the repository
- Whether `cohort.csv` is a renamed copy of a different version of the cohort
- Whether the row count difference represents excluded patients, a different processing step, or a different run of the cohort builder

**Why this matters:** If the two files contain different patient populations, the variable profiling and feature screening results (based on `cohort.csv`) may not correspond to the cohort used for logistic regression (based on `cohort_principal_dx.csv`). This should be reconciled before final modeling.

[Requires confirmation from project discussion]

### 13.2 K50/K51 Code Overlap

As described in Section 5.3, `K50` (Crohn's disease) and `K51` (ulcerative colitis) appear in both the exclusion codes and the steroid exposure codes. The current execution order (exclusion before exposure flagging) means IBD patients should be removed before the exposure variable is computed. Whether this ordering is fully correct and whether the IBD codes should be retained in the steroid exposure list should be confirmed.

### 13.3 Principal-Diagnosis-Only CRC Definition

The current CRC case definition relies solely on `I10_DX1` (principal diagnosis). Admissions where CRC is coded only in a secondary diagnosis position (e.g., `I10_DX2` through `I10_DX40`) are classified as non-CRC.

**This is a design choice, not necessarily an error.** It ensures that CRC is the primary reason for admission. However, it may exclude clinically relevant cases. Whether this definition is appropriate for the research question should be confirmed.

### 13.4 Variables Flagged for Possible Exclusion

From the variable profile, the following variables were identified as candidates for exclusion based on having no variation or being constants:
- `AGE_NEONATE`: Only value is `-9` (HCUP missing code); no valid variation; classified as "Constant (Exclude)"
- `YEAR`: Only value is `2023`; no variation; classified as "Constant (Exclude)"

These variables were not included in the 20-variable candidate set, which is consistent with their profiling results.

---

## 14. Current Feature-Selection Question

### 14.1 Context

With 20 variables screened and ranked, the immediate methodological question is: **How many and which of these candidate variables should be retained for the final multivariable model?**

### 14.2 Proposed Top-K Approach

The current methodological direction under discussion is a Top-K variable selection strategy:

1. **Rank** the 20 candidate variables by a chosen screening metric (e.g., decreasing mutual information).
2. **Select** the top K variables from the ranked list.
3. **Fit** the intended model (e.g., logistic regression) using those K variables.
4. **Evaluate** model performance at that K.
5. **Vary** K (e.g., K = 3, 5, 7, 10, ...) and repeat steps 3–4.
6. **Compare** model performance across different values of K.
7. **Determine** whether adding additional features beyond a certain point produces meaningful improvement, or whether performance plateaus.

This approach provides a structured way to balance model parsimony against explanatory power.

### 14.3 Distinction from Alternatives

The Top-K approach differs from a one-variable-at-a-time backward elimination strategy, where variables are removed one at a time based on, e.g., the highest p-value. The Top-K approach evaluates groups of variables at once, which may better capture the incremental value of adding multiple related variables simultaneously.

### 14.4 Open Questions

The following aspects of the Top-K approach have not yet been finalized:

| Question | Status |
|----------|--------|
| Exact ranking criterion (MI? Logistic p-value? Combined?) | Not finalized |
| Values of K to evaluate | Not finalized |
| Model to be fit at each K | Not finalized (likely logistic regression, but specification not confirmed) |
| Evaluation metric (AIC? BIC? AUC? Cross-validated performance?) | Not finalized |
| Whether to incorporate NIS survey design in the evaluation model | Not finalized |

> **This is the current methodological next step.** No code implementing the Top-K approach has been written. [Requires confirmation from project discussion]

---

## 15. Completed Milestones

| Milestone | Status |
|-----------|--------|
| Dataset validation (KEY_NIS uniqueness check) | Completed |
| Cohort construction (age restriction, CRC identification, exclusions, steroid exposure flagging) | Completed |
| Multivariate logistic regression (initial, unweighted) | Completed |
| Variable profiling (127 variables) | Completed |
| Candidate variable identification (20 variables selected) | Completed |
| Feature screening (20 variables, 3 statistical methods) | Completed |
| Feature screening results generated and saved | Completed |
| Variable profile generated and saved | Completed |
| Project documentation (PROJECT_STATUS_DRAFT.md) | Completed |
| GitHub repository setup (private, `ananya-preyasi/CRC_Project`) | Completed |
| .gitignore, requirements.txt, README.md | Completed |

---

## 16. Pending Work and Next Steps

### 16.1 Decisions Requiring Senior/Supervisor Input

| Decision | Description |
|----------|-------------|
| Final feature-selection methodology | Confirm whether Top-K approach or alternative is appropriate |
| Ranking criterion for Top-K | Confirm which screening metric to use for ranking variables |
| Range of K values to evaluate | Confirm the specific values of K to test |
| CRC definition scope | Confirm whether principal-diagnosis-only CRC definition is sufficient, or secondary diagnoses should be considered |
| K50/K51 overlap resolution | Confirm the intended handling of IBD codes in exclusion vs. exposure lists |
| Cohort file reconciliation | Confirm which of `cohort.csv` / `cohort_principal_dx.csv` is authoritative, and whether they should be unified |
| NIS survey design integration | Confirm whether survey-weighted analysis (using `DISCWT`, `NIS_STRATUM`, `HOSP_NIS`) is required before presenting results |
| Sensitivity analyses | Confirm which sensitivity/subgroup analyses are needed (e.g., age-stratified, sex-stratified, propensity score) |

### 16.2 Analysis Still to Be Implemented

| Item | Description |
|------|-------------|
| Top-K feature selection pipeline | Code to implement the iterative K-evaluation approach |
| Model evaluation metrics | AIC, BIC, AUC, or cross-validated performance at each K |
| Final multivariable model | The definitive regression model with the selected variable set |
| Multicollinearity diagnostics | VIF or correlation analysis for the final variable set |
| Model diagnostics | Goodness-of-fit, calibration, classification performance |
| Survey-weighted analysis | Incorporation of NIS sample weights, strata, and clustering (if required) |
| Sensitivity and subgroup analyses | As determined by supervisor |

### 16.3 Technical and Reproducibility Improvements

| Item | Description |
|------|-------------|
| Reconcile `cohort.csv` and `cohort_principal_dx.csv` | Determine provenance of both files and unify if appropriate |
| Add `main()` guard to `00_check_dataset.py` | Prevent module-level execution on import |
| Consider version pinning in `requirements.txt` | Ensure reproducible dependency versions |
| Populate `configs/` directory | Move hardcoded paths and parameters to configuration files |
| Consider pipeline orchestration | A single script to run all steps in sequence |

---

## 17. Repository and Reproducibility

| Property | Detail |
|----------|--------|
| Repository | `https://github.com/ananya-preyasi/CRC_Project` |
| Visibility | Private |
| Branch | `master` |
| Latest commit | `af912b9` — "Initial CRC analysis pipeline" |

### Tracked Files

| File | Description |
|------|-------------|
| `scripts/00_check_dataset.py` | Dataset validation |
| `scripts/01_build_cohort.py` | Cohort construction |
| `scripts/02_logistic_regression.py` | Multivariate logistic regression |
| `scripts/03_feature_screening.py` | Feature screening pipeline |
| `scripts/03_profile_variables.py` | Variable profiling |
| `scripts/feature_screening_utils.py` | Shared utility functions |
| `outputs/feature_screening_results.csv` | 20-variable screening results |
| `outputs/variable_profile.csv` | 127-variable profiling summary |
| `configs/` | Empty placeholder directory |
| `requirements.txt` | Python dependencies |
| `README.md` | Project overview and documentation |
| `.gitignore` | Excludes hospital-admission-level data, caches, editor backups |

### Excluded from Repository

| Item | Reason |
|------|--------|
| `outputs/cohort.csv` (~1.83M rows) | Hospital-admission-level data containing admission identifiers |
| `outputs/cohort_principal_dx.csv` (~1.81M rows) | Hospital-admission-level data containing admission identifiers |
| Raw HCUP NIS 2023 Core data | Not included per data use agreements; resides on external lab server |
| `scripts/__pycache__/` | Python bytecode cache |
| `scripts/*.py.save` | Editor backup files |

---

## Appendix A: Technical Details

The following software-engineering details are documented here for completeness. They do not affect the scientific validity of the current analysis but are relevant for future development.

| Item | Detail |
|------|--------|
| Hardcoded file paths | All scripts use absolute paths for raw data (external lab-server NIS dataset) and relative paths for outputs (`../outputs/...`). No configuration files are used. |
| `00_check_dataset.py` structure | The script executes at the module level without a `main()` function or `if __name__ == "__main__"` guard. Importing the file would trigger execution. |
| Variable type dictionaries | `03_feature_screening.py` uses a hardcoded `VARIABLE_TYPES` dictionary. `03_profile_variables.py` uses a separate heuristic classifier. The type names are not fully consistent between the two scripts (e.g., "Ordinal / Nominal" vs. "Ordinal", "Nominal"). |
| Version pinning | `requirements.txt` lists dependencies without version constraints. |
| Pipeline orchestration | There is no single script that runs all steps (validation → cohort → profiling → screening → regression) in sequence. Each script is run independently. |
| Empty `configs/` directory | The directory exists as a placeholder but contains no configuration files. |
| Absence of tests | No unit tests or integration tests exist for any of the scripts. |

---

*End of progress report.*
