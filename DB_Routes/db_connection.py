from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import LONGBLOB

Base = declarative_base()

class User(Base):
    __tablename__ ='User'
    id = Column(Integer, primary_key= True)
    name=Column(String)

class Company(Base):
    __tablename__ ='Company'
    id = Column(Integer, primary_key= True)
    name=Column(String)

class File(Base):
    __tablename__='File'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name=Column(String)
    company_id = Column(Integer, ForeignKey('Company.id'))
    file_data =Column(LONGBLOB)
    file_format =Column(String)
    pending = Column(Boolean, default=False)
    running = Column(Boolean, default=False)
    successful = Column(Boolean, default=False)
    failed = Column(Boolean, default=False)
    
DATABASE_URL = "mysql://drcash:admin%40123@mysql-drcash.alwaysdata.net:3306/drcash_mt_rag"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

print("Tables registered with Base.metadata:")
for table_name in Base.metadata.tables.keys():
    print(f"- {table_name}")

Session = sessionmaker(bind=engine)
session = Session() 


