from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.session import get_db

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    return {"status": "ok", "message": "API is healthy"}
