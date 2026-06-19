# Telegram AI Bot (Cursor)

Telegram-бот, который отвечает через **Cursor Cloud Agents API** (`CURSOR_API_KEY`).

## Возможности

- Текст и ссылки
- Фото (с подписью)
- Голосовые сообщения (распознавание речи)
- Видео и video note (анализ превью + метаданных)
- Быстрые ответы через модель `composer-2.5` с параметром `fast`

## Быстрый старт

1. Создайте бота в [@BotFather](https://t.me/BotFather) и получите `TELEGRAM_BOT_TOKEN`.
2. Получите API-ключ Cursor: [Dashboard → Integrations](https://cursor.com/dashboard/integrations).
3. Скопируйте `.env.example` в `.env` и заполните переменные.
4. Установите зависимости и запустите бота.

```bash
pip install -r requirements.txt
python bot.py
```

### Голосовые сообщения

Для конвертации `.ogg` нужен **ffmpeg** в PATH:

- Windows: `winget install Gyan.FFmpeg`
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `CURSOR_API_KEY` | API-ключ Cursor (`cursor_...`) |
| `CURSOR_MODEL` | Модель (по умолчанию `composer-2.5`) |
| `CURSOR_RUNTIME` | `cloud` (по умолчанию) |

## Команды бота

- Кнопки снизу: **Помощь**, **Новый диалог**
- `/start` — приветствие и меню

## Доступ (только админы)

Писать боту могут только пользователи из белого списка. Управление через консоль:

```bash
# Показать админов
python admin_cli.py list

# Выдать доступ (узнай свой id у @userinfobot)
python admin_cli.py add 123456789

# Забрать доступ
python admin_cli.py remove 123456789
```

Список хранится в `data/admins.json`. Изменения применяются сразу, перезапуск бота не нужен.

## Примечания

- Контекст диалога сохраняется per-user в `data/agents.json`.
- Первый ответ может занять несколько секунд — Cursor поднимает cloud agent.
- Для продакшена рекомендуется запуск через systemd, Docker или PM2.
