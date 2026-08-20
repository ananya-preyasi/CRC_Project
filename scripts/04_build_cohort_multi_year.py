"""
04_build_cohort_multi_year.py

Generalizes 01_build_cohort.py (originally 2023-only) across every usable
NIS Core year (2016-2020, 2022-2023; 2021 excluded - see common.py).

For each year:
  1. Reads only the columns actually needed (diagnosis columns + the 20
     candidate variables + AGE), instead of all ~100-127 columns, since the
     raw Core files run 0.2-2.4 GB each.
  2. Applies the identical age filter / CRC definition / exclusion criteria /
     steroid exposure definition as 01_build_cohort.py, using however many
     diagnosis positions (I10_DX1-I10_DXn) that year's Core file actually
     has (30 for 2016, 40 for 2017 onward).
  3. Writes a reduced per-year cohort file containing only the candidate
     variables available that year, plus CRC and STEROID_EXPOSURE -- no
     diagnosis codes, admission IDs, or hospital IDs are retained, so these
     files are smaller and carry less re-identification risk than
     cohort_principal_dx.csv. They are still row-level derived data, so
     outputs/cohorts/ is excluded from version control (see .gitignore).

Years are built in parallel (one process per year) since each year is an
independent file and the machine has ample cores/RAM.

Output
------
outputs/cohorts/cohort_<year>.csv   (one per year)
outputs/cohort_build_summary.csv    (row counts / CRC counts / exposure
                                      counts / available variables per year)
"""

import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

from common import (
    CANDIDATE_VARIABLES,
    COHORT_DIR,
    CRC_CODES,
    EXCLUSION_CODES,
    OUTPUT_DIR,
    STEROID_EXPOSURE_CODES,
    YEARS,
    core_file,
)


def dx_column_count(year):
    # 2016 Core file only has 30 diagnosis positions; 2017 onward has 40.
    return 30 if year == 2016 else 40


def build_cohort_for_year(year):
    t0 = time.time()
    path = core_file(year)

    header = pd.read_csv(path, nrows=0).columns.tolist()
    header_set = set(header)

    n_dx = dx_column_count(year)
    dx_columns = [f"I10_DX{i}" for i in range(1, n_dx + 1) if f"I10_DX{i}" in header_set]

    available_candidates = [v for v in CANDIDATE_VARIABLES if v in header_set]
    missing_candidates = [v for v in CANDIDATE_VARIABLES if v not in header_set]

    usecols = sorted(set(dx_columns) | set(available_candidates) | {"AGE"})

    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    rows_raw = len(df)

    df = df[(df["AGE"] >= 18) & (df["AGE"] <= 49)]
    rows_age_filtered = len(df)

    df["CRC"] = (
        df["I10_DX1"].fillna("").astype(str).str.startswith(tuple(CRC_CODES))
    )
    crc_before_exclusion = int(df["CRC"].sum())

    exclusion_mask = pd.Series(False, index=df.index)
    for col in dx_columns:
        exclusion_mask |= (
            df[col].fillna("").astype(str).str.startswith(tuple(EXCLUSION_CODES))
        )
    n_excluded = int(exclusion_mask.sum())
    df = df[~exclusion_mask]
    rows_after_exclusion = len(df)

    exposure_mask = pd.Series(False, index=df.index)
    for col in dx_columns:
        exposure_mask |= (
            df[col].fillna("").astype(str).str.startswith(tuple(STEROID_EXPOSURE_CODES))
        )
    df["STEROID_EXPOSURE"] = exposure_mask

    out_columns = available_candidates + ["CRC", "STEROID_EXPOSURE"]
    df_out = df[out_columns].copy()
    df_out.insert(0, "YEAR", year)

    out_path = f"{COHORT_DIR}/cohort_{year}.csv"
    df_out.to_csv(out_path, index=False)

    elapsed = time.time() - t0

    summary = {
        "year": year,
        "rows_raw_age18_49_source": rows_raw,
        "rows_after_age_filter": rows_age_filtered,
        "crc_cases_before_exclusion": crc_before_exclusion,
        "rows_excluded_by_criteria": n_excluded,
        "final_cohort_rows": rows_after_exclusion,
        "final_crc_cases": int(df_out["CRC"].sum()),
        "final_steroid_exposed": int(df_out["STEROID_EXPOSURE"].sum()),
        "n_diagnosis_columns_used": len(dx_columns),
        "available_candidate_variables": len(available_candidates),
        "missing_candidate_variables": json.dumps(missing_candidates),
        "runtime_seconds": round(elapsed, 1),
    }
    print(
        f"[{year}] rows={rows_after_exclusion:,} CRC={summary['final_crc_cases']} "
        f"exposed={summary['final_steroid_exposed']} "
        f"({len(available_candidates)}/{len(CANDIDATE_VARIABLES)} candidate vars) "
        f"in {elapsed:.1f}s"
    )
    return summary


def main():
    print(f"Building cohorts for years: {YEARS}")
    summaries = []
    with ProcessPoolExecutor(max_workers=len(YEARS)) as executor:
        futures = {executor.submit(build_cohort_for_year, y): y for y in YEARS}
        for future in as_completed(futures):
            year = futures[future]
            try:
                summaries.append(future.result())
            except Exception as e:
                print(f"[{year}] FAILED: {e}")
                raise

    summary_df = pd.DataFrame(summaries).sort_values("year")
    summary_df.to_csv(f"{OUTPUT_DIR}/cohort_build_summary.csv", index=False)
    print("\nSaved cohort build summary to outputs/cohort_build_summary.csv")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
