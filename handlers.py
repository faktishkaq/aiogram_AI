from __future__ import annotations

import asyncio
import base64
import io
import logging
import re
from typing import Any

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import Message

from access import AccessMiddleware, AccessService
from cursor_client import CursorClient, SYSTEM_PROMPT
from keyboards import BTN_HELP, BTN_NEW, MENU_BUTTONS, main_menu_keyboard
from storage import delete_agent, load_agents, save_agent

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
MAX_TELEGRAM_MESSAGE = 4096

HELP_TEXT = (
    "Отправь:\n"
    "• текст или ссылку\n"
    "• голосовое сообщение\n"
    "• фото (можно с подписью)\n"
    "• видео (анализирую превью и подпись)\n\n"
    "Кнопка «Новый диалог» сбрасывает контекст."
)

WELCOME_TEXT = (
    "Привет! Я AI-бот на Cursor.\n\n"
    "Можешь писать текст, присылать голосовые, фото, видео и ссылки — я отвечу.\n\n"
    "Используй кнопки меню снизу."
)


def split_message(text: str, limit: int = MAX_TELEGRAM_MESSAGE) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    for paragraph in text.split("\n"):
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(paragraph) > limit:
            chunks.append(paragraph[:limit])
            paragraph = paragraph[limit:]
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


async def download_file_bytes(bot: Bot, file_id: str) -> bytes:
    file = await bot.get_file(file_id)
    if not file.file_path:
        raise RuntimeError("Telegram file path is empty")
    buffer = io.BytesIO()
    await bot.download_file(file.file_path, destination=buffer)
    return buffer.getvalue()


def image_payload(data: bytes, mime_type: str) -> dict[str, Any]:
    return {
        "data": base64.b64encode(data).decode("ascii"),
        "mimeType": mime_type,
    }


async def transcribe_voice(bot: Bot, file_id: str) -> str:
    try:
        import speech_recognition as sr
        from pydub import AudioSegment
    except ImportError as exc:
        raise RuntimeError("Voice support requires SpeechRecognition and pydub") from exc

    raw = await download_file_bytes(bot, file_id)
    audio = AudioSegment.from_file(io.BytesIO(raw), format="ogg")
    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_buffer) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data, language="ru-RU")
    except sr.UnknownValueError:
        text = recognizer.recognize_google(audio_data, language="en-US")
    return text.strip()


def build_text_prompt(message: Message, body: str) -> str:
    parts = [body.strip()]
    if message.caption:
        parts.append(f"Подпись: {message.caption.strip()}")
    if message.text and message.text != body:
        parts.append(message.text.strip())
    urls = URL_PATTERN.findall(message.text or message.caption or body)
    if urls:
        parts.append("Ссылки:\n" + "\n".join(dict.fromkeys(urls)))
    return "\n\n".join(part for part in parts if part)


