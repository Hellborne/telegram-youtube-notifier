from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import State
from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog import StartMode

from ....db import DataAccessLayer
from ...filters import RoleFilter
from ...filters import UserRole
from ...states import ChannelDialogSG

scroll_channel_router = Router(name="scroll_channel")


@scroll_channel_router.message(
    Command("channels"),
    RoleFilter(role=[UserRole.ADMIN, UserRole.SUPERUSER]),
    State(state="*"),
)
async def start_channels_dialog(
    message: Message, dialog_manager: DialogManager, dal: DataAccessLayer, **kwargs
):
    await dialog_manager.start(
        ChannelDialogSG.scrolling, mode=StartMode.RESET_STACK, data={"dal": dal}
    )


__all__ = ["scroll_channel_router"]
