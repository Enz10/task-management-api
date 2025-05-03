from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for the data encoded within the JWT token."""
    sub: str | None = None # 'sub' usually holds the user identifier (e.g., email or user_id)

