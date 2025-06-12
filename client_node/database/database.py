# client_node/database/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# We will use a simple SQLite database file for development.
# It will be created inside a new app_data directory within the container.
DATABASE_URL = "sqlite:///./app_data/main.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_and_tables():
    """
    This function creates the database file and all tables defined in models.py.
    """
    print("--- Creating database and tables ---")
    # Get the directory path from the URL
    db_dir = os.path.dirname(DATABASE_URL.replace("sqlite:///./", ""))
    # Create the directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    print("--- Database and tables created successfully ---")


def get_db():
    """
    A dependency for FastAPI routes to get a database session and ensure it's closed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()