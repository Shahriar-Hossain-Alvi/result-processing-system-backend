from pydantic_settings import BaseSettings

#load env variables from .env and make it available to the app with the name settings
class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256" # hash algorithm for jwt
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings() #type: ignore