library(readr)
library(ggplot2)

# Read input via variable
input_data <- "../03_output/r_cohorts_merged.csv"
df <- read_csv(input_data)

# Read model priors (absolute path)
priors <- readRDS("C:/data/r_model_priors.rds")

model <- lm(outcome ~ year, data = df)

# Save model object
saveRDS(model, "../03_output/r_regression_model.rds")

# Write coefficient table
coefs <- as.data.frame(coef(summary(model)))
write_csv(coefs, "../03_output/r_regression_coefs.csv")

# Save coefficient plot
p <- ggplot(coefs) + geom_point()
ggsave("../03_output/r_coef_plot.png")
