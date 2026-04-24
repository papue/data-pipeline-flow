* 2e: /// line continuation in macro definition
local longpath ///
    "../data"
use "`longpath'/input.dta", clear
save "`longpath'/output.dta", replace
