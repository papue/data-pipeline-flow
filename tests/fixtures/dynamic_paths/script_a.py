import os, pandas as pd
base = "./results"
path = os.path.join(base, "output.parquet")
df.to_parquet(path)
