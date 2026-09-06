# API Documentation

The REST API is built with FastAPI. All endpoints requiring authentication must use a valid JWT token in the `Authorization: Bearer <token>` header.

## Base URL
`/api/v1`

## Endpoints

### Auth
- `POST /auth/login`: Authenticate and receive JWT token.
- `GET /auth/me`: Get current authenticated user details.

### Companies (Super Admin)
- `GET /companies`: List companies.
- `POST /companies`: Create a new company.
- `GET /companies/{id}`: Get company details.
- `PATCH /companies/{id}`: Update company.

### Users
- `GET /users`: List users in the current company.
- `GET /users/{id}`: Get specific user details.

### Tickets
- `POST /tickets`: Create a manual ticket.
- `GET /tickets`: List tickets (filtered by company/role).
- `GET /tickets/{id}`: Get full ticket details including history.
- `PATCH /tickets/{id}`: Update ticket metadata.
- `POST /tickets/{id}/assign`: Assign ticket to an IT agent.
- `POST /tickets/{id}/resolve`: Resolve the ticket.
- `POST /tickets/{id}/close`: Close the ticket.

### Messages
- `GET /tickets/{id}/messages`: Retrieve chat history for a specific ticket.

### Protocols
- `POST /protocols`: Upload/create a new protocol.
- `GET /protocols`: List active/archived protocols.
- `GET /protocols/{id}`: Get protocol details.
- `PATCH /protocols/{id}`: Update protocol text/metadata.
- `POST /protocols/{id}/approve`: Approve and trigger RAG ingestion.
- `POST /protocols/{id}/archive`: Archive a protocol.
- `POST /protocols/{id}/reindex`: Reindex embeddings.

### Knowledge Gaps
- `GET /knowledge-gaps`: List identified gaps.
- `GET /knowledge-gaps/{id}`: Get gap details.
- `PATCH /knowledge-gaps/{id}`: Update gap status.
- `POST /knowledge-gaps/{id}/create-protocol`: Open draft protocol from a gap.

### Analytics
- `GET /analytics/overview`: High-level metrics.
- `GET /analytics/tickets`: Ticket trend metrics.
- `GET /analytics/resolution`: Resolution success rates.
- `GET /analytics/knowledge-gaps`: Most frequent gaps.

### System
- `GET /health`: Health check endpoint.
