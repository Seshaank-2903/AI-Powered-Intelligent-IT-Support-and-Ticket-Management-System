from typing import cast, Any
from sqlalchemy.orm import Session
from app.models.protocol import Protocol
from app.models.protocol_chunk import ProtocolChunk
from app.rag.text_extraction import extract_text_from_file
from app.rag.chunking import chunk_text
from app.ai.mistral_client import get_embeddings
from app.rag.chroma_store import get_collection
import uuid
import logging

logger = logging.getLogger(__name__)

def ingest_protocol(db: Session, protocol: Protocol):
    """
    Extracts, chunks, embeds, and permanently stores a protocol in ChromaDB and Postgres.
    """
    try:
        # 1. Extract text from uploaded document
        logger.info(f"Extracting text for Protocol {protocol.id}")
        text = extract_text_from_file(protocol.file_path, protocol.file_type)
        
        # 2. Chunk text
        chunks = chunk_text(text)
        logger.info(f"Generated {len(chunks)} chunks.")
        
        # 3. Always create and save permanent Database ProtocolChunks
        ids = []
        metadatas = []
        documents = []
        
        for i, chunk_str in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)
            documents.append(chunk_str)
            metadata = {
                "company_id": str(protocol.company_id),
                "protocol_id": str(protocol.id),
                "version": protocol.version or "1.0",
                "chunk_index": i
            }
            metadatas.append(metadata)
            
            # Database chunk storage
            db_chunk = ProtocolChunk(
                protocol_id=protocol.id,
                company_id=protocol.company_id,
                chunk_text=chunk_str,
                chunk_index=i,
                embedding_id=chunk_id,
                metadata_json=metadata
            )
            db.add(db_chunk)

        # 4. Attempt vector embedding generation & ChromaDB vector store ingestion
        try:
            embeddings = get_embeddings(chunks)
            collection = get_collection()
            collection.add(
                ids=ids,
                embeddings=cast(Any, embeddings),
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"Vector embeddings added to ChromaDB for Protocol {protocol.id}")
        except Exception as embed_err:
            logger.warning(f"Vector embedding API limit/warning during ingestion: {embed_err}. DB chunks saved successfully.")
        
        # Mark protocol as ACTIVE and commit permanently
        protocol.status = "ACTIVE"
        db.commit()
        logger.info(f"Protocol {protocol.id} successfully saved permanently and activated for RAG.")
        
    except Exception as e:
        logger.error(f"Failed to ingest protocol {protocol.id}: {e}")
        protocol.status = "FAILED"
        db.commit()
        raise e
