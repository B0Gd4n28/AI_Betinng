
"""
Training script for soccer prediction models supporting multiple markets.

Expected CSV format for training data:
- H2H (1X2) model: form_diff, home_form, away_form, odds_available, odds_p_home, odds_p_draw, odds_p_away, target_column (0=Home, 1=Draw, 2=Away)
- Totals (O/U) model: form_diff, home_form, away_form, target_line, combined_form, odds_available, odds_p_over, odds_p_under, target_column (0=Under, 1=Over)  
- BTTS model: form_diff, home_form, away_form, min_form, balanced_teams, odds_available, odds_p_yes, odds_p_no, target_column (0=No, 1=Yes)

The feature vector order is defined in src.ai.features_markets.create_feature_vector().
"""

import pandas as pd, numpy as np, joblib, os
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV


def train_model(csv_path: str, model_out: str = "model/model.joblib", market_type: str = "h2h"):
    """
    Train a model for the specified market type.
    
    Args:
        csv_path: Path to training CSV file
        model_out: Output path for trained model
        market_type: Type of market ('h2h', 'totals', 'btts')
        
    Returns:
        Path to saved model
    """
    df = pd.read_csv(csv_path)
    
    # Validate required columns based on market type
    if market_type == "h2h":
        expected_cols = ["form_diff", "home_form", "away_form", "odds_available", 
                        "odds_p_home", "odds_p_draw", "odds_p_away", "y"]
        classes = ["Home", "Draw", "Away"]
    elif market_type == "totals":
        expected_cols = ["form_diff", "home_form", "away_form", "target_line", "combined_form",
                        "odds_available", "odds_p_over", "odds_p_under", "y"]
        classes = ["Under", "Over"]
    elif market_type == "btts":
        expected_cols = ["form_diff", "home_form", "away_form", "min_form", "balanced_teams",
                        "odds_available", "odds_p_yes", "odds_p_no", "y"]
        classes = ["No", "Yes"]
    else:
        raise ValueError(f"Unknown market_type: {market_type}")
    
    # Check if required columns exist
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns for {market_type} model: {missing_cols}")
    
    # Prepare training data
    y = df["y"].values
    X = df[expected_cols[:-1]].values  # All columns except 'y'
    
    # Create pipeline with scaling and logistic regression
    if market_type == "h2h":
        # Multinomial for 3-class problem
        lr = LogisticRegression(max_iter=1000, multi_class="multinomial", random_state=42)
    else:
        # Binary classification for totals and btts
        lr = LogisticRegression(max_iter=1000, random_state=42)
    
    pipe = Pipeline([
        ("scaler", StandardScaler()), 
        ("lr", lr)
    ])
    
    # Use calibration for better probability estimates
    model = CalibratedClassifierCV(pipe, cv=3, method="isotonic")
    model.fit(X, y)
    
    # Save model
    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    joblib.dump(model, model_out)
    
    print(f"Trained {market_type} model with {len(X)} samples")
    print(f"Classes: {classes}")
    print(f"Feature importance (approximate): {np.abs(model.base_estimator.named_steps['lr'].coef_).mean(axis=0)}")
    
    return model_out


def create_sample_training_data(output_path: str, market_type: str = "h2h", n_samples: int = 1000):
    """
    Create sample training data for testing purposes.
    
    Args:
        output_path: Where to save the sample CSV
        market_type: Type of market ('h2h', 'totals', 'btts')
        n_samples: Number of sample rows to generate
    """
    np.random.seed(42)
    
    if market_type == "h2h":
        # Generate H2H sample data
        data = {
            "form_diff": np.random.normal(0, 1, n_samples),
            "home_form": np.random.uniform(0, 3, n_samples),
            "away_form": np.random.uniform(0, 3, n_samples),
            "odds_available": np.random.choice([0, 1], n_samples, p=[0.2, 0.8]),
            "odds_p_home": np.random.uniform(0.2, 0.6, n_samples),
            "odds_p_draw": np.random.uniform(0.15, 0.4, n_samples),
            "odds_p_away": np.random.uniform(0.2, 0.6, n_samples),
        }
        # Simulate target based on features (home advantage + form)
        home_prob = 0.4 + 0.1 * (data["form_diff"] > 0) + 0.2 * data["home_form"] / 3
        draw_prob = 0.3
        away_prob = 1 - home_prob - draw_prob
        data["y"] = [np.random.choice([0, 1, 2], p=[h, draw_prob, max(0.1, 1-h-draw_prob)]) 
                     for h in home_prob]
        
    elif market_type == "totals":
        # Generate totals sample data
        data = {
            "form_diff": np.random.normal(0, 1, n_samples),
            "home_form": np.random.uniform(0, 3, n_samples),
            "away_form": np.random.uniform(0, 3, n_samples),
            "target_line": np.full(n_samples, 2.5),
            "combined_form": np.random.uniform(0, 3, n_samples),
            "odds_available": np.random.choice([0, 1], n_samples, p=[0.2, 0.8]),
            "odds_p_over": np.random.uniform(0.3, 0.7, n_samples),
            "odds_p_under": np.random.uniform(0.3, 0.7, n_samples),
        }
        # Simulate target (Over if combined form is high)
        over_prob = 0.4 + 0.3 * (data["combined_form"] / 3)
        data["y"] = [1 if np.random.random() < p else 0 for p in over_prob]
        
    elif market_type == "btts":
        # Generate BTTS sample data
        data = {
            "form_diff": np.random.normal(0, 1, n_samples),
            "home_form": np.random.uniform(0, 3, n_samples),
            "away_form": np.random.uniform(0, 3, n_samples),
            "min_form": np.random.uniform(0, 3, n_samples),
            "balanced_teams": np.random.uniform(0, 1, n_samples),
            "odds_available": np.random.choice([0, 1], n_samples, p=[0.2, 0.8]),
            "odds_p_yes": np.random.uniform(0.3, 0.7, n_samples),
            "odds_p_no": np.random.uniform(0.3, 0.7, n_samples),
        }
        # Simulate target (BTTS Yes if teams are balanced and have good form)
        yes_prob = 0.3 + 0.4 * data["balanced_teams"] + 0.2 * (data["min_form"] / 3)
        data["y"] = [1 if np.random.random() < p else 0 for p in yes_prob]
    
    # Save to CSV
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Created sample {market_type} training data: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m src.ai.train <csv_path> [market_type] [model_out]")
        print("Market types: h2h, totals, btts")
        print("Example: python -m src.ai.train data/h2h_training.csv h2h model/h2h_model.joblib")
        print("To create sample data: python -m src.ai.train --sample data/sample_h2h.csv h2h")
        raise SystemExit(1)
    
    if sys.argv[1] == "--sample":
        # Create sample training data
        output_path = sys.argv[2] if len(sys.argv) > 2 else "data/sample_training.csv"
        market_type = sys.argv[3] if len(sys.argv) > 3 else "h2h"
        create_sample_training_data(output_path, market_type)
    else:
        # Train model
        csv_path = sys.argv[1]
        market_type = sys.argv[2] if len(sys.argv) > 2 else "h2h"
        model_out = sys.argv[3] if len(sys.argv) > 3 else f"model/{market_type}_model.joblib"
        
        trained_path = train_model(csv_path, model_out, market_type)
        print(f"Model saved: {trained_path}")
