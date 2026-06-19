from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты полезный AI-ассистент в Telegram. "
    "Отвечай кратко, по делу и на языке пользователя. "
    "Не пиши код и не запускай инструменты, если пользователь явно этого не просит. "
    "Если прислали фото, видео или ссылку — проанализируй и дай понятный ответ."
)


@dataclass
class CursorResponse:
    text: str
    agent_id: str
    run_id: str


class CursorClient:
    _STREAM_UNAVAILABLE_MARKERS = (
        "stream_expired",
        "no longer available",
        "stream unavailable",
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.cursor_api_base,
            auth=(settings.cursor_api_key, ""),
            timeout=httpx.Timeout(300.0, connect=30.0),
            headers={"Content-Type": "application/json"},
        )

    async def close(self) -> None:
        await self._client.aclose()

    @classmethod
    def _is_stream_unavailable(cls, code: str | None, message: str | None) -> bool:
        values = [value for value in (code, message) if value]
        lowered = " ".join(values).lower()
        return any(marker in lowered for marker in cls._STREAM_UNAVAILABLE_MARKERS)

    def _model_payload(self) -> dict[str, Any]:
        return {
            "id": self._settings.cursor_model,
            "params": [{"id": "fast", "value": "true"}],
        }

    async def create_agent(self, prompt_text: str, images: list[dict[str, Any]] | None = None) -> tuple[str, str]:
        prompt: dict[str, Any] = {"text": prompt_text}
        if images:
            prompt["images"] = images

        payload: dict[str, Any] = {
            "prompt": prompt,
            "model": self._model_payload(),
            "mode": "agent",
        }

        response = await self._client.post("/v1/agents", json=payload)
        response.raise_for_status()
        data = response.json()
        agent_id = data["agent"]["id"]
        run_id = data["run"]["id"]
        return agent_id, run_id

    async def send_followup(
        self,
        agent_id: str,
        prompt_text: str,
        images: list[dict[str, Any]] | None = None,
    ) -> str:
        prompt: dict[str, Any] = {"text": prompt_text}
        if images:
            prompt["images"] = images

        response = await self._client.post(
            f"/v1/agents/{agent_id}/runs",
            json={"prompt": prompt},
        )
        if response.status_code == 409:
            await self._wait_until_agent_idle(agent_id)
            response = await self._client.post(
                f"/v1/agents/{agent_id}/runs",
                json={"prompt": prompt},
            )
        response.raise_for_status()
        return response.json()["run"]["id"]

    async def _wait_until_agent_idle(self, agent_id: str, timeout: float = 120.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            response = await self._client.get(f"/v1/agents/{agent_id}")
            response.raise_for_status()
            latest_run_id = response.json().get("latestRunId")
            if not latest_run_id:
                return

            run = await self._get_run(agent_id, latest_run_id)
            status = run.get("status", "")
            if status in {"FINISHED", "ERROR", "CANCELLED", "EXPIRED"}:
                return
            await asyncio.sleep(1.0)
        raise TimeoutError("Cursor agent is busy too long")

    async def _get_run(self, agent_id: str, run_id: str) -> dict[str, Any]:
        response = await self._client.get(f"/v1/agents/{agent_id}/runs/{run_id}")
        response.raise_for_status()
        return response.json()

    async def stream_run(self, agent_id: str, run_id: str) -> AsyncIterator[str]:
        url = f"/v1/agents/{agent_id}/runs/{run_id}/stream"
        accumulated = ""

        try:
            async with self._client.stream("GET", url) as response:
                if response.status_code == 410:
                    logger.info("Run stream expired for %s, will poll run result", run_id)
                    return
                response.raise_for_status()
                event_name: str | None = None

                async for raw_line in response.aiter_lines():
                    if not raw_line:
                        continue

                    if raw_line.startswith("event:"):
                        event_name = raw_line[6:].strip()
                        continue

                    if not raw_line.startswith("data:"):
                        continue

                    payload_raw = raw_line[5:].strip()
                    if not payload_raw:
                        continue

                    try:
                        payload = json.loads(payload_raw)
                    except json.JSONDecodeError:
                        continue

                    if event_name == "assistant":
                        delta = payload.get("text", "")
                        if delta:
                            accumulated += delta
                            yield accumulated
                    elif event_name == "result":
                        final_text = payload.get("text") or accumulated
                        if final_text and final_text != accumulated:
                            yield final_text
                        return
                    elif event_name == "error":
                        message = payload.get("message", "Unknown Cursor stream error")
                        code = payload.get("code")
                        if self._is_stream_unavailable(code, message):
                            logger.info(
                                "Run stream unavailable for %s (%s), will poll run result",
                                run_id,
                                message,
                            )
                            return
                        raise RuntimeError(message)
                    elif event_name == "done":
                        if accumulated:
                            yield accumulated
                        return
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 410:
                logger.info("Run stream expired for %s, will poll run result", run_id)
                return
            raise

        if accumulated:
            yield accumulated

    async def wait_for_result(self, agent_id: str, run_id: str) -> str:
        deadline = time.monotonic() + 300.0
        while time.monotonic() < deadline:
            run = await self._get_run(agent_id, run_id)
            status = run.get("status", "")
            if status == "FINISHED":
                result = run.get("result") or ""
                if result.strip():
                    return result.strip()
                raise RuntimeError("Cursor returned an empty response")
            if status in {"ERROR", "CANCELLED", "EXPIRED"}:
                raise RuntimeError(f"Cursor run failed with status {status}")
            await asyncio.sleep(1.0)
        raise TimeoutError("Cursor response timed out")

    async def _collect_stream_text(self, agent_id: str, run_id: str) -> str:
        text = ""
        async for chunk in self.stream_run(agent_id, run_id):
            text = chunk
        return text.strip()

    async def ask(
        self,
        user_text: str,
        agent_id: str | None = None,
        images: list[dict[str, Any]] | None = None,
    ) -> CursorResponse:
        if agent_id:
            run_id = await self.send_followup(agent_id, user_text, images)
        else:
            agent_id, run_id = await self.create_agent(user_text, images)

        text = await self._collect_stream_text(agent_id, run_id)
        if not text:
            text = await self.wait_for_result(agent_id, run_id)

        return CursorResponse(text=text.strip(), agent_id=agent_id, run_id=run_id)

    async def ensure_agent(self, user_id: int, stored_agent_id: str | None) -> str | None:
        if not stored_agent_id:
            return None
        try:
            response = await self._client.get(f"/v1/agents/{stored_agent_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return stored_agent_id
        except httpx.HTTPError:
            logger.warning("Stored agent %s for user %s is unavailable", stored_agent_id, user_id)
            return None
