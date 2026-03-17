"""add room password hash for public room access"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260316_01_room_password_access"
down_revision = "20260312_01_room_bootstrap"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rooms",
        sa.Column("room_password_hash", sa.String(length=255), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("rooms", "room_password_hash")
