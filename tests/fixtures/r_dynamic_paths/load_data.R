# 2c: Absolute path in variable, bare variable at call site
data_path <- "C:/project/data/results.csv"
df <- read.csv(data_path)
model_path <- "C:/project/models/fit.rds"
model <- readRDS(model_path)
