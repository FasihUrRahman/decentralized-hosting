# client_node/auth/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, schemas
from ..database.database import get_db

# An APIRouter helps organize endpoints into groups
router = APIRouter()

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Handles new user registration.
    - Checks if the username is already taken.
    - Creates the new user in the database.
    - Returns the created user's data (without the password).
    """
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    new_user = crud.create_user(db=db, user=user)
    return new_user