import pandas as pd
import importlib
from py_helpers import clean_data, build_index

# Local helper module import
df = pd.read_parquet("../01_input/py_raw_panel.parquet")
df = clean_data(df)
df = build_index(df, key_col="region_id")

df.to_parquet("../03_output/py_panel_indexed.parquet")

# Dynamically run another prep script via importlib
spec = importlib.util.spec_from_file_location("py_excel_json", "py_excel_json.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
