import sys
import os
import argparse

# Add backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

from app.db.session import SessionLocal
from app.models.company import Company
from app.models.protocol import Protocol
from app.models.user import User
from app.rag.ingestion import ingest_protocol

def add_protocol(file_path: str, title: str, description: str = ""):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    db = SessionLocal()
    try:
        # Get or create company
        company = db.query(Company).first()
        if not company:
            company = Company(name="Default Company", slug="default-company", description="Auto-created default company")
            db.add(company)
            db.commit()
            db.refresh(company)

        # Get or create admin user
        user = db.query(User).first()
        if not user:
            user = User(name="Admin", email="admin@company.com", company_id=company.id, role="SUPER_ADMIN")
            db.add(user)
            db.commit()
            db.refresh(user)

        ext = file_path.split(".")[-1].lower() if "." in file_path else "txt"

        # Create protocol database record
        protocol = Protocol(
            company_id=company.id,
            title=title,
            description=description,
            version="1.0",
            file_path=file_path,
            file_type=ext,
            status="DRAFT",
            created_by=user.id
        )
        db.add(protocol)
        db.commit()
        db.refresh(protocol)

        print(f"Created protocol record ID: {protocol.id}. Ingesting text & embeddings into vector store...")

        # Ingest into ChromaDB & Postgres
        ingest_protocol(db, protocol)
        print(f"✅ Successfully ingested protocol '{title}' into ChromaDB for Company '{company.name}'!")

    except Exception as e:
        print(f"❌ Failed to ingest protocol: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add and ingest a company protocol document.")
    parser.add_argument("file_path", help="Path to protocol document (.txt, .pdf, .docx)")
    parser.add_argument("--title", default="IT Support Protocol", help="Title of protocol")
    parser.add_argument("--desc", default="", help="Description")
    
    args = parser.parse_args()
    add_protocol(args.file_path, args.title, args.desc)
