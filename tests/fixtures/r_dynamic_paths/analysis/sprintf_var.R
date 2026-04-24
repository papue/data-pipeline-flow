# Step 3: sprintf path building with variable base
base <- "../data"
path <- sprintf("%s/results_%s.csv", base, "final")
df <- read.csv(path)
