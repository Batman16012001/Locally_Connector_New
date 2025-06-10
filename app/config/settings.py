from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "locally_staging"
    batch_size: int = 500
    rate_limit_requests: int = 5
    rate_limit_period: int = 60

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings() 