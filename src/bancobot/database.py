import os
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.environ["DB_URL"])


def create_db_and_tables():
    """Initialize SQLModel with database and tables"""
    SQLModel.metadata.create_all(engine)
