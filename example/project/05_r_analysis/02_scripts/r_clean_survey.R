library(readxl)
library(readr)

# Read raw survey data (absolute path)
df <- read.csv("C:/data/raw/r_survey_micro.csv")

# Read household weights (relative path)
weights <- read_xlsx("../01_input/r_household_weights.xlsx")

df <- merge(df, weights, by = "id")

# Save cleaned output via variable
out_file <- "../03_output/r_survey_cleaned.rds"
saveRDS(df, out_file)
