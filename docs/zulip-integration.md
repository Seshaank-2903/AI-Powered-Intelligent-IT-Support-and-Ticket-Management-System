# Zulip Generic Bot Integration Guide

This guide details how to set up, run, and test the Zulip Generic Bot integration for the Company-Specific AI IT Support platform.

---

## 1. Overview & Architecture

The integration connects your FastAPI backend with Zulip to manage IT support workflows:
- **Employee Channel (`#ai-support`):** Employees submit IT issues here. The bot creates tickets (`TKT-YYYY-XXXXXX`), searches tenant-isolated company protocols using ChromaDB RAG, or provides general troubleshooting via Mistral AI fallback.
- **IT Support Stream (`#it-support`):** Automatically receives escalated ticket packages when issues cannot be resolved automatically or user selects "Not Solved".
- **IT Admin Stream (`#it-admin`):** Receives real-time administrative alerts for key lifecycle events (ticket creation, resolution, escalation).
- **Duplicate Prevention:** Zulip message IDs are stored in PostgreSQL/SQLite `messages` metadata to guarantee that no message is processed more than once.

---

## 2. Environment Variables Configuration

Ensure the following environment variables are set in your `.env` file (or system environment):

```env
# Zulip Credentials
ZULIP_SITE=https://companyaitickets.zulipchat.com
ZULIP_EMAIL=your-bot-email@companyaitickets.zulipchat.com
ZULIP_API_KEY=your_secret_zulip_api_key

# Zulip Streams
ZULIP_AI_SUPPORT_STREAM=ai-support
ZULIP_IT_SUPPORT_STREAM=it-support
ZULIP_IT_ADMIN_STREAM=it-admin

# Core & AI Settings
DATABASE_URL=postgresql://user:password@localhost:5432/company_ai_it_support
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_CHAT_MODEL=mistral-small-latest
MISTRAL_EMBEDDING_MODEL=mistral-embed
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_PREFIX=company_protocols
```

> **Security Note:** Never commit `ZULIP_API_KEY` or `MISTRAL_API_KEY` to source control. They are loaded dynamically from environment settings.

---

## 3. Installation Requirements

1. **Python Virtual Environment:**
   Ensure dependencies are installed in your virtual environment:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Verify Dependencies:**
   The `zulip` Python SDK is required:
   ```bash
   pip show zulip
   ```

---

## 4. Starting the Services

### Option A: Running FastAPI Backend (API & Webhook Router)
From the `backend` directory:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs are accessible at: `http://localhost:8000/docs`
- Webhook endpoint: `http://localhost:8000/api/zulip/webhook`

### Option B: Running Zulip Real-time Event Listener (Generic Bot)
To listen for real-time events directly from Zulip with automatic reconnection:
```bash
python -m app.zulip.listener
```
- Listens for messages sent in `#ai-support`.
- Reconnects automatically with exponential backoff if network or socket drops.
- Supports graceful shutdown on `Ctrl+C` (SIGINT) or SIGTERM.

---

## 5. Testing the Integration

### A. Run Automated Unit & Integration Tests
Execute the full test suite covering authentication, messaging, bot filtering, stream filtering, duplicate prevention, ticket creation, and escalation:
```bash
pytest tests/test_zulip_integration.py -v
```

### B. Testing the API / Webhook Connection
You can test the connection programmatically using Python:
```python
from app.zulip.client import check_zulip_connection
print("Connected to Zulip:", check_zulip_connection())
```

### C. Testing an Actual Ticket Lifecycle in Zulip

1. **Submit Issue in `#ai-support`:**
   Send a message in the `#ai-support` stream:
   > *"I cannot connect to the company VPN."*

2. **Verify Ticket Creation & Bot Reply:**
   - Bot auto-creates ticket: `TKT-2026-000001`
   - Executes RAG protocol search for employee's company.
   - Posts step-by-step resolution steps in `#ai-support`.
   - Asks: *"Was your issue resolved? Please reply with **Solved** or **Not Solved**."*
   - Sends admin alert to `#it-admin`.

3. **Testing Resolution ("Solved"):**
   - Reply in stream: `Solved`
   - Ticket status transitions to `RESOLVED`.
   - Bot replies: `Ticket TKT-2026-000001 marked as resolved. Have a great day!`

4. **Testing Escalation ("Not Solved"):**
   - Submit issue in `#ai-support`: *"Printer paper jam error."*
   - Reply in stream: `Not Solved`
   - Ticket status transitions to `ESCALATED`.
   - Bot posts detailed escalation summary package to `#it-support` (including Ticket ID, Employee name & email, Issue description, Conversation summary, Protocol attempted, and AI attempted).
   - Bot replies to employee in `#ai-support`:
     > *"The issue could not be resolved automatically. Ticket TKT-2026-000002 has been raised to the IT Support Team."*
