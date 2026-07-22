import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud_chat import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation,
    list_conversations,
    list_messages,
)
from app.db.crud_papers import get_paper
from app.db.models import MessageRole, PaperStatus
from app.db.session import get_db
from app.schemas.chat import (
    ConversationOut,
    CreateConversationIn,
    CreateMessageIn,
    CreateMessageOut,
    MessageOut,
)
from app.services.chat_runner import spawn_chat_run
from app.services.events import stream as event_stream

router = APIRouter(tags=["conversations"])


@router.post("/api/papers/{paper_id}/conversations", response_model=ConversationOut)
async def create_conversation_route(
    paper_id: uuid.UUID, body: CreateConversationIn, db: AsyncSession = Depends(get_db)
) -> ConversationOut:
    paper = await get_paper(db, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    conversation = await create_conversation(db, paper_id=paper_id, title=body.title)
    return ConversationOut.model_validate(conversation)


@router.get("/api/papers/{paper_id}/conversations", response_model=list[ConversationOut])
async def list_conversations_route(
    paper_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[ConversationOut]:
    conversations = await list_conversations(db, paper_id)
    return [ConversationOut.model_validate(c) for c in conversations]


@router.get("/api/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation_route(
    conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ConversationOut:
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut.model_validate(conversation)


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation_route(
    conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    deleted = await delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}


@router.get("/api/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages_route(
    conversation_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[MessageOut]:
    messages = await list_messages(db, conversation_id)
    return [MessageOut.model_validate(m) for m in messages]


@router.post("/api/conversations/{conversation_id}/messages", response_model=CreateMessageOut)
async def post_message_route(
    conversation_id: uuid.UUID, body: CreateMessageIn, db: AsyncSession = Depends(get_db)
) -> CreateMessageOut:
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    paper = await get_paper(db, conversation.paper_id)
    if paper is None or paper.status != PaperStatus.READY:
        raise HTTPException(status_code=400, detail="Paper is not ready for chat yet")

    user_message = await add_message(
        db, conversation_id=conversation_id, role=MessageRole.USER, content=body.content
    )

    run_id = str(uuid.uuid4())
    spawn_chat_run(
        conversation_id=conversation_id,
        paper_id=conversation.paper_id,
        user_query=body.content,
        run_id=run_id,
    )

    return CreateMessageOut(message_id=user_message.id, run_id=run_id)


@router.get("/api/conversations/{conversation_id}/messages/{run_id}/stream")
async def stream_chat_run(conversation_id: uuid.UUID, run_id: str) -> StreamingResponse:
    async def gen():
        async for event in event_stream(run_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
