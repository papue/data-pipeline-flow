library(here)
df <- read.csv(here("data", "raw.csv"))
saveRDS(model, here("results", "model.rds"))
