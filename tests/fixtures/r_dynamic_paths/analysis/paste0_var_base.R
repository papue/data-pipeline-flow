# Step 3: paste0 path building with variable base
base <- "../data"
path <- paste0(base, "/results.csv")
df <- read.csv(path)
