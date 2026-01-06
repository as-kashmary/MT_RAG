from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.mysql import LONGBLOB, BINARY
from .db_connection_new import Base
from uuid import uuid4, UUID
from datetime import datetime, timezone

from src.logging.logging import get_logger
logger= get_logger("entities")


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
    # email = Column(String(255), nullable=False, unique=True)
    # password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id='{decode_uuid(self.id)}', name='{self.name}', created_at='{self.created_at}')>"


def generate_login_id() -> str:
    """Generate a unique login_id for a company based on UUID."""
    return str(uuid4())[:32]  # Use first 32 chars of UUID as login_id


class Company(Base):
    __tablename__ = 'company'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    login_id = Column(String(255), nullable=False, unique=True, default=generate_login_id)

    def __repr__(self):
        return f"<Company(id='{decode_uuid(self.id)}', name='{self.name}', login_id='{self.login_id}')>"


class Product(Base):
    """
    Product entity - represents a product/service within a company.
    Documents are associated with specific products for multi-product support.
    """
    __tablename__ = 'product'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"<Product(id='{decode_uuid(self.id)}', name='{self.name}', company_id='{decode_uuid(self.company_id)}')>"
    

class Admin(Base):
    __tablename__ = 'admin'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    username = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=True)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE" ), nullable=False)

    def __repr__(self):
        return f"<Admin(id='{decode_uuid(self.id)}', username='{self.username}')>"


class File(Base):
    __tablename__ = 'file'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    file_name = Column(String(255), nullable=False)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE"), nullable=False)
    product_id = Column(BINARY(16), ForeignKey('product.id', ondelete="CASCADE"), nullable=True)
    file_data = Column(LONGBLOB, nullable=False)
    file_hash = Column(String(255), nullable=False, unique=True)
    file_format = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False, default="pending")
    uploaded_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return (
            f"<File(id='{decode_uuid(self.id)}', name='{self.file_name}', "
            f"company_id='{decode_uuid(self.company_id)}', "
            f"product_id='{decode_uuid(self.product_id) if self.product_id else None}', "
            f"format='{self.file_format}', status='{self.status}')>"
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


class Executive(Base):
    """
    Executive (CTO/CEO) entity - owns a company and can manage admins.
    Used for the Executive Portal authentication and authorization.
    """
    __tablename__ = 'executive'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE"), nullable=False)
    industry = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return (
            f"<Executive(id='{decode_uuid(self.id)}', name='{self.name}', "
            f"email='{self.email}', company_id='{decode_uuid(self.company_id)}'>"
        )
