import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import pickle

# -------------------------
# TRAINING DATA (FROM CSV)
# -------------------------
try:
    df = pd.read_csv("insurance_data.csv")
    print(f"Loaded {len(df)} rows for training.")
except FileNotFoundError:
    print("Error: insurance_data.csv not found. Run generate_data.py first.")
    exit()

X = df[["insurance_type","age","income","budget","cover"]]
y = df["policy"]

# -------------------------
# TRAIN MODEL
# -------------------------
model = DecisionTreeClassifier()
model.fit(X, y)

# -------------------------
# SAVE MODEL
# -------------------------
with open("ai_model.pkl", "wb") as f:
    pickle.dump(model, f)

print(f"✅ AI MODEL trained successfully on {len(df)} records.")

