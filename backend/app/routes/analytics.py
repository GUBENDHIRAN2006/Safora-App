from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.schemas import RiskAnalysisRequest, RiskAnalysisResponse
from app.services.risk_analysis import predict_health_risk
from app.routes.auth import get_current_user
from app.models.models import User

router = APIRouter(prefix="/analytics", tags=["AI Risk Analysis"])

@router.post("/analyze", response_model=RiskAnalysisResponse)
def analyze_health_risk(
    request: RiskAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates current user physiological metrics against scikit-learn & XGBoost classifiers
    to output risk category (Low, Medium, High) and prediction confidence.
    """
    try:
        prediction = predict_health_risk(
            heart_rate=request.heart_rate,
            systolic_bp=request.systolic_bp,
            diastolic_bp=request.diastolic_bp,
            spo2=request.spo2,
            sleep_hours=request.sleep_hours,
            steps=request.steps
        )
        return prediction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference pipeline failed: {str(e)}"
        )
