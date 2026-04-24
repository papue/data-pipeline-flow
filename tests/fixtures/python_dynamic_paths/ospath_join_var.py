import os
import pandas as pd

base = "data"
path = os.path.join(base, "input.csv")
df = pd.read_csv(path)
