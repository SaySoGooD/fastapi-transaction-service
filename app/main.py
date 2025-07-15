from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app.config import API_IP, API_PORT, QUEUE_NAME, RABBITMQ_URL

from app.api.handlers import main_router
from app.database.database import InitDB
from app.services.rabbitmq import RabbitMQClient

@asynccontextmanager
async def lifespan(app: FastAPI): # Добавить try/except/finally и логирование ошибок
    InitDB()
    rabbitmq = RabbitMQClient(amqp_url=RABBITMQ_URL, queue_name=QUEUE_NAME)
    await rabbitmq.connect()
    app.state.rabbitmq = rabbitmq  # Хранить кроля здесь ужасное архитектурное решение
    yield
    await rabbitmq.close()

app = FastAPI(lifespan=lifespan)
app.include_router(main_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=API_IP, port=API_PORT, reload=True)