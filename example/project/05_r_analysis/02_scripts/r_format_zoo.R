library(arrow)
library(fst)
library(haven)
library(openxlsx)
library(jsonlite)
library(readr)

# Feather round-trip
df_feather <- read_feather("../01_input/r_panel_data.feather")
write_feather(df_feather, "../03_output/r_panel_clean.feather")

# FST round-trip
df_fst <- read.fst("../01_input/r_panel_data.fst")
write.fst(df_fst, "../03_output/r_panel_clean.fst", compress = 50)

# Stata / SPSS interchange
df_stata <- read_dta("../01_input/r_legacy_stata.dta")
write_dta(df_stata, "../03_output/r_legacy_converted.dta")

df_spss <- read_sav("C:/data/raw/r_spss_survey.sav")
write_sav(df_spss, "../03_output/r_spss_recoded.sav")

# Excel output
write.xlsx(df_stata, "../03_output/r_stata_export.xlsx", sheetName = "data")

# JSON round-trip
meta <- read_json("../01_input/r_metadata.json")
write_json(meta, "../03_output/r_metadata_updated.json", pretty = TRUE)

# readr csv
write_csv(df_feather, "../03_output/r_panel_clean.csv")
df_csv <- read_csv("../03_output/r_panel_clean.csv")
