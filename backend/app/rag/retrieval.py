from typing import List, Dict, Any
from app.ai.mistral_client import get_embeddings
from app.rag.chroma_store import get_collection
from app.db.session import SessionLocal
from app.models.protocol_chunk import ProtocolChunk
import logging

logger = logging.getLogger(__name__)

STOP_WORDS = {"the", "and", "is", "in", "to", "for", "with", "a", "an", "of", "my", "this", "that", "it", "after", "please", "help", "fix", "me", "how", "can", "i", "company", "employee", "employee's", "user", "issue", "problem", "support", "ticket", "system", "information", "access", "another"}

def is_chunk_relevant(query: str, doc_text: str, distance: float = 0.0) -> bool:
    if not doc_text:
        return False
    q_words = [w.lower() for w in query.split() if len(w) > 3 and w.lower() not in STOP_WORDS]
    if not q_words:
        return False
    doc_lower = doc_text.lower()
    return any(w in doc_lower for w in q_words)

def retrieve_company_protocols(company_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieves the most relevant protocol chunks for a given query.
    Performs tenant-isolated vector search in ChromaDB, with fallbacks to general vector search
    and database text chunk search for uploaded protocols.
    """
    retrieved_chunks = []
    
    # Generate query embedding safely
    query_embedding = None
    try:
        embeddings = get_embeddings([query])
        if embeddings:
            query_embedding = embeddings[0]
    except Exception as e:
        logger.warning(f"Failed to generate query embedding: {e}")

    # 1. Attempt ChromaDB vector query with strict tenant filter
    if query_embedding is not None:
        try:
            collection = get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"company_id": company_id}
            )
            if results and results.get('documents') and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
                metadatas = results.get('metadatas')
                distances = results.get('distances')
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    distance = distances[0][i] if (distances and len(distances) > 0 and distances[0] and i < len(distances[0])) else 0.0
                    if is_chunk_relevant(query, doc, distance):
                        metadata = metadatas[0][i] if (metadatas and len(metadatas) > 0 and metadatas[0] and i < len(metadatas[0])) else {}
                        retrieved_chunks.append({
                            "id": results['ids'][0][i],
                            "document": doc,
                            "metadata": metadata,
                            "distance": distance
                        })
                if retrieved_chunks:
                    return retrieved_chunks
        except Exception as e:
            logger.warning(f"Tenant-isolated ChromaDB query warning: {e}")

        # 2. Fallback: Vector search without strict company_id filter (in case of tenant ID mismatch)
        try:
            collection = get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            if results and results.get('documents') and len(results['documents']) > 0 and len(results['documents'][0]) > 0:
                metadatas = results.get('metadatas')
                distances = results.get('distances')
                for i in range(len(results['documents'][0])):
                    doc = results['documents'][0][i]
                    distance = distances[0][i] if (distances and len(distances) > 0 and distances[0] and i < len(distances[0])) else 0.0
                    if is_chunk_relevant(query, doc, distance):
                        metadata = metadatas[0][i] if (metadatas and len(metadatas) > 0 and metadatas[0] and i < len(metadatas[0])) else {}
                        retrieved_chunks.append({
                            "id": results['ids'][0][i],
                            "document": doc,
                            "metadata": metadata,
                            "distance": distance
                        })
                if retrieved_chunks:
                    return retrieved_chunks
        except Exception as e:
            logger.warning(f"Unfiltered ChromaDB query warning: {e}")

    # 3. Fallback: Search DB protocol chunks directly for keyword matches
    db = SessionLocal()
    try:
        words = [w for w in query.lower().split() if len(w) > 3 and w not in STOP_WORDS]
        if words:
            from sqlalchemy import or_
            query_filters = [ProtocolChunk.chunk_text.ilike(f"%{w}%") for w in words]
            db_chunks = db.query(ProtocolChunk).filter(or_(*query_filters)).limit(top_k).all()
            for chunk in db_chunks:
                retrieved_chunks.append({
                    "id": str(chunk.id),
                    "document": chunk.chunk_text,
                    "metadata": {
                        "company_id": str(chunk.company_id),
                        "protocol_id": str(chunk.protocol_id),
                        "version": "1.0"
                    },
                    "distance": 0.0
                })
            if retrieved_chunks:
                return retrieved_chunks

        # 4. Fallback: Directly read uploaded Protocol files in DB
        import os
        from app.models.protocol import Protocol
        from app.rag.text_extraction import extract_text_from_file
        protocols = db.query(Protocol).all()
        uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "documents", "uploads"))
        for p in protocols:
            target_path = p.file_path
            if target_path and not os.path.exists(target_path):
                alt_path = os.path.join(uploads_dir, os.path.basename(target_path))
                if os.path.exists(alt_path):
                    target_path = alt_path
            if target_path and os.path.exists(target_path):
                try:
                    text = extract_text_from_file(target_path, p.file_type or "txt")
                    if text:
                        # Only append if query shares relevant non-stopword keywords with title or text
                        p_title = (p.title or "").lower()
                        p_text = text.lower()
                        q_words = [w for w in query.lower().split() if len(w) > 3 and w not in STOP_WORDS]
                        if q_words and any(w in p_title or w in p_text for w in q_words):
                            retrieved_chunks.append({
                                "id": str(p.id),
                                "document": text[:2000],
                                "metadata": {
                                    "company_id": str(p.company_id),
                                    "protocol_id": p.title or "Uploaded Protocol",
                                    "version": p.version or "1.0"
                                },
                                "distance": 0.0
                            })
                except Exception as ex:
                    logger.warning(f"File text extraction warning: {ex}")
    except Exception as e:
        logger.error(f"Error querying DB protocol chunks: {e}")
    finally:
        db.close()

    return retrieved_chunks
