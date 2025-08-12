# Конфигурация приложения с использованием Vault для хранения секретов
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import hvac

# Основные настройки приложения, загружаемые из Vault
class Settings(BaseSettings):
    vault_url: str = Field(..., json_schema_extra={"env": "VAULT_URL"})
    vault_token: str = Field(..., json_schema_extra={"env": "VAULT_TOKEN"})
    env: str = Field("test", json_schema_extra={"env": "ENVIRONMENT"})

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
        secrets = self.client.secrets.kv.v2.read_secret_version(path='chatbot_noso/secrets')['data']['data']
        self.bot_token = secrets['BOT_TOKEN']
        self.deepseek_api_key = secrets['DEEPSEEK_API_KEY']
        self.database_url = secrets['DATABASE_URL']
        self.redis_url = secrets['REDIS_URL']
        self.sro_api_url = secrets['SRO_API_URL']

# Глобальный экземпляр настроек приложения
settings = Settings()
