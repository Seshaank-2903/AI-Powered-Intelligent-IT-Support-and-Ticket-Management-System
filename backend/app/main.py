from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import AppException, app_exception_handler
from app.api import health, auth, companies, users, tickets, messages, zulip_webhook, protocols, knowledge_gaps, analytics

import app.models
from app.db.base import Base
from app.db.session import engine

# Setup logging
setup_logging()

# Auto-create tables if not present
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    pass


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Company-Specific AI IT Support Platform"
)

# Set all CORS enabled origins
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)

# Include Routers
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api/auth")
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(messages.router, prefix="/api/tickets", tags=["Messages"])
app.include_router(zulip_webhook.router, prefix="/api/zulip", tags=["Zulip"])
app.include_router(protocols.router, prefix="/api/protocols", tags=["Protocols"])
app.include_router(knowledge_gaps.router, prefix="/api/knowledge-gaps", tags=["Knowledge Gaps"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/")
def root():
    return {"message": "Welcome to the Company-Specific AI IT Support API. Go to /docs for Swagger UI."}
