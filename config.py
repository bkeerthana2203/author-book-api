import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(override=True)

db_url = os.getenv("DB_URL")
engine = create_engine(db_url)
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)