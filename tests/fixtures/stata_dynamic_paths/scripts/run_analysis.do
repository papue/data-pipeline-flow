* 2a: c(pwd) system constant used to build a path
local datadir "`c(pwd)'/data"
use "`datadir'/analysis.dta", clear
save "`datadir'/results.dta", replace
