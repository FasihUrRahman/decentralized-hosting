# client_node/auth/crud.py

from sqlalchemy.orm import Session
import secrets

from . import schemas
from . import security
from ..database import models

def get_user_by_username(db: Session, username: str):
    """
    Retrieves a single user from the database by their username.
    """
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    """
    Creates a new user in the database.
    - Hashes the password.
    - Generates a unique API key.
    - Saves the new user record.
    """
    hashed_password = security.get_password_hash(user.password)
    
    api_key = secrets.token_hex(32) 
    
    # The stray underscore on the line below has been removed.
    db_user = models.User(
        username=user.username, 
        hashed_password=hashed_password,
        role=user.role,
        api_key=api_key
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user