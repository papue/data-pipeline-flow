import pandas as pd
import sqlite3
from sqlalchemy import create_engine

# Write to SQLite via sqlalchemy
engine = create_engine("sqlite:///C:/data/project.db")
df = pd.read_parquet("../03_output/py_features.parquet")
df.to_sql("features", engine, if_exists="replace", index=False)

# Read back via raw sqlite3
conn = sqlite3.connect("C:/data/project.db")
result = pd.read_sql("SELECT * FROM features WHERE year >= 2010", conn)
conn.close()

result.to_parquet("../03_output/py_db_extract.parquet")
