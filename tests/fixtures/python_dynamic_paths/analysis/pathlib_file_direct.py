from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent / ".." / "results"
df = pd.read_parquet(ROOT / "output.parquet")
