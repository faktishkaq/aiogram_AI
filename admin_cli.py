#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from access import AccessService


def cmd_list(access: AccessService) -> int:
    admins = access.list_admins()
    if not admins:
        print("Список админов пуст.")
        return 0
    print("Админы с доступом к боту:")
    for admin in admins:
        username = f"@{admin.username}" if admin.username else "без username"
        added = admin.added_at or "—"
        print(f"  {admin.user_id} ({username}), добавлен: {added}")
    return 0


def cmd_add(access: AccessService, user_id: int, username: str | None) -> int:
    if access.add_admin(user_id, username):
        print(f"Админ {user_id} добавлен.")
        return 0
    print(f"Админ {user_id} уже существует.")
    return 1


def cmd_remove(access: AccessService, user_id: int) -> int:
    if access.remove_admin(user_id):
        print(f"Админ {user_id} удалён.")
        return 0
    print(f"Админ {user_id} не найден.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Управление доступом к Telegram-боту (список админов).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="Показать всех админов")

    add_parser = subparsers.add_parser("add", help="Выдать доступ пользователю")
    add_parser.add_argument("user_id", type=int, help="Telegram user id")
    add_parser.add_argument(
        "--username",
        help="Telegram username без @ (необязательно)",
    )

    remove_parser = subparsers.add_parser("remove", help="Забрать доступ")
    remove_parser.add_argument("user_id", type=int, help="Telegram user id")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    access = AccessService()

    if args.command == "list":
        return cmd_list(access)
    if args.command == "add":
        username = args.username.lstrip("@") if args.username else None
        return cmd_add(access, args.user_id, username)
    if args.command == "remove":
        return cmd_remove(access, args.user_id)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
