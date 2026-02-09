# import os
from typing import Any, List
from pydantic import field_validator
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
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    SUPER_ADMIN_EMAIL: str
    SUPER_ADMIN_PASSWORD: str

    # This reads the string and splits it into a list
    CORS_ORIGINS: Any = []  # Default fallback

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Any) -> List[str]:
        # Handle string input from ENV
        if isinstance(value, str):
            # If it's a string from .env, split it
            if not value.startswith("["):
                # Handles "url1, url2" -> ["url1", "url2"]
                return [item.strip() for item in value.split(",") if item.strip()]

            import json
            try:
                return json.loads(value)
            except:
                return []

        if isinstance(value, (list, tuple)):
            return list(value)
        return []

    # Another Approach => directly get the env variables and if not found use the default values
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db/postgres")
    # SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 180))
    # Debug Mode
    # DEBUG: bool = os.getenv("DEBUG", "True") == "True"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # it ignores the env variables that are not in the pydantic model
    )
    # class Config:
    #     env_file = ".env"


settings = Settings()  # type: ignore
