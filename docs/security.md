# Security Considerations

Security is paramount, especially since we handle corporate IT procedures.

## Multi-Tenant Isolation
- The database is strictly scoped by `company_id`.
- The RAG system must pass `company_id` as metadata during any vector search to ensure no cross-company data leakage.
- JWT tokens encode `company_id` to strictly limit user access on backend API calls.

## Authentication & Authorization
- **JWT Auth:** The Admin Dashboard and API endpoints use secure JWT authentication.
- **Passwords:** Passwords are hashed securely (e.g., using `bcrypt`). No plaintext passwords are stored.
- **RBAC:** Four roles: `SUPER_ADMIN`, `COMPANY_ADMIN`, `IT_AGENT`, `EMPLOYEE`. Endpoints validate the role before execution.

## System Defenses
- **Environment Variables:** All secrets (Zulip API keys, Mistral API keys, DB URL, JWT secret) are in `.env` and never in source code.
- **Input Validation:** Extensive use of Pydantic models to validate API input.
- **File Uploads:** Uploaded protocols are validated for file type and size. Filenames are sanitized.
- **Prompt Injection:** Retrieval logic wraps the user input strictly to avoid escaping the prompt and impersonating system logic.
- **CORS:** Configured explicitly to allow only trusted frontend domains.
