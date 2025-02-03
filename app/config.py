from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    root_path: str = ""
    db_container_path: str = "/app/.sqlite/data"
    db_name: str = "database.sqlite"


config = Settings()
