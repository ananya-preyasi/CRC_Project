# This file will perform multivariate logisitic regression on the colorectal cancer cohort.
import pandas as pd
import statsmodels.api as sm
import numpy as np

COHORT_FILE = "../outputs/cohort_principal_dx.csv"

def load_cohort():
	print("Loading cohort..")
	df = pd.read_csv(COHORT_FILE)
	print(f"Loaded {len(df):,} patients.")
	return df

def run_logistic_regression(df):
	df["CRC"] = df["CRC"].astype(int)
	df["STEROID_EXPOSURE"] = df["STEROID_EXPOSURE"].astype(int)
	y = df["CRC"]
	X = df[
		[
			"STEROID_EXPOSURE",
			"AGE",
			"FEMALE",
			"ELECTIVE",
			"PAY1",
			"ZIPINC_QRTL"
		]
	]

	X = sm.add_constant(X)
	model = sm.Logit(y, X)
	results = model.fit()
	print(results.summary())
	# Now, we will print odds ratio.
	odds_ratios = np.exp(results.params)
	confidence_intervals = np.exp(results.conf_int())
	or_table = pd.DataFrame({
		"Odds Ratio": odds_ratios,
		"CI Lower": confidence_intervals[0],
		"CI Upper": confidence_intervals[1],
		"P-value": results.pvalues
	})

	print("\nOdds Ratios\n")
	print(or_table)

def main():
	df = load_cohort()
	run_logistic_regression(df)

if __name__ == "__main__":
	main()

