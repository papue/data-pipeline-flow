import os
import json

_script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_script_dir, "..", "config", "params.json")) as f:
    config = json.load(f)
