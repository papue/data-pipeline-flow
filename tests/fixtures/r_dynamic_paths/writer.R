base_dir <- "./results"
df <- data.frame(x = 1:10)
write.csv(df, file.path(base_dir, "output.csv"))
