# Step 3: here() package (already likely handled, testing)
library(here)
df <- read.csv(here("data", "input.csv"))
write.csv(df, here("output", "processed.csv"))
