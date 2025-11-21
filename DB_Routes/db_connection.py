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
    status= Column(String, default="pending")


mysql_user="drcash"
mysql_password="admin%40123"
mysql_host="mysql-drcash.alwaysdata.net"
mysql_database="drcash_mt_rag"
mysql_port="3306"

DATABASE_URL = f"mysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
    

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)

print("Tables registered with Base.metadata:")
for table_name in Base.metadata.tables.keys():
    print(f"- {table_name}")

Session = sessionmaker(bind=engine)
session = Session() 


