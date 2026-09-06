from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.knowledge_gap import KnowledgeGap
from app.models.protocol import Protocol
from app.schemas.knowledge_gap import KnowledgeGapResponse, KnowledgeGapUpdate
from app.schemas.protocol import ProtocolResponse
from app.core import security
from app.core.exceptions import AppException
import uuid

router = APIRouter()

@router.get("/", response_model=List[KnowledgeGapResponse])
def get_knowledge_gaps(
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN"]))
):
    if current_user.role == "SUPER_ADMIN":
        return db.query(KnowledgeGap).order_by(KnowledgeGap.occurrence_count.desc()).all()
    return db.query(KnowledgeGap).filter(KnowledgeGap.company_id == current_user.company_id).order_by(KnowledgeGap.occurrence_count.desc()).all()

@router.patch("/{gap_id}", response_model=KnowledgeGapResponse)
def update_gap_status(
    gap_id: uuid.UUID,
    gap_update: KnowledgeGapUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN"]))
):
    gap = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
    if not gap:
        raise AppException("NOT_FOUND", "Knowledge gap not found", 404)
        
    if current_user.role != "SUPER_ADMIN" and gap.company_id != current_user.company_id:
        raise AppException("FORBIDDEN", "Forbidden", 403)
        
    if gap_update.status:
        gap.status = gap_update.status
        
    db.commit()
    db.refresh(gap)
    return gap

@router.post("/{gap_id}/create-protocol", response_model=ProtocolResponse)
def create_protocol_from_gap(
    gap_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN"]))
):
    gap = db.query(KnowledgeGap).filter(KnowledgeGap.id == gap_id).first()
    if not gap:
        raise AppException("NOT_FOUND", "Knowledge gap not found", 404)
        
    if current_user.role != "SUPER_ADMIN" and gap.company_id != current_user.company_id:
        raise AppException("FORBIDDEN", "Forbidden", 403)
        
    # Create draft protocol
    protocol = Protocol(
        company_id=gap.company_id,
        title=f"Fix: {gap.topic}",
        description=gap.description,
        version="1.0",
        status="DRAFT",
        created_by=current_user.id
    )
    
    # Mark gap as resolved/converted
    gap.status = "PROTOCOL_CREATED"
    
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    return protocol
