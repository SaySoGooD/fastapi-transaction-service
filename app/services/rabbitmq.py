import aio_pika
from loguru import logger

from app.config import settings


class RabbitMQClient:
    def __init__(self, amqp_url: str | None = settings.rabbitmq.url, 
                 queue_name: str | None = settings.rabbitmq.queue_name):
        self.amqp_url = amqp_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    async def connect(self):
        """Establish connection and channel to RabbitMQ."""
        self.connection = await aio_pika.connect_robust(self.amqp_url)
        self.channel = await self.connection.channel()
        logger.info(f"Connected to RabbitMQ at {self.amqp_url}")

    async def send_message(self, message_body: str):
        """Send message to the queue."""
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized. Call connect() first.")
        message = aio_pika.Message(body=message_body.encode())
        await self.channel.default_exchange.publish(
            message,
            routing_key=self.queue_name
        )
        logger.debug(f"Message sent to queue {self.queue_name}")

    async def close(self):
        """Close channel and connection."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        logger.info("RabbitMQ connection closed")


rabbitmq = RabbitMQClient(amqp_url=settings.rabbitmq.url, 
                         queue_name=settings.rabbitmq.queue_name)
