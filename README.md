# AI-Powered Intelligent IT Support & Ticket Management System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F61?style=for-the-badge)](https://www.trychroma.com/)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-FF7000?style=for-the-badge)](https://mistral.ai/)

An **organization-aware, enterprise-grade AI IT Support & Ticket Escalation Platform**. This system acts as an intelligent IT support bridge between employees and IT agents via corporate chat (Zulip) and a modern Admin Dashboard. It prioritizes company-approved procedures via a robust **Protocol-First RAG (Retrieval-Augmented Generation)** pipeline using **Mistral AI** and **ChromaDB**, and seamlessly escalates unresolved issues to human IT agents while automatically detecting organizational knowledge gaps.

---

## 🌟 Key Features

### 🏢 Multi-Tenant Company Isolation
- Complete multi-tenant isolation via `company_id` across databases, vector stores, and API endpoints.
- Secure Role-Based Access Control (RBAC): **Super Admin**, **Company Admin**, **IT Manager**, **IT Agent**, and **Employee**.

### 🤖 Protocol-First RAG Engine
- Grounded AI response generation using vector search on uploaded company IT protocols (PDFs, DOCX, TXT).
- Custom chunking strategies and cosine-similarity vector retrieval powered by **ChromaDB** and **Mistral AI API**.
- Built-in AI guardrails to prevent hallucination and restrict answers strictly to verified company documentation.

### 💬 Native Zulip Chatbot Integration
- Employees interact with the IT AI Bot directly inside their company's Zulip streams.
- Interactive response buttons: **"Solved"** or **"Escalate to Human Agent"**.
- Automatic ticket creation and event tracking right inside chat channels.

### 🔄 Intelligent Ticket Lifecycle & Escalation
- Complete state machine for tickets: `OPEN` → `AUTO_ASSIGNED` → `IN_PROGRESS` → `ESCALATED` → `RESOLVED` → `CLOSED`.
- Confidential ticket flagging for sensitive HR/Exec inquiries with restricted agent visibility.

### 🧠 Automated Knowledge Gap Detection
- Automatically analyzes unresolved ticket escalations and user feedback.
- Identifies missing or outdated IT protocols and alerts IT Managers with AI-suggested protocol draft improvements.

### 📊 Modern Executive Admin Dashboard
- Built with **React 18**, **TypeScript**, **Vite**, and **Tailwind CSS**.
- Real-time ticket management queue, protocol document upload center, knowledge gap review panel, and analytics.

---

## 🏗️ System Architecture

```
                                 ┌─────────────────────────┐
                                 │   Employee Interface    │
                                 │ (Zulip Chat / React UI) │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │     FastAPI Backend     │
                                 │  (Auth, RBAC, REST API) │
                                 └──────┬──────────────┬───┘
                                        │              │
                   ┌────────────────────┘              └────────────────────┐
                   ▼                                                        ▼
   ┌──────────────────────────────┐                         ┌──────────────────────────────┐
   │       RAG Engine & AI        │                         │      Relational Database     │
   │  ┌────────────────────────┐  │                         │ ┌──────────────────────────┐ │
   │  │ ChromaDB (Vector Store)│  │                         │ │ PostgreSQL / SQLAlchemy  │ │
   │  └────────────────────────┘  │                         │ └──────────────────────────┘ │
   │  ┌────────────────────────┐  │                         │ (Users, Companies, Tickets,  │
   │  │    Mistral AI API      │  │                         │  Protocols, Audit Logs)      │
   │  └────────────────────────┘  │                         └──────────────────────────────┘
   └──────────────┬───────────────┘
                  │ (If unresolved)
                  ▼
   ┌──────────────────────────────┐
   │     Human IT Support Queue   │
   │  (Agent Escalation & Gap)    │
   └──────────────────────────────┘
```

---

## 📁 Repository Structure

```
├── backend/                  # FastAPI Python Application
│   ├── app/
│   │   ├── ai/              # Mistral AI client & response guardrails
│   │   ├── api/             # REST Endpoints (Tickets, Protocols, Auth, Analytics)
│   │   ├── core/            # Security, JWT, Configuration, Logging
│   │   ├── db/              # SQLAlchemy session & Base models
│   │   ├── models/          # ORM Data Models (User, Ticket, Protocol, KnowledgeGap)
│   │   ├── rag/             # Document extraction, Chunking, ChromaDB Vector Store
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── services/        # Business logic & services
│   │   └── zulip/           # Zulip Bot handlers, webhooks, and listener
│   ├── alembic/             # Database migrations
│   └── tests/               # Pytest suite
├── frontend/                 # React + TypeScript + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── pages/           # Dashboard, Tickets, Protocols, Login views
│   │   └── App.tsx          # Router and core application state
├── docs/                     # Comprehensive Architecture & API Documentation
│   ├── architecture.md      # Detailed system architecture
│   ├── api.md               # REST API documentation
│   ├── database.md          # Database schema & ERD details
│   ├── rag.md               # RAG pipeline implementation guide
│   ├── security.md          # Security policy & RBAC rules
│   └── deployment.md        # Production deployment strategies
├── docker-compose.yml        # Docker services for PostgreSQL & ChromaDB
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js**: `v18+`
- **Python**: `v3.11+`
- **Docker & Docker Compose** (for local PostgreSQL & ChromaDB)
- **API Keys**: Mistral AI API Key

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Seshaank-2903/AI-Powered-Intelligent-IT-Support-and-Ticket-Management-System.git
cd AI-Powered-Intelligent-IT-Support-and-Ticket-Management-System
```

---

### 2️⃣ Start Infrastructure (PostgreSQL + ChromaDB)

```bash
docker-compose up -d
```
* PostgreSQL runs on `localhost:5432`
* ChromaDB runs on `localhost:8000`

---

### 3️⃣ Set Up Backend (`FastAPI`)

```bash
cd backend

# Create & activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Open .env and add your MISTRAL_API_KEY and database URL

# Run database migrations
alembic upgrade head

# Seed initial protocols & sample data
python -m app.scripts.seed_protocols

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```
* **API Documentation (Swagger)**: Available at `http://localhost:8000/docs`

---

### 4️⃣ Set Up Frontend (`React + Vite`)

```bash
cd ../frontend

# Install node dependencies
npm install

# Run the Vite development server
npm run dev
```
* **Frontend Web App**: Available at `http://localhost:5173`

---

## 🧪 Running Tests

```bash
cd backend
pytest
```

---

## 🌐 Production Deployment

See [docs/deployment.md](docs/deployment.md) for full production deployment instructions.

* **Frontend**: Deploy to **Vercel** / **Netlify**
* **Backend**: Deploy to **Render** / **Railway** / **AWS ECS**
* **Database**: **Supabase** / **Managed PostgreSQL**
* **Vector Store**: **Chroma Cloud** / **Hosted Container**

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

Developed by **Seshaank** ([@Seshaank-2903](https://github.com/Seshaank-2903)).
