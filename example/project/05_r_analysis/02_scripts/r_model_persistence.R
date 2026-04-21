library(ggplot2)
library(readr)

df <- read_csv("../03_output/r_panel_clean.csv")

# Fit model and save entire workspace snapshot
fit_ols  <- lm(outcome ~ treat + age + female, data = df)
fit_iv   <- ivreg::ivreg(outcome ~ treat | instrument, data = df)

save(fit_ols, fit_iv, file = "../03_output/r_models.RData")

# Reload in a fresh session
load("../03_output/r_models.RData")

# Save cleaned data object as RDS
saveRDS(df, "../03_output/r_panel_final.rds")
df2 <- readRDS("../03_output/r_panel_final.rds")

# ggplot saved via ggsave
p <- ggplot(df2, aes(x = treat, y = outcome)) +
  geom_boxplot() +
  theme_minimal()

ggsave("../03_output/r_outcome_boxplot.png", plot = p, width = 8, height = 5, dpi = 300)
