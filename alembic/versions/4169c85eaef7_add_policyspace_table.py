"""Add PolicySpace table

Revision ID: 4169c85eaef7
Revises: 462297b9f626
Create Date: 2025-08-27 21:31:18.165975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4169c85eaef7'
down_revision: Union[str, Sequence[str], None] = '462297b9f626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create policy_spaces table
    op.create_table('policy_spaces',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policy_spaces_id'), 'policy_spaces', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop policy_spaces table
    op.drop_index(op.f('ix_policy_spaces_id'), table_name='policy_spaces')
    op.drop_table('policy_spaces')
