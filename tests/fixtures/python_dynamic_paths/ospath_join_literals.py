import os
import pandas as pd

# os.path.join with all literal args - no __file__, should work
df = pd.read_csv(os.path.join("data", "input.csv"))
