from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import ADMINS_FILE, DATA_DIR


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict[str, Any]:
    _ensure_data_dir()
    if not ADMINS_FILE.exists():
        return {"admins": {}}
    try:
        data = json.loads(ADMINS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"admins": {}}
    if "admins" not in data or not isinstance(data["admins"], dict):
        return {"admins": {}}
    return data


def _save_raw(data: dict[str, Any]) -> None:
    _ensure_data_dir()
    ADMINS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


@dataclass(frozen=True)
class AdminRecord:
    user_id: int
    username: str | None
    added_at: str


class AccessService:
    def __init__(self) -> None:
        self._admins = self._load()

    def _load(self) -> dict[int, AdminRecord]:
        raw = _load_raw()
        admins: dict[int, AdminRecord] = {}
        for user_id, info in raw["admins"].items():
            if not str(user_id).isdigit():
                continue
            if isinstance(info, dict):
                admins[int(user_id)] = AdminRecord(
                    user_id=int(user_id),
                    username=info.get("username"),
                    added_at=info.get("added_at", ""),
                )
            else:
                admins[int(user_id)] = AdminRecord(
                    user_id=int(user_id),
                    username=None,
                    added_at="",
                )
        return admins

    def reload(self) -> None:
        self._admins = self._load()

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._admins

    def list_admins(self) -> list[AdminRecord]:
        return sorted(self._admins.values(), key=lambda item: item.user_id)

    def add_admin(self, user_id: int, username: str | None = None) -> bool:
        if user_id in self._admins:
            return False
        record = AdminRecord(
            user_id=user_id,
            username=username,
            added_at=datetime.now(timezone.utc).isoformat(),
        )
        self._admins[user_id] = record
        self._persist()
        return True

    def remove_admin(self, user_id: int) -> bool:
        if user_id not in self._admins:
            return False
        del self._admins[user_id]
        self._persist()
        return True

    def _persist(self) -> None:
        data = {
            "admins": {
                str(record.user_id): {
                    "username": record.username,
                    "added_at": record.added_at,
                }
                for record in self._admins.values()
            }
        }
        _save_raw(data)


class AccessMiddleware(BaseMiddleware):
    def __init__(self, access: AccessService) -> None:
        self._access = access

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, Message) and event.from_user:
            self._access.reload()
            if not self._access.is_admin(event.from_user.id):
                await event.answer(
                    "⛔ У вас нет доступа к боту.\n"
                    "Попросите администратора выдать доступ через консоль."
                )
                return
        return await handler(event, data)
