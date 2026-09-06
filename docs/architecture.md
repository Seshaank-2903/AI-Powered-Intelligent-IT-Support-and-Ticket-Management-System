# Architecture

## Overview
The "Company-Specific AI IT Support and Intelligent Ticket Escalation Platform" is a production-style academic prototype. It enables employees to get IT support through a Zulip chatbot, backed by a sophisticated AI framework that prioritizes company-approved protocols.

## System Components

### 1. Backend (FastAPI)
- **Framework:** Python 3.11+ with FastAPI.
- **Responsibilities:** API routing, DB interactions, orchestrating RAG pipelines, managing tickets, communicating with Zulip.
- **Database:** PostgreSQL (using SQLAlchemy and Alembic) for relational data.

### 2. Frontend (React + Vite)
- **Framework:** React + TypeScript + Vite, styled with Tailwind CSS.
- **Responsibilities:** Admin dashboard for managing tickets, users, protocols, and knowledge gaps.

### 3. AI & RAG (Mistral + ChromaDB)
- **LLM:** Mistral API for conversational logic.
- **Vector DB:** ChromaDB for protocol storage and retrieval.
- **RAG Pipeline:** Document ingestion -> Text extraction -> Chunking -> Mistral Embeddings -> ChromaDB.

### 4. Chat Interface (Zulip)
- **Platform:** Zulip API and Bot framework.
- **Streams:** `#ai-support` (employee interaction), `#it-support` (escalated tickets), `#it-admin`.

## High-Level Workflow
1. User messages Zulip `#ai-support`.
2. Backend identifies user and company, opens/updates ticket.
3. RAG system searches company-specific protocols.
4. If found, grounded response is generated via Mistral and returned to Zulip with citations.
5. If not found, Mistral AI troubleshooting is provided (labeled as AI).
6. User confirms if solved. If not, ticket is escalated to IT in `#it-support` and a knowledge gap is potentially recorded.
