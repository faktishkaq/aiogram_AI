import asyncio
import logging

from aiogram import Bot, Dispatcher

from access import AccessService
from config import Settings
from cursor_client import CursorClient
from handlers import ChatService, build_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = Settings.load()
    access = AccessService()

    if not access.list_admins():
        logger.warning(
            "Список админов пуст. Добавьте себя: python admin_cli.py add YOUR_TELEGRAM_ID"
        )

    bot = Bot(token=settings.telegram_token)
    cursor = CursorClient(settings)
    service = ChatService(cursor)
    dp = Dispatcher()
    dp.include_router(build_router(service, access))

    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    finally:
        await cursor.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
