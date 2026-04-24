# Step 3: haven for Stata files with variable path
library(haven)
path <- "../data/survey.dta"
df <- read_dta(path)
