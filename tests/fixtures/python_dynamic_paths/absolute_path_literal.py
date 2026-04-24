import pandas as pd

# Absolute path passed directly as a literal string (no variable)
df = pd.read_csv(r"C:\project\data\input.csv")
df2 = pd.read_parquet("C:/project/results/all_results.parquet")
