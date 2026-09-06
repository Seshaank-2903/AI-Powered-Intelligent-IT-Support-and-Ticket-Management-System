from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.analytics import AnalyticsOverview
from app.services.analytics_service import AnalyticsService
from app.core import security
from app.core.exceptions import AppException

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN"]))
):
    if current_user.role == "SUPER_ADMIN":
        return AnalyticsService.get_overview(db)
    return AnalyticsService.get_overview(db, current_user.company_id)
