import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainModel")

# Try to import xgboost
XGB_AVAILABLE = False
try:
    from xgboost import XGBClassifier
    XGB_AVAILABLE = True
    logger.info("XGBoost is available for training.")
except ImportError:
    logger.warning("XGBoost is not installed. Training will fall back to Random Forest.")

def generate_synthetic_data(num_samples=2000):
    """Generates synthetic health metrics and assigns risk labels based on criteria."""
    np.random.seed(42)
    
    heart_rates = np.random.uniform(35, 160, num_samples)
    systolic_bps = np.random.uniform(80, 200, num_samples)
    diastolic_bps = np.random.uniform(50, 130, num_samples)
    spo2_values = np.random.uniform(80, 100, num_samples)
    sleep_hours = np.random.uniform(3, 10, num_samples)
    steps_values = np.random.randint(500, 18000, num_samples)
    
    data = pd.DataFrame({
        "heart_rate": heart_rates,
        "systolic_bp": systolic_bps,
        "diastolic_bp": diastolic_bps,
        "spo2": spo2_values,
        "sleep_hours": sleep_hours,
        "steps": steps_values
    })
    
    # Assign labels based on logic
    labels = []
    for _, row in data.iterrows():
        hr, sys, dia, spo2 = row["heart_rate"], row["systolic_bp"], row["diastolic_bp"], row["spo2"]
        
        # High Risk Conditions
        if spo2 < 90.0 or hr > 130.0 or hr < 40.0 or sys > 180.0 or dia > 120.0:
            labels.append("High")
        # Medium Risk Conditions
        elif (90.0 <= spo2 < 94.0) or (100.0 < hr <= 130.0) or (140.0 < sys <= 180.0) or (90.0 < dia <= 120.0):
            labels.append("Medium")
        # Low Risk
        else:
            labels.append("Low")
            
    data["risk_level"] = labels
    return data

def train_and_save_models():
    """Trains the Random Forest and XGBoost classifiers and saves them to disk."""
    # Ensure directory exists
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(model_dir, exist_ok=True)
    
    # Generate data
    df = generate_synthetic_data(3000)
    X = df.drop(columns=["risk_level"])
    y = df["risk_level"]
    
    # Encode Target Labels
    # 'Low' -> 0, 'Medium' -> 1, 'High' -> 2
    # Ensure consistent mapping
    label_mapping = {"Low": 0, "Medium": 1, "High": 2}
    y_encoded = y.map(label_mapping)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)
    
    # 1. Train Random Forest
    logger.info("Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    rf_acc = rf_model.score(X_test, y_test)
    logger.info(f"Random Forest accuracy: {rf_acc:.4f}")
    
    rf_path = os.path.join(model_dir, "rf_model.joblib")
    joblib.dump(rf_model, rf_path)
    logger.info(f"Random Forest model saved to {rf_path}")
    
    # 2. Train XGBoost
    xgb_path = os.path.join(model_dir, "xgb_model.joblib")
    if XGB_AVAILABLE:
        try:
            logger.info("Training XGBoost Classifier...")
            xgb_model = XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
            xgb_model.fit(X_train, y_train)
            xgb_acc = xgb_model.score(X_test, y_test)
            logger.info(f"XGBoost accuracy: {xgb_acc:.4f}")
            joblib.dump(xgb_model, xgb_path)
            logger.info(f"XGBoost model saved to {xgb_path}")
        except Exception as e:
            logger.error(f"Failed to train XGBoost: {e}. Falling back to copying Random Forest as XGBoost surrogate.")
            joblib.dump(rf_model, xgb_path)
    else:
        # Save RF model as XGBoost surrogate to keep code happy
        logger.info("Copying Random Forest as fallback XGBoost surrogate model.")
        joblib.dump(rf_model, xgb_path)
        
    logger.info("Model training process completed successfully!")

if __name__ == "__main__":
    train_and_save_models()
