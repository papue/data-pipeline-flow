# 2d: Multi-line file.path() call
base_dir <- "../data"
data_path <- file.path(
  base_dir,
  "results.csv"
)
df <- read.csv(data_path)
