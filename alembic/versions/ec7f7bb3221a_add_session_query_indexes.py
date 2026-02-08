"""add_session_query_indexes

Revision ID: ec7f7bb3221a
Revises: 9403029f294b
Create Date: 2026-02-08 13:03:25.411401

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec7f7bb3221a'
down_revision: Union[str, Sequence[str], None] = '9403029f294b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        'ix_chat_sessions_user_status_messages',
        'chat_sessions',
        ['user_id', 'status', 'message_count'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chat_sessions_user_status_messages', table_name='chat_sessions')
