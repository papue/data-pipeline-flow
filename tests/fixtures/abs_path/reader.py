import os, pandas as pd
BASE = r"C:\Users\researcher\project\results"
df = pd.read_parquet(os.path.join(BASE, "output.parquet"))
