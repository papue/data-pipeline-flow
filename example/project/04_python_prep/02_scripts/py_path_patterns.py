import pandas as pd
import numpy as np
import zarr
from pathlib import Path

# pathlib.Path construction
BASE = Path("../03_output")
out_path = BASE / "py_path_test.parquet"

df = pd.read_csv("../01_input/py_census_data.csv")
df.to_parquet(out_path)

# Config dict holding paths
config = {
    "input_dir": "../01_input",
    "output_dir": "../03_output",
}
df2 = pd.read_csv(config["input_dir"] + "/py_survey_raw.csv")
df2.to_parquet(config["output_dir"] + "/py_survey_via_config.parquet")

# Path passed as function argument
def save_result(data, dest):
    data.to_parquet(dest)

save_result(df2, "../03_output/py_survey_fn_arg.parquet")

# Zarr array storage
z = zarr.open("../03_output/py_array_store.zarr", mode="w", shape=(1000, 10), dtype="f4")
z[:] = np.random.rand(1000, 10)
