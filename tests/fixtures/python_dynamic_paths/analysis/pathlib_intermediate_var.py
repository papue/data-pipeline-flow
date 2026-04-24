from pathlib import Path
import pandas as pd

this_file = Path(__file__)
project_root = this_file.parent.parent
df = pd.read_csv(project_root / "data" / "input.csv")
