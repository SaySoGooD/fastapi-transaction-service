from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy_utils import create_database, database_exists # type: ignore

from loguru import logger

from app.config import settings
from app.database.models import Base



class InitDB:
    def __init__(self):
        self.custom_create_database()

    def custom_create_database(self):
        url = settings.db.sync_url
        try:
            if not database_exists(url):
                create_database(url)
                logger.success("Database created!")
            else:
                logger.info("Database already exists.")
        except Exception as e:
            logger.error(f"Failed to create or check database: {e}")
            raise


class AsyncSessionManager:
    def __init__(self, db_url: str = settings.db.async_url):
        self.engine = create_async_engine(db_url, echo=False)
        self._sessionmaker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def get_session(self) -> AsyncSession:
        return self._sessionmaker()

