from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    FIREBASE_CREDENTIALS: str
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    PROJECT_NAME: str = "SHIFT SCALL API"
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str
    play_ht_user_id: str
    play_ht_api_key: str
    openai_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
