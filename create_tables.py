"""
Script to create all database tables.
Run this once to create the Executive, Company, Admin, User, File, and QueryAndAnswer tables.
"""
import asyncio
from src.DB_Routes.db_connection_new import engine, Base

# Import all entities so they register with Base.metadata
from src.DB_Routes.entities import User, Company, Admin, File, QueryAndAnswer, Executive


async def create_tables():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        # Create all tables defined in Base.metadata
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully!")
        
        # List created tables
        print("\nTables created:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")


if __name__ == "__main__":
    asyncio.run(create_tables())
