import pandas as pd
from bs4 import BeautifulSoup

# Read scraped HTML file
with open("../01_input/py_scraped_page.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
tables = pd.read_html(html)
df = tables[0]

df.to_parquet("../03_output/py_scraped_table.parquet")

# Write processed summary back to HTML
summary_html = df.describe().to_html()
with open("../03_output/py_scraped_summary.html", "w", encoding="utf-8") as f:
    f.write(summary_html)
