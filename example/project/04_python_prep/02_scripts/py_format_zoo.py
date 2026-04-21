import pandas as pd
import pyreadstat

# Feather round-trip
df = pd.read_feather("../01_input/py_panel_clean.feather")
df["flag"] = df["score"] > 0.5
df.to_feather("../03_output/py_panel_flagged.feather")

# Stata .dta round-trip
stata_df = pd.read_stata("../01_input/py_survey.dta")
stata_df.to_stata("../03_output/py_survey_out.dta", write_index=False)

# SPSS .sav round-trip
spss_df, meta = pyreadstat.read_sav("C:/data/raw/py_spss_data.sav")
pyreadstat.write_sav(spss_df, "../03_output/py_spss_out.sav")

# HDF5
hdf_df = pd.read_hdf("../01_input/py_timeseries.h5", key="observations")
hdf_df.to_hdf("../03_output/py_timeseries_out.h5", key="observations", mode="w")
