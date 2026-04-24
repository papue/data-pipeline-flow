import os
import pickle

_script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(_script_dir, "..", "results", "model.pkl"), "rb") as fh:
    model = pickle.load(fh)
