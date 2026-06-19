import json
from pathlib import Path
from typing import Any

from config import AGENTS_FILE, DATA_DIR


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_agents() -> dict[str, str]:
    _ensure_data_dir()
    if not AGENTS_FILE.exists():
        return {}
    try:
        data: dict[str, Any] = json.loads(AGENTS_FILE.read_text(encoding="utf-8"))
        return {str(k): str(v) for k, v in data.items()}
    except (json.JSONDecodeError, OSError):
        return {}


def save_agent(user_id: int, agent_id: str) -> None:
    agents = load_agents()
    agents[str(user_id)] = agent_id
    _ensure_data_dir()
    AGENTS_FILE.write_text(
        json.dumps(agents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def delete_agent(user_id: int) -> None:
    agents = load_agents()
    agents.pop(str(user_id), None)
    _ensure_data_dir()
    AGENTS_FILE.write_text(
        json.dumps(agents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
