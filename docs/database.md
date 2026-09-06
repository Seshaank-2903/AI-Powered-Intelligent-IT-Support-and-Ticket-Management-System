# Database Schema

The system uses PostgreSQL for relational data storage, accessed via SQLAlchemy ORM. All tables except `COMPANIES` are strictly scoped by `company_id` for multi-tenant isolation.

## Tables

### COMPANIES
- `id` (UUID, PK)
- `name` (String)
- `slug` (String, Unique)
- `description` (Text)
- `status` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### USERS
- `id` (UUID, PK)
- `company_id` (UUID, FK -> COMPANIES)
- `zulip_user_id` (String)
- `name` (String)
- `email` (String)
- `department` (String)
- `role` (String)
- `is_active` (Boolean)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### TICKETS
- `id` (UUID, PK)
- `ticket_number` (String, Unique, e.g., TKT-2026-000001)
- `company_id` (UUID, FK -> COMPANIES)
- `user_id` (UUID, FK -> USERS)
- `title` (String)
- `description` (Text)
- `category` (String)
- `priority` (String)
- `status` (String)
- `resolution_source` (String)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `closed_at` (DateTime)

### MESSAGES
- `id` (UUID, PK)
- `ticket_id` (UUID, FK -> TICKETS)
- `sender_type` (String: USER, BOT, IT_AGENT)
- `sender_id` (String/UUID)
- `message` (Text)
- `source` (String: PROTOCOL, MISTRAL, HUMAN)
- `metadata` (JSONB)
- `created_at` (DateTime)

### PROTOCOLS
- `id` (UUID, PK)
- `company_id` (UUID, FK -> COMPANIES)
- `title` (String)
- `description` (Text)
- `version` (String)
- `file_path` (String)
- `file_type` (String)
- `status` (String: DRAFT, UNDER_REVIEW, APPROVED, ACTIVE, ARCHIVED)
- `created_by` (UUID, FK -> USERS)
- `approved_by` (UUID, FK -> USERS)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `approved_at` (DateTime)

### PROTOCOL_CHUNKS
- `id` (UUID, PK)
- `protocol_id` (UUID, FK -> PROTOCOLS)
- `company_id` (UUID, FK -> COMPANIES)
- `chunk_text` (Text)
- `section` (String)
- `page_number` (Integer)
- `chunk_index` (Integer)
- `embedding_id` (String - Maps to ChromaDB)
- `metadata` (JSONB)
- `created_at` (DateTime)

### KNOWLEDGE_GAPS
- `id` (UUID, PK)
- `company_id` (UUID, FK -> COMPANIES)
- `topic` (String)
- `description` (Text)
- `occurrence_count` (Integer)
- `example_ticket_id` (UUID, FK -> TICKETS)
- `status` (String: OPEN, UNDER_REVIEW, PROTOCOL_CREATED, RESOLVED)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- `resolved_at` (DateTime)

### TICKET_EVENTS
- `id` (UUID, PK)
- `ticket_id` (UUID, FK -> TICKETS)
- `event_type` (String)
- `actor_type` (String)
- `actor_id` (String/UUID)
- `metadata` (JSONB)
- `created_at` (DateTime)
