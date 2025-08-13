# Конфигурация приложения
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field(..., json_schema_extra={"env": "BOT_TOKEN"})
    deepseek_api_key: str = Field(..., json_schema_extra={"env": "DEEPSEEK_API_KEY"})
    database_url: str = Field(..., json_schema_extra={"env": "DATABASE_URL"})
    redis_url: str = Field(..., json_schema_extra={"env": "REDIS_URL"})
    sro_api_url: str = Field(..., json_schema_extra={"env": "SRO_API_URL"})
    env: str = Field("development", json_schema_extra={"env": "ENVIRONMENT"})

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
