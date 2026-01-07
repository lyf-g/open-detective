"""Initial schema

Revision ID: 71e25aec6397
Revises: 
Create Date: 2026-01-07 11:21:58.472545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71e25aec6397'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'open_digger_metrics',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('repo_name', sa.String(255), nullable=False),
        sa.Column('metric_type', sa.String(64), nullable=False),
        sa.Column('month', sa.String(7), nullable=False),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now())
    )
    op.create_index('idx_repo_metric', 'open_digger_metrics', ['repo_name', 'metric_type'])

    op.create_table(
        'sessions',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now())
    )

    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(36), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('evidence_sql', sa.Text(), nullable=True),
        sa.Column('evidence_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], )
    )


def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('open_digger_metrics')