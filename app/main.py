from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger
import uvicorn

from app.config import settings
from app.api.handlers import main_router
from app.database.database import InitDB
from app.services.rabbitmq import rabbitmq

InitDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq.connect()
    yield
    await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
app.include_router(main_router)

if __name__ == "__main__":
    try:
        uvicorn.run("app.main:app", host=settings.api.ip, port=settings.api.port, reload=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
