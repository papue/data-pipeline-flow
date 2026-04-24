# Step 3: arrow parquet with variable path
library(arrow)
path <- "../data/results.parquet"
df <- read_parquet(path)
