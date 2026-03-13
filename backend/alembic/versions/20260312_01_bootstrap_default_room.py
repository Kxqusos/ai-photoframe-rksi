"""bootstrap default room after schema migrations"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260312_01_bootstrap_default_room"
down_revision = "20260224_01_rooms_pg17"
branch_labels = None
depends_on = None

DEFAULT_ROOM_ID = 1
DEFAULT_ROOM_SLUG = "ph000000"
DEFAULT_ROOM_NAME = "Main"
DEFAULT_ROOM_MODEL = "openai/gpt-5-image"


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "sqlite":
        bind.execute(
            sa.text(
                """
                INSERT OR IGNORE INTO rooms (id, slug, name, model_name, is_active)
                VALUES (:id, :slug, :name, :model_name, :is_active)
                """
            ),
            {
                "id": DEFAULT_ROOM_ID,
                "slug": DEFAULT_ROOM_SLUG,
                "name": DEFAULT_ROOM_NAME,
                "model_name": DEFAULT_ROOM_MODEL,
                "is_active": 1,
            },
        )
        return

    bind.execute(
        sa.text(
            """
            INSERT INTO rooms (id, slug, name, model_name, is_active)
            VALUES (:id, :slug, :name, :model_name, :is_active)
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {
            "id": DEFAULT_ROOM_ID,
            "slug": DEFAULT_ROOM_SLUG,
            "name": DEFAULT_ROOM_NAME,
            "model_name": DEFAULT_ROOM_MODEL,
            "is_active": True,
        },
    )


def downgrade() -> None:
    # The down-revision already expects the default room to exist, so downgrading
    # this idempotent bootstrap step must not remove it.
    return None
