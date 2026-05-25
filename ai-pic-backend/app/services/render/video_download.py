"""Retrying download helpers for render video assets."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Sequence
from typing import Any

import aiohttp
from app.core.logging import get_logger

logger = get_logger()


async def download_video(
    url: str,
    session: aiohttp.ClientSession,
    *,
    retries: int = 3,
    retry_delay_seconds: float = 1.0,
) -> bytes:
    """Download video bytes with bounded retry for transient connection failures."""
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise ValueError(
                        f"Failed to download video: {url} (status={resp.status})"
                    )
                return await resp.read()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            logger.warning(
                "Video download failed on attempt %s/%s: %s",
                attempt,
                retries,
                exc,
            )
            await asyncio.sleep(retry_delay_seconds * attempt)
    raise last_error or RuntimeError(f"Failed to download video: {url}")


async def download_url(url: str) -> bytes:
    timeout = aiohttp.ClientTimeout(total=180)
    connector = aiohttp.TCPConnector(force_close=True, limit=4)
    headers = {"User-Agent": "ai-video-studio-render/1.0"}
    async with aiohttp.ClientSession(
        connector=connector,
        headers=headers,
        timeout=timeout,
    ) as session:
        return await download_video(url, session)


async def download_all_clips(
    clips: Sequence[Any],
    work_dir: str,
) -> list[str]:
    """Download all video clips to work directory in render order."""
    paths: list[str] = []
    timeout = aiohttp.ClientTimeout(total=180)
    connector = aiohttp.TCPConnector(force_close=True, limit=4)
    headers = {"User-Agent": "ai-video-studio-render/1.0"}
    async with aiohttp.ClientSession(
        connector=connector,
        headers=headers,
        timeout=timeout,
    ) as session:
        for index, clip in enumerate(clips):
            try:
                data = await download_video(str(clip.url), session)
                path = os.path.join(work_dir, f"clip_{index:03d}.mp4")
                with open(path, "wb") as file:
                    file.write(data)
                paths.append(path)
                logger.info(
                    "Downloaded clip %s/%s: %s bytes",
                    index + 1,
                    len(clips),
                    len(data),
                )
            except Exception as exc:
                logger.error("Failed to download clip %s: %s", index, exc)
                raise
    return paths
