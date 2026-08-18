import pandas as pd

CORE_FILE = "/NFSDISK/HCUP/2023/NIS_2023_Core.csv"

print("Loading dataset..")
df = pd.read_csv(CORE_FILE, usecols=["KEY_NIS", "HOSP_NIS"], low_memory=False)

print("\nTotal rows:", len(df))
print("Unique KEY_NIS:", df["KEY_NIS"].nunique())

if len(df) == df["KEY_NIS"].nunique():
	print("\nEvery row represents a unique hospital admission.")
else:
	print("\nDuplicate KEY_NIS values found.")
	print("Duplicate admissions:",
		len(df) - df["KEY_NIS"].nunique())

print("Checking duplicate KEY_NIS values..")
duplicates = df[df.duplicated(subset="KEY_NIS", keep=False)]

if duplicates.empty:
	print("No duplicate KEY_NIS values found.")
else:
	print(duplicates.head(20))
