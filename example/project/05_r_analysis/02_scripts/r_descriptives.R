library(readr)
library(ggplot2)

# Run upstream script
source("r_merge_cohorts.R")

# Read merged data using file.path
df <- read_csv(file.path("05_r_analysis/03_output", "r_cohorts_merged.csv"))

# Open PDF device via variable
fig_path <- "../03_output/r_descriptive_plots.pdf"
pdf(fig_path)
plot(df$outcome)
dev.off()

# Write summary table
summary_tbl <- as.data.frame(summary(df))
write_csv(summary_tbl, "../03_output/r_descriptives_table.csv")