class ChatService:
    def __init__(self, cursor: CursorClient) -> None:
        self._cursor = cursor
        self._agents = load_agents()
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock_for(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def reset(self, user_id: int) -> None:
        delete_agent(user_id)
        self._agents.pop(str(user_id), None)

    async def get_agent_id(self, user_id: int) -> str | None:
        stored = self._agents.get(str(user_id))
        valid = await self._cursor.ensure_agent(user_id, stored)
        if stored and not valid:
            await self.reset(user_id)
        return valid

    async def ask(
        self,
        user_id: int,
        prompt: str,
        images: list[dict[str, Any]] | None = None,
    ) -> str:
        async with self._lock_for(user_id):
            agent_id = await self.get_agent_id(user_id)
            if not agent_id:
                first_prompt = f"{SYSTEM_PROMPT}\n\nСообщение пользователя:\n{prompt}"
                response = await self._cursor.ask(first_prompt, images=images)
                save_agent(user_id, response.agent_id)
                return response.text

            response = await self._cursor.ask(prompt, agent_id=agent_id, images=images)
            save_agent(user_id, response.agent_id)
            return response.text


async def _delete_message(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def reply_text(
    message: Message,
    text: str,
    *,
    with_menu: bool = True,
) -> None:
    chunks = split_message(text)
    for index, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            reply_markup=main_menu_keyboard() if with_menu and index == len(chunks) - 1 else None,
        )


async def reply_error(message: Message, status: Message, error_text: str) -> None:
    try:
        await status.edit_text(error_text)
    except TelegramBadRequest:
        await _delete_message(status)
        await reply_text(message, error_text)


async def process_with_status(
    message: Message,
    service: ChatService,
    prompt: str,
    images: list[dict[str, Any]] | None = None,
) -> None:
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    # Reply-keyboard messages cannot be edited in Telegram.
    status = await message.answer("Думаю...")

    try:
        answer = await service.ask(message.from_user.id, prompt, images)
        if not answer.strip():
            raise RuntimeError("Cursor вернул пустой ответ")

        await _delete_message(status)
        await reply_text(message, answer)
    except Exception as exc:
        logger.exception("Failed to process message")
        await reply_error(message, status, f"Ошибка: {exc}")


def build_router(service: ChatService, access: AccessService) -> Router:
    router = Router()
    router.message.middleware(AccessMiddleware(access))

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await message.answer(
            WELCOME_TEXT,
            reply_markup=main_menu_keyboard(),
        )

    @router.message(F.text == BTN_HELP)
    async def menu_help(message: Message) -> None:
        await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())

    @router.message(F.text == BTN_NEW)
    async def menu_new(message: Message) -> None:
        await service.reset(message.from_user.id)
        await message.answer("Новый диалог начат.", reply_markup=main_menu_keyboard())

    @router.message(F.text)
    async def handle_text(message: Message) -> None:
        if message.text in MENU_BUTTONS:
            return
        prompt = build_text_prompt(message, message.text or "")
        await process_with_status(message, service, prompt)

    @router.message(F.photo)
    async def handle_photo(message: Message) -> None:
        photo = message.photo[-1]
        data = await download_file_bytes(message.bot, photo.file_id)
        prompt = build_text_prompt(message, "Пользователь прислал фото. Опиши и ответь по содержанию.")
        await process_with_status(message, service, prompt, [image_payload(data, "image/jpeg")])

    @router.message(F.voice)
    async def handle_voice(message: Message) -> None:
        await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        status = await message.answer("Распознаю голос...")
        try:
            transcript = await transcribe_voice(message.bot, message.voice.file_id)
            prompt = build_text_prompt(message, f"Голосовое сообщение (транскрипт): {transcript}")
            await _delete_message(status)
            await process_with_status(message, service, prompt)
        except Exception as exc:
            logger.exception("Voice transcription failed")
            await reply_error(message, status, f"Не удалось распознать голос: {exc}")

    @router.message(F.video)
    async def handle_video(message: Message) -> None:
        video = message.video
        images: list[dict[str, Any]] | None = None
        if video.thumbnail:
            thumb = await download_file_bytes(message.bot, video.thumbnail.file_id)
            images = [image_payload(thumb, "image/jpeg")]

        details = [
            "Пользователь прислал видео.",
            f"Длительность: {video.duration} сек.",
        ]
        if video.file_name:
            details.append(f"Имя файла: {video.file_name}")
        prompt = build_text_prompt(message, "\n".join(details))
        await process_with_status(message, service, prompt, images)

    @router.message(F.video_note)
    async def handle_video_note(message: Message) -> None:
        note = message.video_note
        images: list[dict[str, Any]] | None = None
        if note.thumbnail:
            thumb = await download_file_bytes(message.bot, note.thumbnail.file_id)
            images = [image_payload(thumb, "image/jpeg")]
        prompt = build_text_prompt(
            message,
            f"Пользователь прислал видео-кружок длительностью {note.length} сек.",
        )
        await process_with_status(message, service, prompt, images)

    @router.message(F.document)
    async def handle_document(message: Message) -> None:
        document = message.document
        mime = document.mime_type or ""
        if mime.startswith("image/"):
            data = await download_file_bytes(message.bot, document.file_id)
            prompt = build_text_prompt(message, "Пользователь прислал изображение.")
            await process_with_status(message, service, prompt, [image_payload(data, mime)])
            return
        prompt = build_text_prompt(
            message,
            f"Пользователь прислал файл: {document.file_name or 'без имени'} ({mime or 'unknown type'}). "
            "Файл нельзя прочитать напрямую — ответь по названию и подписи.",
        )
        await process_with_status(message, service, prompt)

    return router
