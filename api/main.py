from fastapi import FastAPI
from app.api.v1.endpoints import users, tasks
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Include routers from V1 endpoints
api_prefix = "/api/v1"
app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["users"])
app.include_router(tasks.router, prefix=f"{api_prefix}/tasks", tags=["tasks"])
