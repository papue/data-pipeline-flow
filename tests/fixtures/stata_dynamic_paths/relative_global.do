* Step 3: Relative path global joined with filename
global ddir "../data/"
use "${ddir}analysis.dta", clear
save "${ddir}cleaned.dta", replace
