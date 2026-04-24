import pandas as pd, os
base = "./results"
df = pd.read_parquet(os.path.join(base, "data.parquet"))
