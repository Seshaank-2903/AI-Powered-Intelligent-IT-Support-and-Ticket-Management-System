from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.protocol import Protocol
from app.schemas.protocol import ProtocolCreate
from app.rag.text_extraction import extract_text_from_file
import shutil
import os
import uuid

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "documents", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ProtocolService:
    @staticmethod
    def create_protocol_from_upload(db: Session, protocol_in: ProtocolCreate, file: UploadFile, user_id: uuid.UUID) -> Protocol:
        # Determine file extension safely
        filename = file.filename or ""
        ext = filename.split(".")[-1].lower() if "." in filename else "txt"
        
        # Save file to disk securely
        unique_filename = f"{uuid.uuid4()}.{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Create database record
        protocol = Protocol(
            company_id=protocol_in.company_id,
            title=protocol_in.title,
            description=protocol_in.description,
            version=protocol_in.version,
            file_path=file_path,
            file_type=ext,
            status="DRAFT",
            created_by=user_id
        )
        
        db.add(protocol)
        db.commit()
        db.refresh(protocol)

        # Trigger automatic RAG extraction, chunking, and embedding ingestion
        try:
            from app.rag.ingestion import ingest_protocol
            ingest_protocol(db, protocol)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"RAG Ingestion warning: {e}")

        return protocol
