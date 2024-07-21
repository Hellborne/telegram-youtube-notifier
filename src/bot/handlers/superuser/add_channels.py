from io import TextIOWrapper
from typing import BinaryIO
from typing import Optional
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram import F
from aiogram import Router
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import File
from aiogram.types import Message
from sulguk import SULGUK_PARSE_MODE

from ....db import DataAccessLayer
from ....dto import ChannelCreateDTO
from ....dto import ChannelRetrieveDTO
from ...filters import RoleFilter
from ...filters import UserRole
from ...states import ChannelsSG
from src.utils import youtube_channel_url_validator

add_channels_router = Router(name="add_channels")
last_command_time = {}

@add_channels_router.message(
    Command("add_channels"),
    RoleFilter(role=[UserRole.SUPERUSER]),
    State(state="*"),
)
async def add_channels(message: Message, state: FSMContext, **kwargs) -> None:
    await message.answer(
        text="Upload a file with format: <br/>"
             "<code>url[TAB]label[END_ROW]</code><br/>"
             "every single line == channel to insert.<br/>"
             "Set channel url in format: <b>https://www.youtube.com/@username</b>"
             "Enter /cancel for exit <br/>",
        parse_mode=SULGUK_PARSE_MODE,
    )
    await state.set_state(ChannelsSG.bulk_channels)


@add_channels_router.message(
    F.content_type == ContentType.DOCUMENT,
    RoleFilter(role=[UserRole.SUPERUSER]),
    StateFilter(ChannelsSG.bulk_channels),
)
async def channel_file_handler(
        message: Message, state: FSMContext, bot: Bot, dal: DataAccessLayer, **kwargs
) -> None:
    file_id = message.document.file_id
    file: File = await bot.get_file(file_id=file_id)

    if file.file_size >= 10 * 1024 * 1024:
        await message.answer(
            text="File too big. Try again with filesize lower then 10 mb.",
            parse_mode=SULGUK_PARSE_MODE,
        )
        return

    user_schema = await dal.get_user_by_attr(**{"user_id": message.from_user.id})
    if user_schema:
        _: BinaryIO = await bot.download_file(file.file_path)
        channels: list[ChannelCreateDTO] = []
        with TextIOWrapper(_, encoding="utf-8") as text_io:
            for line in text_io:
                line = line.strip()
                splitted_line = line.split("\t")
                if len(splitted_line) != 2:
                    await message.answer(
                        text=f"Malformed line {line[0:255]}. ",
                        parse_mode=SULGUK_PARSE_MODE,
                    )
                    return

                if not youtube_channel_url_validator(splitted_line[0]):
                    await message.answer(
                        text=f"Error url validation: {splitted_line[0]} <br/>"
                             "Set channel url in format: <b>https://www.youtube.com/@username</b>",
                        parse_mode=SULGUK_PARSE_MODE,
                    )
                    return

                channel = ChannelCreateDTO(
                    url=splitted_line[0],
                    label=splitted_line[1],
                    enabled=True,
                    user_id=user_schema.id,
                )
                channels.append(channel)

        for channel in channels:
            result: Optional[ChannelRetrieveDTO] = await dal.create_channel(
                channel_schema=channel
            )
            await message.answer(f"{str(result)}")

    await state.clear()


@add_channels_router.message(
    Command("list_channels", "каналы"),
    State(state="*"),
)
async def list_channels(message: Message, dal: DataAccessLayer, bot: Bot, **kwargs) -> None:
    user_id = message.from_user.id
    current_time = datetime.now()

    # Check if the user is a superuser
    user_schema = await dal.get_user_by_attr(**{"user_id": user_id})
    if user_schema and user_schema.is_superuser:
        # Superusers are not subject to rate limiting
        await send_channel_list(message, dal, bot)
        return

    # Check if the user has called the command within the last 30 minutes
    if user_id in last_command_time:
        last_time = last_command_time[user_id]
        if current_time - last_time < timedelta(minutes=1):
            await bot.send_message(
                chat_id=user_id,
                text="Частота запросов 1 раз в минуту."
            )
            return

    # Update the last command time for the user
    last_command_time[user_id] = current_time

    await send_channel_list(message, dal, bot)

async def send_channel_list(message: Message, dal: DataAccessLayer, bot: Bot) -> None:
    channels = await dal.get_channels()
    if not channels:
        await message.answer("Каналы не найдены.")
        return

    response = "Список отслеживаемых каналов:\n"
    for channel in channels:
        response += f"{channel.label}: {channel.url}\n"

    await bot.send_message(chat_id=message.from_user.id, text=response)

__all__ = ["add_channels_router"]
