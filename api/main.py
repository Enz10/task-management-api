from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import users, tasks, teams, login
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Set up CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],      # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],      # Allow all headers
)

# Include routers from V1 endpoints
api_prefix = "/api/v1"
app.include_router(login.router, prefix=f"{api_prefix}", tags=["login"])
app.include_router(users.router, prefix=f"{api_prefix}/users", tags=["users"])
app.include_router(tasks.router, prefix=f"{api_prefix}/tasks", tags=["tasks"])
app.include_router(teams.router, prefix=f"{api_prefix}/teams", tags=["teams"])
