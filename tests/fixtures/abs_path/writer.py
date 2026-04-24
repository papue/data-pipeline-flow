import os, pandas as pd
BASE = r"C:\Users\researcher\project\results"
df.to_parquet(os.path.join(BASE, "output.parquet"))
