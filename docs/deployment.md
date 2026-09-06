# Deployment Architecture

## Local Development
- Handled via `docker-compose.yml`.
- Spins up local PostgreSQL and ChromaDB containers.
- The FastAPI backend and React frontend are run locally on the host machine.
- Mistral API and Zulip require active network connections.

## Production
- **Backend:** Deployed to a platform like Heroku, Render, AWS ECS, or similar container orchestrator.
- **Frontend:** Deployed as static files to Vercel, Netlify, or S3/CloudFront.
- **Database:** Managed PostgreSQL (e.g., Supabase, AWS RDS).
- **Vector Store:** Managed ChromaDB or deployed ChromaDB container.
- **Secrets Management:** Environment variables injected securely via the deployment provider (never committed to git).
