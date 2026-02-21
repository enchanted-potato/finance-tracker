from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str
    firebase_credentials_path: str = ""
    firebase_web_api_key: str = ""
    firebase_auth_domain: str = ""
    firebase_project_id: str = ""
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
