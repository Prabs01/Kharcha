from sqlmodel import SQLModel, create_engine, Session
from fastapi import Depends
from typing import Annotated
from app.config import settings


engine = create_engine(settings.database_url , echo = True
 , pool_pre_ping=True,
    pool_size=10,
    max_overflow=20) #pool_pre_ping checks if the connection is alive before using it, pool_size is the number of connections to keep in the pool, max_overflow is the number of connections to allow in overflow (i.e. when the pool is full)

def create_db_and_table():
    SQLModel.metadata.create_all(engine)

def get_session():
   with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


# reusable alias
SessionDep = Annotated[Session, Depends(get_session)]

