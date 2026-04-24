from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent / "data"
df = pd.read_csv(BASE / "input.csv")
