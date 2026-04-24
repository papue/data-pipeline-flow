from pathlib import Path
import pandas as pd

# Path() / "literal" chain - all literals, no __file__
df = pd.read_csv(Path("data") / "input.csv")
