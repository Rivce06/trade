"""Environment-backed settings for QuantDesk.

This module centralizes configuration access behind a single cached
`Settings` object so downstream modules never read raw environment
variables directly.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings loaded from the environment.

    The fields are intentionally declared in the public Python style
    (`ibkr_host`, `ibkr_port`, ...) while the real environment variable
    names remain `IBKR_HOST`, `IBKR_PORT`, and so on.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    ibkr_host: str = Field(alias="IBKR_HOST")
    ibkr_port: int = Field(alias="IBKR_PORT")
    ibkr_client_id: int = Field(alias="IBKR_CLIENT_ID")
    anthropic_api_key: SecretStr = Field(alias="ANTHROPIC_API_KEY")
    data_cache_dir: Path = Field(default=Path("data/cache"), alias="DATA_CACHE_DIR")
    control_dir: Path = Field(default=Path("control"), alias="CONTROL_DIR")

    @classmethod
    def model_validate(cls, obj: object, *, from_attributes: bool = False, **kwargs):
        """Validate a dictionary using either the Python field names or env aliases.

        This keeps the public constructor ergonomic while preserving the
        contract that required values map to the documented environment
        variables.
        """

        return super().model_validate(obj, from_attributes=from_attributes, **kwargs)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings instance for the current process.

    Returns:
        Settings: the parsed and validated environment-backed settings.
    """

    return Settings()
