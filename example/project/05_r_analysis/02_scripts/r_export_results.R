library(writexl)
library(jsonlite)
library(here)

# Read regression coefficients via here::here
coefs <- read_csv(here::here("05_r_analysis", "03_output", "r_regression_coefs.csv"))

# Read auxiliary estimates (absolute path)
aux <- readRDS("C:/projects/cache/r_auxiliary_estimates.rds")

results <- merge(coefs, aux, by = "term")

# Write final Excel output via variable
export_path <- "../03_output/r_final_results.xlsx"
write_xlsx(results, export_path)

# Write JSON summary
summary_list <- as.list(results)
write_json(summary_list, "../03_output/r_results_summary.json")
