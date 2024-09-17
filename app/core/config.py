from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    FIREBASE_CREDENTIALS: str
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    PROJECT_NAME: str = "SHIFT SCALL API"

    class Config:
        env_file = ".env.dev"


settings = Settings()
