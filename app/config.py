from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    bot_token: str = Field(..., env="BOT_TOKEN")
    deepseek_key: str = Field("your_api_key_here", env="DEEPSEEK_API_KEY")
    db_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    env: str = Field("development", env="ENVIRONMENT")

    class Config:
        env_file = ".env"

settings = Settings()
