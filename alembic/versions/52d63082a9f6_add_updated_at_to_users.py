"""Add updated_at to users

Revision ID: 52d63082a9f6
Revises: ec7f7bb3221a
Create Date: 2026-02-08 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '52d63082a9f6'
down_revision: Union[str, None] = 'ec7f7bb3221a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column to users table
    # We use server_default to populate existing rows, checking dialect support
    # For SQLite, adding a column with a default is supported in recent versions
    # But batch_alter_table is safer for SQLite
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Update existing rows to have current timestamp
    op.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")

    # Now make it non-nullable if desired, but for now we keep it nullable or rely on default
    # The model has a default factory, but let's make it consistent.
    # In SQLite, altering column nullability is complex, so let's stick with nullable=True initially
    # or just leave it. The model defines it as:
    # updated_at: datetime = Field(default_factory=utc_now, ...)
    # which implies it should be populated.
    
    # Create index
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_updated_at'), ['updated_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_updated_at'))
        batch_op.drop_column('updated_at')
