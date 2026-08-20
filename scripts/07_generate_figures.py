"""
07_generate_figures.py

Generates the figures summarizing the multi-year Top-K feature-selection
analysis (06_topk_selection.py) and its screening/cohort inputs.

Figures written to figures/:
  fig1_auc_vs_k.png              CV ROC-AUC vs K, one line per year (primary/full variable set)
  fig2_prauc_vs_k.png            CV PR-AUC (average precision) vs K, per year
  fig3_bic_vs_k.png              BIC vs K, per year (parsimony view)
  fig4_auc_heatmap.png           Year x K heatmap of CV ROC-AUC
  fig5_mi_rank_heatmap.png       Variable x Year heatmap of MI-based rank
  fig6_best_k_summary.png        Best K per year (by AUC) vs elbow K, with AUC labels
  fig7_crc_rate_by_year.png      CRC cases per 100,000 admissions, by year (context)
  fig8_auc_vs_k_restricted.png   CV ROC-AUC vs K, restricted variable set (excludes DRG/MDC family)
  fig9_primary_vs_restricted.png Best AUC per year: primary vs restricted, side by side
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURE_DIR, OUTPUT_DIR, YEARS
from plot_style import (
    AXIS,
    BLUE_SEQUENTIAL_CMAP,
    CATEGORICAL,
    GRIDLINE,
    INK_MUTED,
    INK_PRIMARY,
    INK_SECONDARY,
    apply_base_style,
    year_color_map,
)

apply_base_style()

topk = pd.read_csv(f"{OUTPUT_DIR}/topk_results_all_years.csv")
best_k = pd.read_csv(f"{OUTPUT_DIR}/topk_best_k_summary.csv")
screening = pd.read_csv(f"{OUTPUT_DIR}/feature_screening_results_all_years.csv")
cohort_summary = pd.read_csv(f"{OUTPUT_DIR}/cohort_build_summary.csv")

YEAR_COLORS = year_color_map(YEARS)


def _line_with_band(ax, group, x_col, y_col, std_col, color, label):
    g = group.sort_values(x_col)
    ax.plot(g[x_col], g[y_col], color=color, linewidth=2, marker="o", markersize=4, label=label)
    if std_col in g.columns:
        ax.fill_between(g[x_col], g[y_col] - g[std_col], g[y_col] + g[std_col],
                         color=color, alpha=0.12, linewidth=0)


def _end_label(ax, group, x_col, y_col, color, text):
    g = group.sort_values(x_col)
    x_last = g[x_col].iloc[-1]
    y_last = g[y_col].iloc[-1]
    ax.annotate(f" {text}", (x_last, y_last), color=color, fontsize=9,
                va="center", ha="left", fontweight="bold")


# ----------------------------------------------------------------------
# Figure 1: CV ROC-AUC vs K
# ----------------------------------------------------------------------
# No end-of-line labels here: all 7 years converge to ~0.998 by K=7-9, so
# direct labels at the right edge collide into an unreadable stack. A legend
# plus the DRG/DRG_NOPOA callout (the actual story of this chart) do the job.
fig, ax = plt.subplots(figsize=(10, 6.5))
for year, group in topk.groupby("year"):
    color = YEAR_COLORS[year]
    _line_with_band(ax, group, "k", "cv_auc_mean", "cv_auc_std", color, str(year))

ax.axvline(3.5, color=INK_MUTED, linewidth=1, linestyle="--", zorder=1)
ax.annotate(
    "DRG / DRG_NOPOA enter the model here\n(hospital billing codes derived from\nthe diagnoses -- see caveat in README)",
    xy=(3.5, 0.86), xytext=(5.3, 0.78),
    fontsize=9, color=INK_SECONDARY,
    arrowprops=dict(arrowstyle="->", color=INK_MUTED, linewidth=1),
)

ax.set_xlabel("K (number of top-ranked variables included)")
ax.set_ylabel("Cross-validated ROC-AUC (5-fold, mean ± SD band)")
ax.set_title("Model discrimination (ROC-AUC) as K varies, by year\n(full 20-variable candidate set)", fontsize=13, pad=14)
ax.set_xlim(0.5, 20.7)
ax.legend(title="Year", loc="lower right", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig1_auc_vs_k.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 2: CV PR-AUC vs K
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6.5))
for year, group in topk.groupby("year"):
    color = YEAR_COLORS[year]
    _line_with_band(ax, group, "k", "cv_pr_auc_mean", "cv_pr_auc_std", color, str(year))
    _end_label(ax, group, "k", "cv_pr_auc_mean", color, str(year))

ax.set_xlabel("K (number of top-ranked variables included)")
ax.set_ylabel("Cross-validated PR-AUC / average precision (5-fold, mean ± SD band)")
ax.set_title("Precision-recall AUC as K varies, by year\n(CRC is a rare outcome, so PR-AUC is reported alongside ROC-AUC)",
              fontsize=13, pad=14)
ax.set_xlim(0.5, 20.7)
ax.legend(title="Year", loc="upper left", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig2_prauc_vs_k.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 3: BIC vs K (parsimony view)
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 6.5))
for year, group in topk.groupby("year"):
    color = YEAR_COLORS[year]
    g = group.sort_values("k")
    ax.plot(g["k"], g["bic"], color=color, linewidth=2, marker="o", markersize=4, label=str(year))
    _end_label(ax, group, "k", "bic", color, str(year))
    best_row = g.loc[g["bic"].idxmin()]
    ax.scatter([best_row["k"]], [best_row["bic"]], color=color, s=70, zorder=5,
               edgecolor=INK_PRIMARY, linewidth=0.8)

ax.set_xlabel("K (number of top-ranked variables included)")
ax.set_ylabel("BIC (lower is better; marker = minimum BIC per year)")
ax.set_title("Bayesian Information Criterion as K varies, by year", fontsize=13, pad=14)
ax.set_xlim(0.5, 20.7)
ax.legend(title="Year", loc="upper left", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig3_bic_vs_k.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 4: Year x K heatmap of CV AUC
# ----------------------------------------------------------------------
pivot = topk.pivot(index="year", columns="k", values="cv_auc_mean").sort_index(ascending=False)
fig, ax = plt.subplots(figsize=(11, 4.5))
im = ax.imshow(pivot.values, cmap=BLUE_SEQUENTIAL_CMAP, aspect="auto")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
ax.set_xlabel("K")
ax.set_ylabel("Year")
ax.set_title("Cross-validated ROC-AUC by year and K", fontsize=13, pad=14)
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        val = pivot.values[i, j]
        if not np.isnan(val):
            text_color = "white" if val > (pivot.values[~np.isnan(pivot.values)].min() +
                                            0.7 * (pivot.values[~np.isnan(pivot.values)].max() -
                                                   pivot.values[~np.isnan(pivot.values)].min())) else INK_PRIMARY
            ax.text(j, i, f"{val:.3f}", ha="center", va="center", fontsize=7, color=text_color)
cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
cbar.set_label("ROC-AUC")
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig4_auc_heatmap.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 5: Variable x Year heatmap of MI-based rank
# ----------------------------------------------------------------------
rank_pivot = screening.pivot(index="Variable", columns="Year", values="MI_Rank")
rank_pivot["_avg"] = rank_pivot.mean(axis=1, skipna=True)
rank_pivot = rank_pivot.sort_values("_avg").drop(columns="_avg")
rank_pivot = rank_pivot[sorted(rank_pivot.columns)]

fig, ax = plt.subplots(figsize=(8, 8.5))
im = ax.imshow(rank_pivot.values, cmap=BLUE_SEQUENTIAL_CMAP.reversed(), aspect="auto")
ax.set_xticks(range(len(rank_pivot.columns)))
ax.set_xticklabels(rank_pivot.columns)
ax.set_yticks(range(len(rank_pivot.index)))
ax.set_yticklabels(rank_pivot.index, fontsize=9)
ax.set_xlabel("Year")
ax.set_title("Mutual-information rank of each variable, by year\n(darker = higher-ranked / more informative that year)",
              fontsize=12, pad=14)
for i in range(rank_pivot.shape[0]):
    for j in range(rank_pivot.shape[1]):
        val = rank_pivot.values[i, j]
        if not np.isnan(val):
            ax.text(j, i, f"{int(val)}", ha="center", va="center", fontsize=7.5,
                    color=INK_PRIMARY if val > 10 else "white")
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig5_mi_rank_heatmap.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 6: Best K per year (by AUC) vs elbow K
# ----------------------------------------------------------------------
best_sorted = best_k.sort_values("year")
x = np.arange(len(best_sorted))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
bars1 = ax.bar(x - width / 2, best_sorted["best_k_by_auc"], width,
                color=CATEGORICAL["blue"], label="Best K (max CV AUC)")
bars2 = ax.bar(x + width / 2, best_sorted["elbow_k"], width,
                color=CATEGORICAL["aqua"], label="Elbow K (simplest model within 0.002 AUC of best)")

for bar, auc_val in zip(bars1, best_sorted["best_auc"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
            f"{auc_val:.3f}", ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)
for bar, auc_val in zip(bars2, best_sorted["auc_at_elbow_k"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
            f"{auc_val:.3f}", ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)

ax.set_xticks(x)
ax.set_xticklabels(best_sorted["year"])
ax.set_ylim(0, best_sorted["best_k_by_auc"].max() + 3)
ax.set_xlabel("Year")
ax.set_ylabel("K (number of variables)")
ax.set_title("Best-performing K vs. simplest near-equivalent K, by year\n(bar labels show the CV ROC-AUC at that K)",
              fontsize=12, pad=14)
ax.legend(loc="upper right", fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig6_best_k_summary.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 7: CRC rate per 100,000 admissions, by year (context)
# ----------------------------------------------------------------------
cohort_summary = cohort_summary.sort_values("year")
rate = cohort_summary["final_crc_cases"] / cohort_summary["final_cohort_rows"] * 100_000

fig, ax = plt.subplots(figsize=(9, 5.5))
bars = ax.bar(cohort_summary["year"].astype(str), rate, color=CATEGORICAL["blue"])
for bar, val, n in zip(bars, rate, cohort_summary["final_crc_cases"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
            f"{val:.1f}\n(n={n})", ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)

ax.set_xlabel("Year")
ax.set_ylabel("CRC cases per 100,000 eligible admissions (ages 18-49)")
ax.set_title("Early-onset CRC diagnosis rate in the analysis cohort, by year\n(2021 excluded: incomplete source file)",
              fontsize=12, pad=14)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig7_crc_rate_by_year.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 8: CV ROC-AUC vs K, restricted variable set (excludes DRG family)
# ----------------------------------------------------------------------
topk_restricted = pd.read_csv(f"{OUTPUT_DIR}/topk_restricted_results_all_years.csv")
best_k_restricted = pd.read_csv(f"{OUTPUT_DIR}/topk_restricted_best_k_summary.csv")

fig, ax = plt.subplots(figsize=(10, 6.5))
for year, group in topk_restricted.groupby("year"):
    color = YEAR_COLORS[year]
    _line_with_band(ax, group, "k", "cv_auc_mean", "cv_auc_std", color, str(year))
    _end_label(ax, group, "k", "cv_auc_mean", color, str(year))

ax.set_xlabel("K (number of top-ranked variables included)")
ax.set_ylabel("Cross-validated ROC-AUC (5-fold, mean ± SD band)")
ax.set_title(
    "Model discrimination (ROC-AUC) as K varies, by year\n"
    "(restricted set: excludes DRG, DRG_NOPOA, MDC, MDC_NOPOA)",
    fontsize=13, pad=14,
)
ax.set_xlim(0.5, 16.7)
ax.legend(title="Year", loc="lower right", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig8_auc_vs_k_restricted.png")
plt.close(fig)

# ----------------------------------------------------------------------
# Figure 9: Best AUC per year, primary (full set) vs restricted
# ----------------------------------------------------------------------
merged = best_k.merge(best_k_restricted, on="year", suffixes=("_primary", "_restricted"))
merged = merged.sort_values("year")
x = np.arange(len(merged))
width = 0.35

fig, ax = plt.subplots(figsize=(11, 6))
bars1 = ax.bar(x - width / 2, merged["best_auc_primary"], width,
                color=CATEGORICAL["blue"], label="Full 20-variable set (includes DRG/MDC)")
bars2 = ax.bar(x + width / 2, merged["best_auc_restricted"], width,
                color=CATEGORICAL["aqua"], label="Restricted set (excludes DRG/MDC family)")

for bar, val in zip(bars1, merged["best_auc_primary"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{val:.3f}", ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)
for bar, val in zip(bars2, merged["best_auc_restricted"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{val:.3f}", ha="center", va="bottom", fontsize=8, color=INK_SECONDARY)

ax.set_xticks(x)
ax.set_xticklabels(merged["year"])
ax.set_ylim(0, 1.08)
ax.set_xlabel("Year")
ax.set_ylabel("Best cross-validated ROC-AUC")
ax.set_title(
    "Best achievable AUC with vs. without DRG/MDC-family variables, by year\n"
    "(the gap is the circularity described in the DRG/MDC interpretive caveat)",
    fontsize=12, pad=14,
)
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9, ncol=1, frameon=False)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig9_primary_vs_restricted.png")
plt.close(fig)

print("Saved 9 figures to", FIGURE_DIR)
for fname in ["fig1_auc_vs_k.png", "fig2_prauc_vs_k.png", "fig3_bic_vs_k.png",
              "fig4_auc_heatmap.png", "fig5_mi_rank_heatmap.png",
              "fig6_best_k_summary.png", "fig7_crc_rate_by_year.png",
              "fig8_auc_vs_k_restricted.png", "fig9_primary_vs_restricted.png"]:
    print(" -", fname)
