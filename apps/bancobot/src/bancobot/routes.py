from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException

from .dependecies import get_bbchat_service
from .models import (
    ConversationCreate,
    ConversationPublic,
    ConversationPublicWithMessages,
    MessageCreate,
    MessagePublic,
)
from .services import BancoBotService

### Routes
router = APIRouter()


@router.get("/")
async def root():
    """Root of BancoBotAPI."""
    return {
        "detail": "Root of BancoBotAPI. Check /docs endpoint for available endpoints."
    }


@router.get("/health")
async def health():
    """Healthchecker of the API. Returns its current status"""
    return {"detail": "API is on air."}


@router.post("/sessions", response_model=ConversationPublic, status_code=201)
async def create_session(
    props: ConversationCreate,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Create a new session. Possibly from a parent session to fork a dialogue"""
    return await service.create_session(props)


@router.get("/sessions", response_model=Sequence[ConversationPublic])
async def get_sessions(
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Retrieve all sessions entries."""
    return await service.get_all_sessions()


@router.get("/sessions/{id}", response_model=ConversationPublicWithMessages)
async def fetch_session(
    id: int, service: Annotated[BancoBotService, Depends(get_bbchat_service)]
):
    """Fetch a session by its id"""
    return await service.fetch_session(id)


@router.delete("/sessions/{id}", response_model=None, status_code=204)
async def delete_session(
    id: int,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Delete a session by its id"""
    return await service.delete_session(id)


@router.post("/messages", response_model=MessagePublic, status_code=201)
async def create_message(
    props: MessageCreate,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Creates a new message to the chatbot. Receives session id to continue a previous session dialogue."""
    try:
        return await service.save_publish_answer_message(props)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{id}/messages", response_model=Sequence[MessagePublic])
async def fetch_messages(
    id: int,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Fetches all messages from the chatbot."""
    return await service.get_messages_by_conversation(id)
