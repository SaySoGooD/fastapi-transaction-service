from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from loguru import logger

from app.config import DB_ASYNC_URL, DB_SYNC_URL
from app.database.models import Base



class InitDB:
    def __init__(self):
        self.custom_create_database()
        self.create_tables()

    def custom_create_database(self):
        url = DB_SYNC_URL
        try:
            if not database_exists(url):
                create_database(url)
                logger.success("Database created!")
            else:
                logger.info("Database already exists.")
        except Exception as e:
            logger.error(f"Failed to create or check database: {e}")
            raise

    def create_tables(self):
        engine = create_engine(DB_SYNC_URL, echo=True)
        Base.metadata.create_all(bind=engine)  #  А как же alembic???
        logger.success("Tables created!")


class AsyncSessionManager:
    def __init__(self, db_url: str = DB_ASYNC_URL):
        self.engine = create_async_engine(db_url, echo=False)
        self._sessionmaker = sessionmaker( # Почему-то синхронный sessionmaker
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    def get_session(self) -> AsyncSession:
        return self._sessionmaker()

