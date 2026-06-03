"""add_periodo_to_avaliacao_gestao

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-03 00:00:00.000000

"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('avaliacao_gestao_submissions',
        sa.Column('periodo', sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column('avaliacao_gestao_submissions', 'periodo')
