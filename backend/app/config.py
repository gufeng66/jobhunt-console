from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    username: str = "admin"
    initial_password: str
    jwt_secret: str
    upload_dir: str = "uploads"


settings = Settings()
