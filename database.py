import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session

load_dotenv()

engine = create_engine(os.getenv("DB_LINK"))

def get_session():
    with Session(engine) as session:
        yield session