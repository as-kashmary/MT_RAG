# init_db.py
import asyncio
from src.DB_Routes.db_connection_new import engine, Base
# Import entities so SQLAlchemy knows about them
from src.DB_Routes.entities import User, Company, Product, File, ChatSession, ChatMessage 

async def init_tables():
    async with engine.begin() as conn:
        # This creates tables ONLY if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables (including ChatSession & ChatMessage) created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_tables())