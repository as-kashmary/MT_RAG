from sqlalchemy.dialects.mysql import LONGBLOB, BINARY
from .db_connection_new import Base
from uuid import uuid4, UUID
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text # <--- ADD 'Text' HERE
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
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    Company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE" ), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<User(id='{decode_uuid(self.id)}', name='{self.name}', created_at='{self.created_at}')>"


class Company(Base):
    __tablename__ = 'company'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    login_id = Column(String(255), nullable=False, unique=True)
    passkey = Column(String(255), nullable=False, unique=False)

    def __repr__(self):
        return f"<Company(id='{decode_uuid(self.id)}', name='{self.name}')>"
    

class Admin(Base):
    __tablename__ = 'admin'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    username = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE" ), nullable=False)

    def __repr__(self):
        return f"<Admin(id='{decode_uuid(self.id)}', username='{self.username}', created_at='{self.created_at}')>"

class Product(Base):
    __tablename__ = 'product'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)
    company_id = Column(BINARY(16), ForeignKey('company.id', ondelete="CASCADE" ), nullable=False)

    def __repr__(self):
        return f"<Product(id='{decode_uuid(self.id)}', name='{self.name}', company_id='{decode_uuid(self.company_id)}')>"

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
    product_id = Column(BINARY(16), ForeignKey('product.id', ondelete="CASCADE" ), nullable=False)

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

# --- These tables are created for store chat sessions and messages ---

class ChatSession(Base):
    __tablename__ = 'chat_session'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    # Note: 'User' table uses 'id', so we link to 'user.id'
    user_id = Column(BINARY(16), ForeignKey('user.id', ondelete="CASCADE"), nullable=False)
    product_id = Column(BINARY(16), ForeignKey('product.id', ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True) # First message snippet (for sidebar)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ChatSession(id='{decode_uuid(self.id)}', title='{self.title}')>"

class ChatMessage(Base):
    __tablename__ = 'chat_message'

    id = Column(BINARY(16), primary_key=True, default=generate_uuid)
    session_id = Column(BINARY(16), ForeignKey('chat_session.id', ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False) # 'user' or 'assistant'
    content = Column(Text, nullable=False)    # 'Text' type is crucial for long RAG responses
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ChatMessage(id='{decode_uuid(self.id)}', role='{self.role}')>"
