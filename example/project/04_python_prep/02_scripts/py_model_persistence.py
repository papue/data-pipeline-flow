import pickle
import joblib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier

MODEL_DIR = "../03_output"

# Train a placeholder model
clf = RandomForestClassifier(n_estimators=100, random_state=42)

# Pickle save/load
with open(f"{MODEL_DIR}/py_rf_model.pkl", "wb") as f:
    pickle.dump(clf, f)
with open(f"{MODEL_DIR}/py_rf_model.pkl", "rb") as f:
    clf_loaded = pickle.load(f)

# Joblib save/load
joblib.dump(clf, f"{MODEL_DIR}/py_rf_model.joblib")
clf_jl = joblib.load(f"{MODEL_DIR}/py_rf_model.joblib")

# Numpy array persistence
arr = np.array([1.0, 2.0, 3.0])
np.save(f"{MODEL_DIR}/py_coefs.npy", arr)
arr_loaded = np.load(f"{MODEL_DIR}/py_coefs.npy")

# Save figure
fig, ax = plt.subplots()
ax.plot(arr_loaded)
fig.savefig(f"{MODEL_DIR}/py_coefs_plot.png", dpi=150)
