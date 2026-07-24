"""Add email/provider fields to users

Revision ID: a1b2c3d4e5f6
Revises: 3e916e573889
Create Date: 2026-07-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "3e916e573889"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("provider", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("provider_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("avatar_url", sa.String(), nullable=True))
        batch_op.create_index("ix_users_email", ["email"], unique=False)
        batch_op.create_index("ix_users_provider", ["provider"], unique=False)
        batch_op.create_index("ix_users_provider_id", ["provider_id"], unique=False)
        batch_op.create_unique_constraint("uix_provider_id", ["provider", "provider_id"])


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uix_provider_id", type_="unique")
        batch_op.drop_index("ix_users_provider_id")
        batch_op.drop_index("ix_users_provider")
        batch_op.drop_index("ix_users_email")
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("provider_id")
        batch_op.drop_column("provider")
        batch_op.drop_column("email")
