# Step 3: data.table::fread with variable path
library(data.table)
path <- "../data/large_file.csv"
dt <- fread(path)
