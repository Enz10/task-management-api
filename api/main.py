from fastapi import FastAPI
from app.core.config import settings 
from app.api.v1.endpoints import users 

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

@app.get("/")
async def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
