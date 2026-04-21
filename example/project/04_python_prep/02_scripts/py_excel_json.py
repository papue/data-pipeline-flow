import pandas as pd

# Excel with sheet name and openpyxl engine
raw = pd.read_excel("../01_input/py_admin_data.xlsx", sheet_name="2022", engine="openpyxl")

# Write Excel output
raw.to_excel("../03_output/py_admin_clean.xlsx", sheet_name="cleaned", index=False, engine="openpyxl")

# JSON round-trip
raw.to_json("../03_output/py_admin_records.json", orient="records", indent=2)
reloaded = pd.read_json("../03_output/py_admin_records.json", orient="records")
