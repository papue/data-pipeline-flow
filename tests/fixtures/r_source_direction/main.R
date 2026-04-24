source("helper.R")
result <- compute(data)
write.csv(result, "output.csv")
