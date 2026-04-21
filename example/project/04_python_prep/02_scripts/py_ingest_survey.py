import pandas as pd

# Read from absolute path (raw source)
survey_raw = pd.read_csv("C:/data/raw/py_survey_raw.csv")

# Read from relative path (local input)
census = pd.read_csv("../01_input/py_census_data.csv")

# Merge and clean
merged = pd.concat([survey_raw, census], axis=0)
merged = merged.dropna()

# Write output via variable
OUTPUT_FILE = "../03_output/py_survey_clean.parquet"
merged.to_parquet(OUTPUT_FILE)
