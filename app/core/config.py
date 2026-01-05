# import os
from pydantic_settings import BaseSettings, SettingsConfigDict


# load env variables from .env and make it available to the app with the name settings
class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"  # hash algorithm for jwt
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 180

    # Another Approach => directly get the env variables and if not found use the default values
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db/postgres")
    # SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 180))
    # Debug Mode
    # DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    model_config = SettingsConfigDict(env_file=".env")
    # class Config:
    #     env_file = ".env"


settings = Settings()  # type: ignore
