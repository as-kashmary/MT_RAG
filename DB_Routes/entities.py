from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import LONGBLOB, BINARY
from .db_connection_new import Base
from uuid import uuid4, UUID
from datetime import datetime, timezone


def generate_uuid()->bytes:
    return uuid4().bytes

def encode_uuid(value: str)->bytes:
    return UUID(value).bytes

def decode_uuid(value: bytes)-> UUID:
    return UUID(bytes=value)

"""
UUID is required because: UUID can identify an ID very accurately. Two UUID won't be same. 
It's a 16bits Binary. Here, while defining the entity the generate_uuid() automatically generates a UUID.
decode_uuid() is used to convert it into readable format.

Why cascade is required? 
If a row in parent table is deleted then all the child instances of this row will need to be automatically deleted
Cascade ensures this
"""


class User(Base):
    __tablename__ = 'user'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id='{decode_uuid(self.id)}', name='{self.name}', created_at='{self.created_at}')>"


class Company(Base):
    __tablename__ = 'company'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Company(id='{decode_uuid(self.id)}', name='{self.name}')>"


class File(Base):
    __tablename__ = 'file'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    file_name = Column(String(255), nullable=False)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE" ), nullable=False)
    file_data = Column(LONGBLOB, nullable=False)
    file_hash= Column(String(255), nullable=False, unique=True)
    file_format = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False, default="pending")
    uploaded_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return (
            f"<File(id='{decode_uuid(self.id)}', name='{self.file_name}', "
            f"company_id='{decode_uuid(self.company_id)}', format='{self.file_format}', "
            f"status='{self.status}')>"
        )


class QueryAndAnswer(Base):
    __tablename__ = 'query_and_answer'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    query = Column(String(255), nullable=False)
    response = Column(String(255), nullable=False)
    user_id = Column(BINARY(16), ForeignKey('user.id', ondelete="CASCADE"), nullable=False )

    def __repr__(self):
        return (
            f"<QueryAndAnswer(id='{decode_uuid(self.id)}', query='{self.query}', "
            f"response='{self.response}', user_id='{decode_uuid(self.user_id)}')>"
        )
