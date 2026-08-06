from pathlib import Path

import pytest
from pydantic import SecretStr

from config.settings import Settings, get_settings


def test_settings_loads_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "IBKR_HOST=127.0.0.1",
                "IBKR_PORT=7497",
                "IBKR_CLIENT_ID=1",
                "ANTHROPIC_API_KEY=test-key",
            ]
        )
    )

    monkeypatch.setenv("ENV_FILE", str(env_file))
    monkeypatch.delenv("IBKR_HOST", raising=False)
    monkeypatch.delenv("IBKR_PORT", raising=False)
    monkeypatch.delenv("IBKR_CLIENT_ID", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    settings = Settings.model_validate(
        {
            "ibkr_host": "127.0.0.1",
            "ibkr_port": 7497,
            "ibkr_client_id": 1,
            "anthropic_api_key": "test-key",
            "data_cache_dir": tmp_path / "cache",
            "control_dir": tmp_path / "control",
        }
    )

    assert settings.ibkr_host == "127.0.0.1"
    assert settings.ibkr_port == 7497
    assert settings.ibkr_client_id == 1
    assert settings.anthropic_api_key == SecretStr("test-key")
    assert settings.data_cache_dir == tmp_path / "cache"
    assert settings.control_dir == tmp_path / "control"


def test_missing_required_env_field_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IBKR_HOST", raising=False)
    monkeypatch.delenv("IBKR_PORT", raising=False)
    monkeypatch.delenv("IBKR_CLIENT_ID", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(Exception) as exc_info:
        Settings.model_validate(
            {
                "ibkr_port": 7497,
                "ibkr_client_id": 1,
                "anthropic_api_key": "test-key",
                "data_cache_dir": Path("cache"),
                "control_dir": Path("control"),
            }
        )

    assert "IBKR_HOST" in str(exc_info.value)
