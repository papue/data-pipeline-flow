import pandas as pd
import json
import subprocess

# Re-run feature builder
subprocess.run(["python", "py_build_features.py"])

# Read features via variable
INPUT = "../03_output/py_features.parquet"
features = pd.read_parquet(INPUT)

# Fit a simple OLS (stub)
results = features.describe().reset_index()

# Write results CSV
results.to_csv("../03_output/py_model_results.csv")

# Write JSON summary
summary = {"n_obs": len(features), "n_vars": features.shape[1]}
json.dump(summary, open("../03_output/py_model_summary.json", "w"))
