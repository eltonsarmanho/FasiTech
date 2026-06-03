"""add_fasitech_questions_to_avaliacao_gestao

Revision ID: a1b2c3d4e5f6
Revises: d0deefb647a4
Create Date: 2026-06-03 00:00:00.000000

"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd0deefb647a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('avaliacao_gestao_submissions',
        sa.Column('q12_fasitech_impacto', sa.String(length=100), nullable=True))
    op.add_column('avaliacao_gestao_submissions',
        sa.Column('q12_valor', sa.Integer(), nullable=True))
    op.add_column('avaliacao_gestao_submissions',
        sa.Column('q13_fasitech_funcionalidades', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('avaliacao_gestao_submissions', 'q13_fasitech_funcionalidades')
    op.drop_column('avaliacao_gestao_submissions', 'q12_valor')
    op.drop_column('avaliacao_gestao_submissions', 'q12_fasitech_impacto')
