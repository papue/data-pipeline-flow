# Step 3: Write variants with variable path
out <- "../output"
write.csv(df, file.path(out, "result.csv"))
saveRDS(model, file.path(out, "model.rds"))
