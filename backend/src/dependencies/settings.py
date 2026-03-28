from functools import lru_cache

from src.settings import Settings, settings


@lru_cache()
def get_settings() -> Settings:
    return settings
