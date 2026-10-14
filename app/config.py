from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ENV_TEMPLATE = """# Copy this file to .env for local configuration
YOUTUBE_CLIENT_SECRET_PATH=credentials/client_secret.json
YOUTUBE_TOKEN_PATH=credentials/token.json
YOUTUBE_DEFAULT_PRIVACY=private
YOUTUBE_DEFAULT_TAGS=shorts,youtube,automation
"""


def _read_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_settings() -> dict[str, str]:
    env_values = _read_env_file(PROJECT_ROOT / ".env")
    env_values.update({
        key: value
        for key, value in os.environ.items()
        if key.startswith("YOUTUBE_") or key in {"YOUTUBE_CLIENT_SECRET_PATH", "YOUTUBE_TOKEN_PATH"}
    })

    defaults = {
        "YOUTUBE_CLIENT_SECRET_PATH": "credentials/client_secret.json",
        "YOUTUBE_TOKEN_PATH": "credentials/token.json",
        "YOUTUBE_DEFAULT_PRIVACY": "private",
        "YOUTUBE_DEFAULT_TAGS": "shorts,youtube,automation",
    }

    for key, value in defaults.items():
        env_values.setdefault(key, value)

    return env_values


def resolve_path(path_value: str | None) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return str(path)


def get_client_secret_path() -> str:
    settings = load_settings()
    return resolve_path(settings.get("YOUTUBE_CLIENT_SECRET_PATH", "credentials/client_secret.json"))


def get_token_path() -> str:
    settings = load_settings()
    return resolve_path(settings.get("YOUTUBE_TOKEN_PATH", "credentials/token.json"))


def get_default_privacy() -> str:
    return load_settings().get("YOUTUBE_DEFAULT_PRIVACY", "private")


def get_default_tags() -> list[str]:
    tags_raw = load_settings().get("YOUTUBE_DEFAULT_TAGS", "shorts,youtube,automation")
    return [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
