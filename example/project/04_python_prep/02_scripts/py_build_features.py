import pandas as pd
import matplotlib.pyplot as plt
import os

# Read merged panel via os.path.join
merged = pd.read_parquet(os.path.join("04_python_prep/03_output", "py_panel_merged.parquet"))

# Build features
merged["log_income"] = merged["income"].apply(lambda x: x ** 0.5)
merged["age_sq"] = merged["age"] ** 2

# Write features via variable
OUTFILE = "04_python_prep/03_output/py_features.parquet"
merged.to_parquet(OUTFILE)

# Save diagnostic figure
merged["log_income"].hist()
plt.savefig("../03_output/py_feature_distributions.png")
