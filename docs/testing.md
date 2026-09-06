# Testing Strategy

We employ a comprehensive testing suite to validate all system paths.

## Backend Testing (pytest)
- **Authentication:** Valid/invalid login, unauthorized routes, RBAC permissions.
- **Database:** CRUD operations for users, tickets, and protocols with strict `company_id` scoping checks.
- **State Machine:** Ticket status transitions must follow the strict `NEW -> CLASSIFYING -> ... -> CLOSED` pipeline. Invalid transitions must be rejected.
- **RAG & AI:** Mocked ChromaDB and Mistral API responses to test protocol retrieval logic, citation attachment, fallback mechanisms, and the Response Guard.
- **Zulip Integration:** Webhook/polling logic tests using mocked payload events.

## Frontend Testing
- Component testing where complex state logic is implemented (e.g., Markdown rendering for protocols, ticket state management).

## End-to-End Workflow Testing
Integration tests that simulate the full cycle: User message -> User identification -> Ticket creation -> RAG search -> Bot response -> Solved/Not Solved -> Escalation -> IT Resolution.
