import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).resolve().parent / "data"
AGENTS_FILE = DATA_DIR / "agents.json"
ADMINS_FILE = DATA_DIR / "admins.json"


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    cursor_api_key: str
    cursor_model: str
    cursor_runtime: str
    cursor_api_base: str

    @classmethod
    def load(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        api_key = os.getenv("CURSOR_API_KEY", "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
        if not api_key:
            raise RuntimeError("CURSOR_API_KEY is not set")

        runtime = os.getenv("CURSOR_RUNTIME", "cloud").strip().lower()
        if runtime not in {"cloud", "local"}:
            raise RuntimeError("CURSOR_RUNTIME must be 'cloud' or 'local'")

        return cls(
            telegram_token=token,
            cursor_api_key=api_key,
            cursor_model=os.getenv("CURSOR_MODEL", "composer-2.5").strip(),
            cursor_runtime=runtime,
            cursor_api_base=os.getenv(
                "CURSOR_API_BASE", "https://api.cursor.com"
            ).strip().rstrip("/"),
        )
