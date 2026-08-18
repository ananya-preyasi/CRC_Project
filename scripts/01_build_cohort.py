# The purpose of this file is to create the cohort (for colorectal cancer) using the HCUP NIS Core dataset.
import pandas as pd

CORE_FILE = "/NFSDISK/HCUP/2023/NIS_2023_Core.csv"
OUTPUT_FILE = "../outputs/cohort_principal_dx.csv"

DX_COLUMNS = [
	f"I10_DX{i}"
	for i in range(1, 41)
]

# Why are we creating these DX_COLUMNS?

CRC_CODES = [
	"C18",
	"C19",
	"C20",
]

EXCLUSION_CODES = [
	"D12",
	"C21",
	"C78.5",
	"D13.91",
	"Z15.09",
	"Q85.89",
	"K50",
	"K51",
]

# Why did we create these 2?

def load_core():
# This will load the HCUP NIS Core dataset.
	print("Loading HCUP NIS Core dataset..")
	df = pd.read_csv(CORE_FILE, low_memory=False)
	print(f"Loaded {len(df):,} patients.")

	return df

def filter_age(df):
# Keeps only those patients who fulfil the age criteria.
	print("Applying age filter..")
	df = df[(df["AGE"] >= 18) & (df["AGE"] <= 49)]
	print(f"Remaining patients: {len(df):,}")
	return df

def identify_crc_cases(df):
# Identify patients with colorectal cancer. A patient is considered a CRC case if ANY diagnosis column starts with C18, C19 or C20.
	print("Identifying CRC cases..")
	df["CRC"] = (
		df["I10_DX1"]
		.fillna("")
		.astype(str)
		.str.startswith(tuple(CRC_CODES))
	)
	print(f"CRC cases found: {df['CRC'].sum():,}")
	return df

def apply_exclusion_criteria(df):
# Remove patients meeting any exclusion criteria.
	print("Applying exclusion criteria..")
	exclusion_mask = pd.Series(False, index=df.index)
	for col in DX_COLUMNS:
		exclusion_mask |= (
			df[col]
			.fillna("")
			.astype(str)
			.str.startswith(tuple(EXCLUSION_CODES))
		)
	excluded = exclusion_mask.sum()
	print(f"Patients excluded: {excluded:,}")
	df = df[~exclusion_mask]
	print(f"Remaining patients: {len(df):,}")
	return df

STEROID_EXPOSURE_CODES = [
    "Z79.52",
    "M05",
    "M06",
    "M32",
    "M30",
    "M31",
    "M35.3",
    "M33",
    "M33.2",
    "L40.5",
    "M07",
    "D86",
    "G35",
    "N04",
    "K75.4",
    "Z94",
    "K50",
    "K51",
]

def identify_steroid_exposure(df):
# Identify patients with chronic corticosteroid exposure.
	print("Identifying steroid exposure..")
	exposure_mask = pd.Series(False, index=df.index)
	for col in DX_COLUMNS:
		exposure_mask |= (
			df[col]
			.fillna("")
			.astype(str)
			.str.startswith(tuple(STEROID_EXPOSURE_CODES))
		)

	df["STEROID_EXPOSURE"] = exposure_mask
	print(f"Exposed patients: {df['STEROID_EXPOSURE'].sum():,}")
	return df

def main():
	df = load_core()
	df = filter_age(df)
	df = identify_crc_cases(df)
	df = apply_exclusion_criteria(df)
	df = identify_steroid_exposure(df)
	df.to_csv(OUTPUT_FILE, index=False)
	print("Age-filtered cohort has been saved.")
if __name__ == "__main__":
	main()
