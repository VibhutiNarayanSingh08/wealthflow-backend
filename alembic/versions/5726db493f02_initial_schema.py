"""Initial schema

Revision ID: 5726db493f02
Revises: 
Create Date: 2026-05-03 15:17:53.807988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5726db493f02'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.Text(), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('name', sa.Text()),
        sa.Column('created_at', sa.Text(), server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    
    op.create_table(
        'investments',
        sa.Column('id', sa.REAL(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('type', sa.Text(), nullable=False),
        sa.Column('invested', sa.REAL(), nullable=False),
        sa.Column('current_value', sa.REAL(), nullable=False),
        sa.Column('date', sa.Text(), nullable=False),
        sa.Column('note', sa.Text()),
        sa.Column('created_at', sa.Text(), server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    
    op.create_table(
        'expenses',
        sa.Column('id', sa.REAL(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('amount', sa.REAL(), nullable=False),
        sa.Column('date', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('payment_method', sa.Text(), server_default='upi'),
        sa.Column('note', sa.Text()),
        sa.Column('created_at', sa.Text(), server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    
    op.create_table(
        'budgets',
        sa.Column('id', sa.REAL(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('limit_amount', sa.REAL(), nullable=False),
        sa.Column('created_at', sa.Text(), server_default=sa.text("CURRENT_TIMESTAMP"))
    )
    
    op.create_table(
        'recurring_expenses',
        sa.Column('id', sa.REAL(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('amount', sa.REAL(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('frequency', sa.Text(), server_default='monthly'),
        sa.Column('day_of_month', sa.Integer(), server_default='1'),
        sa.Column('active', sa.Integer(), server_default='1'),
        sa.Column('last_paid', sa.Text()),
        sa.Column('created_at', sa.Text(), server_default=sa.text("CURRENT_TIMESTAMP"))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('recurring_expenses')
    op.drop_table('budgets')
    op.drop_table('expenses')
    op.drop_table('investments')
    op.drop_table('users')
