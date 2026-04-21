import pandas as pd

# Read panel inputs from relative paths
panel_a = pd.read_parquet("../01_input/py_panel_a.parquet")
panel_b = pd.read_parquet("../01_input/py_panel_b.parquet")

# Read legacy Stata file from absolute path
legacy = pd.read_stata("C:/projects/archive/py_legacy_panel.dta")

# Merge all panels
merged = pd.concat([panel_a, panel_b, legacy], axis=0)
merged = merged.reset_index(drop=True)

# Write merged output
merged.to_parquet("../03_output/py_panel_merged.parquet")
