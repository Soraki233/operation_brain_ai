"""create chat_threads / chat_messages tables

Revision ID: a7c12e4b91f5
Revises: 6f32e85c528a
Create Date: 2026-04-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7c12e4b91f5'
down_revision: Union[str, Sequence[str], None] = '6f32e85c528a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'chat_threads',
        sa.Column('user_id', sa.String(length=100), nullable=False, comment='归属用户ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='线程标题'),
        sa.Column('summary', sa.Text(), nullable=True, comment='历史摘要'),
        sa.Column('summary_version', sa.Integer(), nullable=False, server_default='0', comment='摘要版本'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0', comment='消息数'),
        sa.Column('last_message_at', sa.DateTime(), nullable=True, comment='最后消息时间'),
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.SmallInteger(), nullable=False, server_default='0', comment='是否删除(0: 正常, 1: 删除)'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_threads')),
    )
    op.create_index(op.f('ix_chat_threads_user_id'), 'chat_threads', ['user_id'], unique=False)

    op.create_table(
        'chat_messages',
        sa.Column('thread_id', sa.String(length=36), nullable=False, comment='线程ID'),
        sa.Column('parent_message_id', sa.String(length=36), nullable=True, comment='父消息ID'),
        sa.Column('sequence_no', sa.Integer(), nullable=False, comment='线程内顺序号'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='user/assistant/system'),
        sa.Column('content', sa.Text(), nullable=False, comment='消息内容'),
        sa.Column('tokens_estimate', sa.Integer(), nullable=False, server_default='0', comment='粗略token数'),
        sa.Column('meta_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}', comment='引用来源等'),
        sa.Column('is_summarized', sa.Integer(), nullable=False, server_default='0', comment='是否已汇总 0/1'),
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.Column('is_deleted', sa.SmallInteger(), nullable=False, server_default='0', comment='是否删除(0: 正常, 1: 删除)'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_chat_messages')),
    )
    op.create_index(op.f('ix_chat_messages_thread_id'), 'chat_messages', ['thread_id'], unique=False)
    op.create_index(op.f('ix_chat_messages_sequence_no'), 'chat_messages', ['sequence_no'], unique=False)
    op.create_index(op.f('ix_chat_messages_parent_message_id'), 'chat_messages', ['parent_message_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_chat_messages_parent_message_id'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_sequence_no'), table_name='chat_messages')
    op.drop_index(op.f('ix_chat_messages_thread_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index(op.f('ix_chat_threads_user_id'), table_name='chat_threads')
    op.drop_table('chat_threads')
