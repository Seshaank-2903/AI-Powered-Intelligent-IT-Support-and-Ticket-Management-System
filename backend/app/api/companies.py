from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.core import security
from app.core.exceptions import AppException

router = APIRouter()

@router.get("/", response_model=List[CompanyResponse])
def get_companies(
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_active_superuser)
):
    companies = db.query(Company).all()
    return companies

@router.post("/", response_model=CompanyResponse)
def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_active_superuser)
):
    exists = db.query(Company).filter(Company.slug == company_in.slug).first()
    if exists:
        raise AppException("COMPANY_EXISTS", "Company with this slug already exists")
    
    company = Company(
        name=company_in.name,
        slug=company_in.slug,
        description=company_in.description,
        status=company_in.status
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_active_superuser)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise AppException("NOT_FOUND", "Company not found", 404)
    return company

@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: str,
    company_in: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(security.get_current_active_superuser)
):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise AppException("NOT_FOUND", "Company not found", 404)
    
    update_data = company_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
        
    db.commit()
    db.refresh(company)
    return company
