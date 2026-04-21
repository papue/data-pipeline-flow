import pandas as pd

# Read model results from relative path
results = pd.read_csv("../03_output/py_model_results.csv")

# Read Excel template from absolute path
template = pd.read_excel("C:/data/templates/py_table_template.xlsx")

# Merge results into template layout
final = pd.concat([template, results], axis=1)

# Write final tables via variable
EXPORT = "../03_output/py_final_tables.xlsx"
final.to_excel(EXPORT)
