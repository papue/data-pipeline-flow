import pandas as pd

base = "results"
df = pd.read_parquet(f"{base}/all_results.parquet")
