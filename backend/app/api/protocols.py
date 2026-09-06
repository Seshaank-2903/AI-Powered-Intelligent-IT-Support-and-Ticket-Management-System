from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.protocol import Protocol
from app.schemas.protocol import ProtocolResponse, ProtocolCreate, ProtocolUpdate
from app.services.protocol_service import ProtocolService
from app.core import security
from app.core.exceptions import AppException
import uuid
from datetime import datetime, timezone

router = APIRouter()

@router.post("/", response_model=ProtocolResponse)
def upload_protocol(
    company_id: uuid.UUID = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    version: str = Form("1.0"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN"]))
):
    if current_user.role != "SUPER_ADMIN" and current_user.company_id != company_id:
        raise AppException("FORBIDDEN", "Cannot upload protocol for another company", 403)
        
    protocol_in = ProtocolCreate(
        company_id=company_id,
        title=title,
        description=description,
        version=version
    )
    
    return ProtocolService.create_protocol_from_upload(db, protocol_in, file, current_user.id)

@router.get("/", response_model=List[ProtocolResponse])
def list_protocols(
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN", "IT_AGENT"]))
):
    if current_user.role == "SUPER_ADMIN":
        return db.query(Protocol).all()
    return db.query(Protocol).filter(Protocol.company_id == current_user.company_id).all()

@router.patch("/{protocol_id}", response_model=ProtocolResponse)
def update_protocol(
    protocol_id: uuid.UUID,
    update_data: ProtocolUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(security.require_role(["COMPANY_ADMIN", "SUPER_ADMIN"]))
):
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise AppException("NOT_FOUND", "Protocol not found", 404)
        
    if current_user.role != "SUPER_ADMIN" and protocol.company_id != current_user.company_id:
        raise AppException("FORBIDDEN", "Forbidden", 403)
        
    for k, v in update_data.model_dump(exclude_unset=True).items():
        setattr(protocol, k, v)
        
    db.commit()
    db.refresh(protocol)
    return protocol
