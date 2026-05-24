from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/events"
    events_provider_base_url: str = "http://events-provider.dev-2.python-labs.ru"
    events_provider_api_key: str = "your-api-key"
    sync_interval_seconds: int = 86400  # раз в день

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
