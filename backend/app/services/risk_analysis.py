import os
import joblib
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger("RiskAnalysisService")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RF_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "rf_model.joblib")
XGB_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "xgb_model.joblib")

# Label mappings
RISK_LABELS = {0: "Low", 1: "Medium", 2: "High"}

# Placeholders for loaded models
rf_model = None
xgb_model = None

def load_models():
    """Loads trained ML models from the filesystem."""
    global rf_model, xgb_model
    try:
        if os.path.exists(RF_MODEL_PATH):
            rf_model = joblib.load(RF_MODEL_PATH)
            logger.info("Random Forest risk model loaded successfully.")
        else:
            logger.warning(f"Random Forest model not found at {RF_MODEL_PATH}. Running in heuristic fallback mode.")

        if os.path.exists(XGB_MODEL_PATH):
            xgb_model = joblib.load(XGB_MODEL_PATH)
            logger.info("XGBoost risk model loaded successfully.")
        else:
            logger.warning(f"XGBoost model not found at {XGB_MODEL_PATH}. Running in heuristic fallback mode.")
    except Exception as e:
        logger.error(f"Error loading machine learning models: {e}. Falling back to heuristics.")

def heuristic_predict(heart_rate: float, systolic_bp: float, diastolic_bp: float, spo2: float) -> tuple:
    """Fallback rule-based risk classification engine."""
    # High Risk
    if spo2 < 90.0 or heart_rate > 130.0 or heart_rate < 40.0 or systolic_bp > 180.0 or diastolic_bp > 120.0:
        return "High", 0.99, 0.99
    # Medium Risk
    elif (90.0 <= spo2 < 94.0) or (100.0 < heart_rate <= 130.0) or (40.0 <= heart_rate < 50.0) or (140.0 < systolic_bp <= 180.0) or (90.0 < diastolic_bp <= 120.0):
        return "Medium", 0.85, 0.85
    # Low Risk
    else:
        return "Low", 0.95, 0.95

def predict_health_risk(
    heart_rate: float,
    systolic_bp: float,
    diastolic_bp: float,
    spo2: float,
    sleep_hours: float,
    steps: int
) -> dict:
    """
    Evaluates health parameters using Random Forest and XGBoost.
    If models are not pre-trained/loaded, falls back to clinical heuristics.
    """
    global rf_model, xgb_model
    
    # Try loading if not done yet
    if rf_model is None or xgb_model is None:
        load_models()
        
    # Heuristic fallback if models still unavailable
    if rf_model is None or xgb_model is None:
        risk, rf_conf, xgb_conf = heuristic_predict(heart_rate, systolic_bp, diastolic_bp, spo2)
        return {
            "risk_level": risk,
            "rf_confidence": rf_conf,
            "xgb_confidence": xgb_conf,
            "timestamp": datetime.now()
        }
        
    try:
        # Prepare feature vector (must match training feature order):
        # ["heart_rate", "systolic_bp", "diastolic_bp", "spo2", "sleep_hours", "steps"]
        features = np.array([[heart_rate, systolic_bp, diastolic_bp, spo2, sleep_hours, steps]])
        
        # 1. Random Forest Prediction
        rf_probs = rf_model.predict_proba(features)[0]
        rf_class = int(np.argmax(rf_probs))
        rf_conf = float(rf_probs[rf_class])
        rf_risk = RISK_LABELS.get(rf_class, "Low")
        
        # 2. XGBoost Prediction
        xgb_probs = xgb_model.predict_proba(features)[0]
        xgb_class = int(np.argmax(xgb_probs))
        xgb_conf = float(xgb_probs[xgb_class])
        xgb_risk = RISK_LABELS.get(xgb_class, "Low")
        
        # Consensus: default to higher risk if there's a discrepancy
        risk_hierarchy = {"Low": 0, "Medium": 1, "High": 2}
        final_risk = rf_risk if risk_hierarchy[rf_risk] >= risk_hierarchy[xgb_risk] else xgb_risk
        
        return {
            "risk_level": final_risk,
            "rf_confidence": rf_conf,
            "xgb_confidence": xgb_conf,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error during ML inference: {e}. Falling back to heuristics.")
        risk, rf_conf, xgb_conf = heuristic_predict(heart_rate, systolic_bp, diastolic_bp, spo2)
        return {
            "risk_level": risk,
            "rf_confidence": rf_conf,
            "xgb_confidence": xgb_conf,
            "timestamp": datetime.now()
        }
