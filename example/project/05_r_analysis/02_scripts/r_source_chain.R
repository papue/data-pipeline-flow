library(readr)

# Config stored in a list
config <- list(
  input_dir  = "../01_input",
  output_dir = "../03_output",
  vintage    = "2024q4"
)

# Source shared helpers and data prep scripts
source("../02_scripts/r_helpers.R")
source("../02_scripts/r_clean_survey.R")
source("../02_scripts/r_merge_cohorts.R")

# Path constructed via paste0 with config values
out_path <- paste0(config$output_dir, "/r_final_", config$vintage, ".csv")
df_final <- run_pipeline(config$input_dir)   # function defined in r_helpers.R

write_csv(df_final, out_path)

# Path passed as a function argument
save_summary <- function(data, path) {
  write_csv(as.data.frame(summary(data)), path)
}
save_summary(df_final, file.path(config$output_dir, "r_source_chain_summary.csv"))
