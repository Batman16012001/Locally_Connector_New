from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends
from typing import AsyncGenerator
from .settings import get_settings

settings = get_settings()

class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

    @classmethod
    async def connect_db(cls):
        """Create database connection."""
        cls.client = AsyncIOMotorClient(settings.mongodb_url)
        cls.db = cls.client[settings.mongodb_db_name]
        print(f"Connected to MongoDB database: {settings.mongodb_db_name}")

    @classmethod
    async def close_db(cls):
        """Close database connection."""
        if cls.client:
            cls.client.close()
            print("Closed MongoDB connection.")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        return cls.db

async def get_database() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Dependency for getting database instance."""
    yield Database.get_db() 