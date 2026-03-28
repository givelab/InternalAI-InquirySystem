import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: int = Field(5432, ge=0, le=65535)
    db_name: str

    db_pool_max_overflow: int = Field(10, ge=0)
    db_pool_timeout: int = Field(10, ge=0)
    db_pool_size: int = Field(5, ge=0)

    openai_api_key: str

    log_level: str = "INFO"
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
    )

settings = Settings()
