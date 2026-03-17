"""intake_session 채팅 컬럼 추가

Revision ID: a1b2c3d4e5f6
Revises: 80b3129e0173
Create Date: 2026-03-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "80b3129e0173"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "intake_session",
        sa.Column("intake_type", sa.String(10), nullable=False, server_default="FORM"),
    )
    op.add_column(
        "intake_session",
        sa.Column("chat_history", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("intake_session", "chat_history")
    op.drop_column("intake_session", "intake_type")
