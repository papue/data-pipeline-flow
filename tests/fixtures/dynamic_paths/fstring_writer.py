import pickle

parameter = "run1"
seed = 42

for seed in range(10):
    result = {}
    with open(f"./results/{parameter}/result_{seed}.pkl", "wb") as f:
        pickle.dump(result, f)
