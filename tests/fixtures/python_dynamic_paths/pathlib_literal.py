from pathlib import Path
import pandas as pd

p = Path("data/input.csv")
df = pd.read_csv(p)
