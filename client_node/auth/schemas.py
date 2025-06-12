# client_node/auth/schemas.py

from pydantic import BaseModel
# We import the UserRole enum from our database models
from ..database.models import UserRole

class UserCreate(BaseModel):
    """
    Schema for data required to create a new user.
    This is what the user will send to the API.
    """
    username: str
    password: str
    role: UserRole = UserRole.CLIENT # Default role to 'client'

class User(BaseModel):
    """
    Schema for data returned to the user from the API.
    Notice it does NOT include the password.
    """
    id: int
    username: str
    role: UserRole
    api_key: str

    class Config:
        from_attributes = True # Pydantic v2 replaces orm_mode