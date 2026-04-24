# Step 3: getSrcFilename() idiom
script_path <- getSrcFilename(function(){}, full.names=TRUE)
script_dir  <- dirname(script_path)
df <- read.csv(file.path(script_dir, "..", "data", "input.csv"))
