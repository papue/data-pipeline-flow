* 2c: Global macro set to absolute path string
global datapath "C:\research\project\data"
use "$datapath\clean.dta", clear
save "$datapath\output.dta", replace
