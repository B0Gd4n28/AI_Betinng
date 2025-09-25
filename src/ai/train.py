
# Offline trainer scaffold (placeholder). Collect matches with outcomes + engineered features and fit a model.
import pandas as pd, numpy as np, joblib, os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

def train_model(csv_path:str, model_out:str="model/model.joblib"):
    df = pd.read_csv(csv_path)
    # expected columns (example): pH_odds, pD_odds, pA_odds, form_diff, is_home_strength, ... , y in {0,1,2}
    y = df["y"].values
    X = df.drop(columns=["y"]).values
    pipe = Pipeline([("scaler", StandardScaler()), ("lr", LogisticRegression(max_iter=1000, multi_class="multinomial"))])
    model = CalibratedClassifierCV(pipe, cv=3, method="isotonic")
    model.fit(X, y)
    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    joblib.dump(model, model_out)
    return model_out

if __name__=="__main__":
    import sys
    if len(sys.argv)<2: 
        print("Usage: python -m src.ai.train data/training.csv")
        raise SystemExit(1)
    path = sys.argv[1]
    out = train_model(path)
    print("Saved:", out)
