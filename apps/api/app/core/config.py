from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    app_env: str = "development"
    api_port: int = 8000
    frontend_origin: str = "http://localhost:3000"

    # LLM settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = ""

    # Hindsight memory settings
    hindsight_api_key: str = ""
    hindsight_base_url: str = "https://api.hindsight.ai"
    hindsight_bank_id: str = ""

    # Voice settings
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "JBFqnCBsd6RMkjVDRZzb"

    # Supabase Auth + REST
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_audience: str = "authenticated"

    # Jobs and scheduler
    jobs_provider: str = "hybrid"
    jobs_api_key: str = ""
    jobs_api_url: str = ""
    firecrawl_api_key: str = ""
    firecrawl_base_url: str = "https://api.firecrawl.dev/v2"
    scheduler_enabled: bool = True
    scheduler_cron: str = "0 8 * * *"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    # Singleton settings to avoid re-parsing env on every request
    return Settings()
