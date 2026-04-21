library(haven)
library(readr)

# Read cohort CSVs (relative paths)
cohort_2020 <- read_csv("../01_input/r_cohort_2020.csv")
cohort_2021 <- read_csv("../01_input/r_cohort_2021.csv")

# Read legacy cohort from Stata archive (absolute path)
legacy <- read_dta("C:/archive/r_legacy_cohort.dta")

merged <- rbind(cohort_2020, cohort_2021)

# Write merged output
write_csv(merged, "../03_output/r_cohorts_merged.csv")
