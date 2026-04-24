* Step 3: Nested macro expansion (global built from two other globals)
global root "C:\project"
global sub "analysis"
global full "$root\$sub\results.dta"
use "$full", clear
