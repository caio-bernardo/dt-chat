import uuid

from bancobot.agent import BancoAgentBuilder
from classifier.models import Touchpoint
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session
from userbot import TimeSimulationConfig, UserBotBuilder

from fork_engine.helpers import (
    convert_conversation_to_langchain_types,
    retrieve_messages_until,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)


class ForkConfig(BaseModel):
    """Configuration of a Fork process. Allows to create a new conversation between a userbot and a bancobot, with specific values."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    parent_conversation: uuid.UUID
    branched_message_id: uuid.UUID
    bancobot_builder: BancoAgentBuilder
    userbot_builder: UserBotBuilder
    next_msg: str
    timesim: TimeSimulationConfig = TimeSimulationConfig()
    label: str = ""
    iterations: int = 15


def create_config(
    storage: Session, data: Touchpoint, bot: BancoAgentBuilder, label: str
) -> ForkConfig:
    """Creates a ForkConfig for the given data and bot, with the given label.
    Inserts previous messages of the conversation
    """
    meta = data.message.conversation.meta
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)

    previous_messages = convert_conversation_to_langchain_types(
        retrieve_messages_until(storage, data.message)
    )

    # This touchpoint is only produced by humans, so If the message is at the
    # begining (max position 2) then we are begin the conversation from the
    # start
    if len(previous_messages) < 4:
        next_msg = "Olá"
        userbot.initial_messages = []
    else:
        # Else reask the previous question
        next_msg = previous_messages[-3].content
        userbot.initial_messages = previous_messages[:-3]

    timesim = retrieve_timesim_from_metadata(meta)
    return ForkConfig(
        parent_conversation=data.message.conversation_id,
        bancobot_builder=bot,
        userbot_builder=userbot,
        branched_message_id=data.message.id,
        next_msg=str(next_msg),  # re-ask the message before the touchpoint
        timesim=timesim,
        label=label,
        iterations=15 - len(previous_messages),
    )
