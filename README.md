# Company-Specific AI IT Support and Intelligent Ticket Escalation Platform

A production-style academic prototype of an organization-aware AI IT support system.

## Overview
This platform acts as an intelligent IT support bridge between employees and IT agents via Zulip. It prioritizes company-approved procedures via a robust RAG (Retrieval-Augmented Generation) pipeline using Mistral AI and ChromaDB, and seamlessly escalates to human agents when issues cannot be resolved automatically, identifying knowledge gaps along the way.

## Features
- **Company Isolation:** Complete multi-tenant isolation via `company_id`.
- **Protocol-First AI:** Grounds AI answers in uploaded, approved corporate procedures.
- **Human Escalation:** Escalates unresolved issues to human IT agents.
- **Knowledge Gap Detection:** Automatically identifies missing procedures based on unresolved escalations.
- **Zulip Integration:** Operates directly inside the company's communication tool.
- **Admin Dashboard:** Full React/TypeScript UI for managing users, tickets, protocols, and analytics.

## Architecture
See `docs/architecture.md` for a high-level overview.

## Technology Stack
- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL.
- **Frontend:** React, TypeScript, Vite, Tailwind CSS.
- **AI/RAG:** Mistral API, ChromaDB.
- **Chat:** Zulip.

## Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Accounts for Mistral AI and Zulip

## Installation

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in credentials.
3. Start local infrastructure:
   ```bash
   docker-compose up -d
   ```
4. Setup Backend:
   ```bash
   cd backend
   python -m venv venv
   # Activate venv
   pip install -r requirements.txt
   ```
5. Setup Frontend:
   ```bash
   cd frontend
   npm install
   ```

*(Further instructions on database migrations, seeding, and running the servers will be populated in subsequent phases).*
