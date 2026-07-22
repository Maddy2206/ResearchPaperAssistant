import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.db.models import MessageRole

AgentKey = Literal[
    "research_analysis",
    "math_algorithm",
    "results_critique",
    "paper_to_code",
    "architecture_flowchart",
    "general_qa",
]

AGENT_LABELS: dict[AgentKey, str] = {
    "research_analysis": "Research Analysis",
    "math_algorithm": "Math & Algorithm",
    "results_critique": "Results & Critique",
    "paper_to_code": "Paper-to-Code",
    "architecture_flowchart": "Architecture & Flowchart",
    "general_qa": "General Q&A",
}


class Citation(BaseModel):
    index: int
    chunk_id: uuid.UUID
    page_number: int | None
    section_title: str | None
    content_type: str
    snippet: str


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    paper_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    agent_used: list[str] | None
    citations: list[Citation] | None
    created_at: datetime


class CreateConversationIn(BaseModel):
    title: str = "New conversation"


class CreateMessageIn(BaseModel):
    content: str


class CreateMessageOut(BaseModel):
    message_id: uuid.UUID
    run_id: str
