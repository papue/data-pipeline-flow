import os
import json

RESULTS_BASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "results", "demand_benchmark"
)

param_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "parameters", "param_file.json"
)
with open(param_file) as f:
    params = json.load(f)
