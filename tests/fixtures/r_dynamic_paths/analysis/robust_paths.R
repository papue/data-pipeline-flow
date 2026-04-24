# 2b: tryCatch fallback for script_dir
script_dir <- tryCatch(
  dirname(sys.frame(1)$ofile),
  error = function(e) getwd()
)
df <- read.csv(file.path(script_dir, "..", "data", "input.csv"))
