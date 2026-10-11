from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    # Windows 自己占用了 USERNAME，这里不用那个变量。
    username: str = Field(default="admin", validation_alias="APP_USERNAME")
    initial_password: str
    jwt_secret: str
    upload_dir: str = "uploads"


settings = Settings()
