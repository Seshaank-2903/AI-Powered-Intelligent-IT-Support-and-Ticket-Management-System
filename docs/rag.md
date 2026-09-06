# RAG System Architecture

The Retrieval-Augmented Generation (RAG) system is the core component ensuring that the AI strictly provides company-approved solutions when available.

## Components
1. **Document Ingestion:**
   - Supported formats: PDF, DOCX, TXT, Markdown.
   - Optional OCR using `pytesseract` and `Pillow`.
2. **Chunking & Embeddings:**
   - Text is cleaned and split into semantic chunks.
   - Embeddings are generated using the Mistral API (`mistral-embed`).
3. **Vector Storage:**
   - ChromaDB is used as the vector store.
   - Every embedding includes metadata mapping it to its source (`company_id`, `protocol_id`, `version`, `section`, `page_number`).
4. **Retrieval & Response Guard:**
   - Queries are embedded and compared against ChromaDB.
   - **Crucial:** All queries are hard-filtered by `company_id`. Cross-tenant data leakage is structurally prevented.
   - Retrieved context is passed to the Mistral Chat LLM.
   - A Response Guard verifies that the source was used properly before sending to the user.

## Data Flow
```text
UPLOAD -> VALIDATE -> EXTRACT -> CLEAN -> CHUNK -> EMBED -> CHROMADB + POSTGRES -> READY
```

When querying:
```text
QUESTION -> RETRIEVE (Filter by company_id) -> EVIDENCE SUFFICIENT? 
  -> YES: Grounded Response + Citation (Source: PROTOCOL)
  -> NO: Mistral AI Troubleshooting Fallback (Source: MISTRAL)
```
