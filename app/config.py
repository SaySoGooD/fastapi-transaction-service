# mypy: ignore-errors
import os
from dotenv import load_dotenv

load_dotenv(override=True, encoding="UTF-8")

import os
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    user: str = os.getenv("DB_USER")
    password: str = os.getenv("DB_PASSWORD")
    host: str = os.getenv("DB_HOST")
    port: str = os.getenv("DB_PORT")
    name: str = (
        os.getenv("DB_TEST_NAME") if os.getenv("IS_TESTING", "False").lower() == "true"
        else os.getenv("DB_NAME")
    )

    def __post_init__(self):
        if not self.user:
            raise ValueError("DB_USER is not set")
        if not self.password:
            raise ValueError("DB_PASSWORD is not set")
        if not self.host:
            raise ValueError("DB_HOST is not set")
        if not self.port:
            raise ValueError("DB_PORT is not set")
        if not self.name:
            raise ValueError("DB_NAME or DB_TEST_NAME is not set")


    @property
    def sync_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass
class RabbitMQConfig:
    url: str = os.getenv("RABBITMQ_URL")
    queue_name: str = os.getenv("QUEUE_NAME")

    def __post_init__(self):
        if not self.url:
            raise ValueError("RABBITMQ_URL is not set")
        if not self.queue_name:
            raise ValueError("QUEUE_NAME is not set")


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", 6379))
    db: int = int(os.getenv("REDIS_DB", 0))
    password: str = os.getenv("REDIS_PASSWORD")

    def __post_init__(self):
        if not self.host:
            raise ValueError("REDIS_HOST is not set")
        if not self.port:
            raise ValueError("REDIS_PORT is not set")
        if not self.db:
            raise ValueError("REDIS_DB is not set")
        if not self.password:
            raise ValueError("REDIS_PASSWORD is not set, using default (no password)")


@dataclass
class APISettings:
    token: str = os.getenv("API_TOKEN") 
    ip: str = os.getenv("API_IP")
    port: int = int(os.getenv("API_PORT", 8000))

    def __post_init__(self):
        if not self.token:
            raise ValueError("API_TOKEN is not set")
        if not self.ip:
            raise ValueError("API_IP is not set")
        if not self.port:
            raise ValueError("API_PORT is not set")


@dataclass
class Settings:
    is_testing: bool = os.getenv("IS_TESTING", "False").lower() == "true"
    db: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
    rabbitmq: RabbitMQConfig = field(default_factory=lambda: RabbitMQConfig())
    redis: RedisConfig = field(default_factory=lambda:  RedisConfig())
    api: APISettings = field(default_factory=lambda: APISettings())


settings = Settings()
