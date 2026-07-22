"""add agent_key to conversations

Revision ID: 7b3f95bee7b8
Revises: c6aec4d2fea6
Create Date: 2026-07-22 16:01:58.650652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b3f95bee7b8'
down_revision: Union[str, None] = 'c6aec4d2fea6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Conversations are now pinned 1:1 to an agent tab. Existing conversations
    # predate that model (dev/test data only) — clear them before adding the
    # NOT NULL column rather than trying to backfill a meaningless value.
    op.execute("DELETE FROM messages")
    op.execute("DELETE FROM conversations")

    op.add_column("conversations", sa.Column("agent_key", sa.String(), nullable=False))
    op.create_unique_constraint(
        "uq_conversation_paper_agent", "conversations", ["paper_id", "agent_key"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_conversation_paper_agent", "conversations", type_="unique")
    op.drop_column("conversations", "agent_key")
