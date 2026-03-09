from typing import Annotated, Sequence

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse

from .dependecies import get_bbchat_service
from .models import Message, MessageCreate, Session, SessionCreate, SessionWithMessages
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


@router.post("/sessions", response_model=SessionWithMessages)
async def create_session(
    props: SessionCreate,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    return 201, await service.create_session(props)


@router.get("/sessions", response_model=Sequence[Session])
async def get_sessions(
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    return await service.get_all_sessions()


@router.get("/sessions/{id}", response_model=SessionWithMessages)
async def fetch_session(
    id: int, service: Annotated[BancoBotService, Depends(get_bbchat_service)]
):
    """Fetch a session by its id"""
    return await service.fetch_session(id)


@router.delete("/sessions/{id}", response_model=None)
async def delete_session(
    id: int,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Delete a session by its id"""
    return 204, await service.delete_session(id)


@router.post("/messages", response_model=Message, status_code=201)
async def create_message(
    props: MessageCreate,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Creates a new message to the chatbot. Receives an optional session id to continue a previous session dialogue."""
    try:
        return await service.create_message(props)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{id}/messages", response_model=Sequence[Message])
async def fetch_messages(
    id: int,
    service: Annotated[BancoBotService, Depends(get_bbchat_service)],
):
    """Fetches all messages from the chatbot."""
    return await service.get_messages_by_session(id)


@router.get("/sessions/messages/stream")
async def stream(
    request: Request, service: Annotated[BancoBotService, Depends(get_bbchat_service)]
):
    """Stream new created messages on the system as Server Side Event."""
    return EventSourceResponse(
        service.subscribe_and_yield(request),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
