* 2b: c(current_do_file) to get running script path (Stata 16+)
local mydir = subinstr("`c(current_do_file)'", "/scripts/script_relative.do", "", .)
use "`mydir'/data/clean.dta", clear
