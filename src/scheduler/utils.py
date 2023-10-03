import os
from datetime import datetime
from typing import Any

import yt_dlp
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.config import Config
from src.constants import PROJECT_ROOT_DIR
from src.telegram_notify_job import send_report


async def setup_scheduler(conf: Config, bot: Bot) -> AsyncIOScheduler:
    """
    :param conf:
    :param bot:
    :return:
    """

    scheduler = AsyncIOScheduler()

    ydl_opts: dict[str, Any] = {
        "cookiefile": os.path.join(PROJECT_ROOT_DIR, "cookies.txt"),
        "quiet": True,
        "load-pages": False,
        "extract_flat": False,
        "skip_download": True,
        "getcomments": False,
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)

    notify_kwargs = {
        "bot": bot,
        "channels": conf.channels,
        "chat_id": conf.chat_id,
        "temp_chat_id": conf.temp_chat_id,
        "ydl": ydl,
    }

    scheduler.add_job(
        send_report,
        trigger=IntervalTrigger(seconds=conf.interval_s),
        kwargs=notify_kwargs,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(),
    )

    return scheduler


__all__ = ["setup_scheduler"]
