* Step 3: Concatenated global building
* Global built from another global (nested expansion)
global root "C:\project"
global data "$root\data"
use "$data\analysis.dta", clear
save "$data\processed.dta", replace
