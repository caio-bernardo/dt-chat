import json
import uuid

import pytest
from chatbot import HumanMessage
from fastapi import HTTPException

from bancobot.models import MessageCreate, MessageType


@pytest.mark.asyncio
async def test_create_session(bancobot_service, conversation_create_data):
    """Test creating a new conversation session."""
    result = await bancobot_service.create_session(conversation_create_data)

    assert result.id is not None
    assert result.meta == conversation_create_data.meta
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_get_all_sessions(bancobot_service, conversation_create_data):
    """Test retrieving all sessions."""
    # Create multiple sessions
    await bancobot_service.create_session(conversation_create_data)
    await bancobot_service.create_session(conversation_create_data)

    sessions = await bancobot_service.get_all_sessions()

    assert len(sessions) >= 2
    assert all(s.id is not None for s in sessions)


@pytest.mark.asyncio
async def test_fetch_session(bancobot_service, conversation):
    """Test fetching a specific session by ID."""
    result = await bancobot_service.fetch_session(conversation.id)

    assert result.id == conversation.id
    assert result.meta == conversation.meta


@pytest.mark.asyncio
async def test_fetch_session_not_found(bancobot_service):
    """Test fetching a non-existent session."""
    fake_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await bancobot_service.fetch_session(fake_id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_session(bancobot_service, conversation):
    """Test deleting a session."""
    await bancobot_service.delete_session(conversation.id)

    with pytest.raises(HTTPException) as exc_info:
        await bancobot_service.fetch_session(conversation.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_not_found(bancobot_service):
    """Test deleting a non-existent session."""
    fake_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await bancobot_service.delete_session(fake_id)

    assert exc_info.value.status_code == 404


def test_save_message(bancobot_service, message_create_data):
    """Test saving a message to storage."""
    result = bancobot_service.save_message(
        message_create_data, message_create_data.timing_metadata
    )

    assert result.id is not None
    assert result.content == message_create_data.content
    assert result.type == MessageType.Human
    assert result.timing_metadata == message_create_data.timing_metadata


@pytest.mark.asyncio
async def test_save_and_publish_message(bancobot_service, message_create_data):
    """Test saving and publishing a message."""
    result = await bancobot_service.save_and_publish_message(
        message_create_data, message_create_data.timing_metadata
    )

    assert result.id is not None
    assert result.content == message_create_data.content
    bancobot_service.producer.publish.assert_called_once()


@pytest.mark.asyncio
async def test_publish_message(bancobot_service, conversation):
    """Test publishing a message to the channel."""
    from bancobot.models import Message

    message = Message(
        conversation_id=conversation.id,
        content="Test message",
        type=MessageType.Human,
        timing_metadata={},  # pyright: ignore[reportArgumentType]
    )
    bancobot_service.storage.add(message)
    bancobot_service.storage.commit()

    await bancobot_service.publish(message)

    bancobot_service.producer.publish.assert_called_once()
    call_args = bancobot_service.producer.publish.call_args
    assert call_args[0][0] == bancobot_service.channel

    # Verify the payload structure
    payload = json.loads(call_args[0][1])
    assert payload["origin"] == "real_bancobot"
    assert "content" in payload


@pytest.mark.asyncio
async def test_get_messages_by_conversation(
    bancobot_service, conversation, message_create_data
):
    """Test retrieving messages for a conversation."""
    # Create a few messages
    bancobot_service.save_message(
        message_create_data, message_create_data.timing_metadata
    )
    bancobot_service.save_message(
        message_create_data, message_create_data.timing_metadata
    )

    messages = await bancobot_service.get_messages_by_conversation(conversation.id)

    assert len(messages) >= 2
    assert all(m.conversation_id == conversation.id for m in messages)


@pytest.mark.asyncio
async def test_get_recent_messages(bancobot_service, conversation, message_create_data):
    """Test retrieving recent messages with limit."""
    # Create several messages
    for _ in range(5):
        bancobot_service.save_message(
            message_create_data, message_create_data.timing_metadata
        )

    messages = await bancobot_service.get_recent_messages(conversation.id, limit=3)

    assert len(messages) <= 3


@pytest.mark.asyncio
async def test_delete_message_by_id(bancobot_service, message_create_data):
    """Test deleting a specific message."""
    message = bancobot_service.save_message(
        message_create_data, message_create_data.timing_metadata
    )
    message_id = message.id

    result = await bancobot_service.delete_message_by_id(message_id)

    assert result is True


def test_answer_message(bancobot_service, conversation, timing_metadata):
    """Test answering a message using the agent."""
    bancobot_service.agent.process_message.return_value = HumanMessage(
        content="Bot response"
    )

    answer, answer_metadata = bancobot_service.answer_message(
        conversation.id, "Hello!", timing_metadata
    )

    assert answer.content == "Bot response"
    assert "simulated_timestamp" in answer_metadata
    bancobot_service.agent.process_message.assert_called_once()


@pytest.mark.asyncio
async def test_save_publish_answer_message(
    bancobot_service, conversation, timing_metadata
):
    """Test the full flow: save user message, get AI answer, save and publish it."""
    bancobot_service.agent.process_message.return_value = HumanMessage(
        content="Bot response"
    )

    props = MessageCreate(
        conversation_id=conversation.id,
        content="User message",
        type=MessageType.Human,
        timing_metadata=timing_metadata,
    )

    result = await bancobot_service.save_publish_answer_message(props)

    assert result.type == MessageType.AI
    assert result.content == "Bot response"
    assert bancobot_service.producer.publish.called
