import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Conversation, Message, MessageRole


async def create_conversation(
    db: AsyncSession, *, paper_id: uuid.UUID, title: str, agent_key: str
) -> Conversation:
    conversation = Conversation(paper_id=paper_id, title=title, agent_key=agent_key)
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_conversation_by_agent(
    db: AsyncSession, paper_id: uuid.UUID, agent_key: str
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.paper_id == paper_id, Conversation.agent_key == agent_key
        )
    )
    return result.scalar_one_or_none()


async def list_conversations(db: AsyncSession, paper_id: uuid.UUID) -> list[Conversation]:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.paper_id == paper_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> Conversation | None:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return result.scalar_one_or_none()


async def delete_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> bool:
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        return False
    await db.delete(conversation)
    await db.commit()
    return True


async def add_message(
    db: AsyncSession,
    *,
    conversation_id: uuid.UUID,
    role: MessageRole,
    content: str,
    agent_used: list[str] | None = None,
    citations: list[dict] | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        agent_used=agent_used,
        citations=citations,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def list_messages(db: AsyncSession, conversation_id: uuid.UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def recent_history(db: AsyncSession, conversation_id: uuid.UUID, limit: int = 10) -> list[dict]:
    messages = await list_messages(db, conversation_id)
    tail = messages[-limit:]
    return [{"role": m.role.value, "content": m.content} for m in tail]
