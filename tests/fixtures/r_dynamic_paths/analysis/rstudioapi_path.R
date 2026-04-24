# Step 3: rstudioapi idiom (very common in interactive research scripts)
script_dir <- dirname(rstudioapi::getActiveDocumentContext()$path)
df <- read.csv(file.path(script_dir, "..", "data", "input.csv"))
