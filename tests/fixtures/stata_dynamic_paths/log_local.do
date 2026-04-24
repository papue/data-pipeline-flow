* Step 3: log using with local macro path
local logdir "../logs"
log using "`logdir'/run.log", replace text
use "../data/analysis.dta", clear
save "../data/logged_output.dta", replace
