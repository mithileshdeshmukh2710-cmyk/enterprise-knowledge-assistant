from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    frontend_url: str = "http://localhost:5173"
    app_api_key: str = ""
    max_upload_size_mb: int = 10
    chroma_persist_dir: str = str(
        Path(__file__).resolve().parents[2] / "data" / "chromadb"
    )
    document_metadata_path: str = str(
        Path(__file__).resolve().parents[2] / "data" / "document_metadata.json"
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

