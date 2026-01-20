from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4

from .dependecies import get_bbchat_service
from .models import MessageCreate, MessagePublic
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


@router.get("/sessions", response_model=Sequence[UUID4])
async def get_sessions(
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    try:
        return await service.get_all_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{id}", response_model=Sequence[MessagePublic])
async def fetch_session(
    id: UUID4, service: Annotated[BancoBotService, Depends(get_bbchat_service)]
):
    """Fetch a session by its id"""
    try:
        return await service.get_message_by_session(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{id}", response_model=None)
async def delete_session(
    id: UUID4,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Delete a session by its id"""
    try:
        return 204, await service.delete_messages_by_session(id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages", response_model=MessagePublic, status_code=201)
async def create_message(
    props: MessageCreate,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Creates a new message to the chatbot. Receives an optional session id to continue a previous session dialogue."""
    try:
        return await service.create_message(props)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
