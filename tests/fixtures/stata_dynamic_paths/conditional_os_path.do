* Step 3: Conditional os-based path (static parser cannot resolve branches)
if "`c(os)'" == "Windows" {
    global data "C:\project\data"
}
else {
    global data "/home/user/project/data"
}
use "$data\analysis.dta", clear
