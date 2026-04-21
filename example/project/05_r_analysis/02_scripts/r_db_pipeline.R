library(DBI)
library(RSQLite)
library(readr)

# Build DB path dynamically
db_dir  <- "../03_output"
db_path <- file.path(db_dir, "r_results.sqlite")

con <- dbConnect(SQLite(), db_path)

# Write main results table
results <- read_csv("../01_input/r_model_results.csv")
dbWriteTable(con, "model_results", results, overwrite = TRUE)

# Write lookup table
lookup <- read_csv("../01_input/r_region_lookup.csv")
dbWriteTable(con, "region_lookup", lookup, overwrite = TRUE)

# Read back with query
top10 <- dbGetQuery(con, "SELECT * FROM model_results ORDER BY estimate DESC LIMIT 10")

# Read full table
all_results <- dbReadTable(con, "model_results")

dbDisconnect(con)

write_csv(top10, "../03_output/r_top10_estimates.csv")
