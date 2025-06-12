# client_node/database/models.py

from sqlalchemy import Column, Integer, String, Enum as SAEnum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

# Define the possible roles for a user
class UserRole(str, enum.Enum):
    CLIENT = "client"
    PEER = "peer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.CLIENT)
    
    # --- THIS LINE IS NOW CORRECTED (UNCOMMENTED) ---
    api_key = Column(String, unique=True, index=True, nullable=False)