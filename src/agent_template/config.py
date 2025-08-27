from __future__ import annotations

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Read OPENAI_API_KEY for the OpenAI Python SDK
    openai_api_key: str = Field(alias="OPENAI_API_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def require(cls) -> Settings:
        try:
            return cls()  # will validate OPENAI_API_KEY
        except ValidationError as e:
            raise RuntimeError(
                "Missing required env vars (see .env.example). At minimum set OPENAI_API_KEY."
            ) from e
