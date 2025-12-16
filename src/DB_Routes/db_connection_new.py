from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
#importing aiomysql
import aiomysql

from src.logging.logging import get_logger
logger= get_logger("db_connection_new")

load_dotenv()

mysql_user=os.getenv('mysql_user')
mysql_password=os.getenv('mysql_password')
mysql_host=os.getenv('mysql_host')
mysql_database=os.getenv('mysql_database')
mysql_port=os.getenv('mysql_port')

"""
This implementation is for async database. So Why we are using it?
When we are using async functions to interact with mysql db, the session must also be async. 
Otherwise we won't be able to harness all the async features of async engine
"""
DATABASE_URL=f"mysql+aiomysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
logger.info(f"Connecting to database at {DATABASE_URL}")


engine= create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False
)
sessionlocal= sessionmaker(
    bind= engine,
    autocommit=False,
    autoflush= False,
    class_=AsyncSession,
    expire_on_commit= False
)

async def get_db():
    async with sessionlocal() as session:
        yield session

Base=declarative_base()



DBSession=Annotated[AsyncSession, Depends(get_db)]
logger.info("Async DBSession configured successfully.")

"""
#This implementation for sync database

DATABASE_URL=f"mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

engine= create_engine(DATABASE_URL)
sessionlocal= sessionamaker(autocommit=False, autoflush= False, bind= engine)

def get_db():
    db=sessionlocal()
    try:
        yield db
    finally:
        db.close()

Base= declarative_base()

DBSession=Annotated[Session, Depends(get_db)]

"""