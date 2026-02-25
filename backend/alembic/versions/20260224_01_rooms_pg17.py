"""add rooms schema and room_id fks for prompts/jobs"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260224_01_rooms_pg17"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_ROOM_SLUG = "main"
DEFAULT_ROOM_NAME = "Main"
DEFAULT_ROOM_MODEL = "openai/gpt-5-image"


def _default_room_id(bind) -> int:
    room_id = bind.execute(sa.text("SELECT id FROM rooms WHERE slug = :slug"), {"slug": DEFAULT_ROOM_SLUG}).scalar()
    if room_id is None:
        raise RuntimeError("default room was not created")
    return int(room_id)


def _ensure_room_fk(table_name: str, fk_name: str, index_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if "room_id" not in columns:
        op.add_column(table_name, sa.Column("room_id", sa.Integer(), nullable=True))

    room_id = _default_room_id(bind)
    bind.execute(
        sa.text(f"UPDATE {table_name} SET room_id = :room_id WHERE room_id IS NULL"),
        {"room_id": room_id},
    )

    inspector = sa.inspect(bind)
    foreign_keys = inspector.get_foreign_keys(table_name)
    has_room_fk = any(
        foreign_key.get("referred_table") == "rooms" and foreign_key.get("constrained_columns") == ["room_id"]
        for foreign_key in foreign_keys
    )
    if not has_room_fk:
        op.create_foreign_key(fk_name, table_name, "rooms", ["room_id"], ["id"])

    op.alter_column(table_name, "room_id", existing_type=sa.Integer(), nullable=False)
    bind.execute(sa.text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (room_id)"))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "rooms" not in tables:
        op.create_table(
            "rooms",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("slug", sa.String(length=120), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("model_name", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )

    bind.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_rooms_slug ON rooms (slug)"))
    bind.execute(
        sa.text(
            """
            INSERT INTO rooms (slug, name, model_name, is_active)
            VALUES (:slug, :name, :model_name, :is_active)
            ON CONFLICT (slug) DO NOTHING
            """
        ),
        {
            "slug": DEFAULT_ROOM_SLUG,
            "name": DEFAULT_ROOM_NAME,
            "model_name": DEFAULT_ROOM_MODEL,
            "is_active": True,
        },
    )

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "prompts" not in tables:
        op.create_table(
            "prompts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.String(length=500), nullable=False),
            sa.Column("prompt", sa.Text(), nullable=False),
            sa.Column("preview_image_url", sa.String(length=500), nullable=False),
            sa.Column("icon_image_url", sa.String(length=500), nullable=False),
            sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
        )
        bind.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_prompts_room_id ON prompts (room_id)"))
    else:
        _ensure_room_fk("prompts", "fk_prompts_room_id_rooms", "ix_prompts_room_id")

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "generation_jobs" not in tables:
        op.create_table(
            "generation_jobs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("prompt_id", sa.Integer(), sa.ForeignKey("prompts.id"), nullable=False),
            sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id"), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("qr_hash", sa.String(length=64), nullable=True, unique=True),
            sa.Column("source_path", sa.String(length=500), nullable=True),
            sa.Column("result_path", sa.String(length=500), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
        )
        bind.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_generation_jobs_room_id ON generation_jobs (room_id)"))
    else:
        _ensure_room_fk("generation_jobs", "fk_generation_jobs_room_id_rooms", "ix_generation_jobs_room_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "generation_jobs" in tables:
        bind.execute(sa.text("DROP INDEX IF EXISTS ix_generation_jobs_room_id"))
        foreign_keys = inspector.get_foreign_keys("generation_jobs")
        if any(foreign_key.get("name") == "fk_generation_jobs_room_id_rooms" for foreign_key in foreign_keys):
            op.drop_constraint("fk_generation_jobs_room_id_rooms", "generation_jobs", type_="foreignkey")
        columns = {column["name"] for column in inspector.get_columns("generation_jobs")}
        if "room_id" in columns:
            op.drop_column("generation_jobs", "room_id")

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "prompts" in tables:
        bind.execute(sa.text("DROP INDEX IF EXISTS ix_prompts_room_id"))
        foreign_keys = inspector.get_foreign_keys("prompts")
        if any(foreign_key.get("name") == "fk_prompts_room_id_rooms" for foreign_key in foreign_keys):
            op.drop_constraint("fk_prompts_room_id_rooms", "prompts", type_="foreignkey")
        columns = {column["name"] for column in inspector.get_columns("prompts")}
        if "room_id" in columns:
            op.drop_column("prompts", "room_id")

    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "rooms" in tables:
        bind.execute(sa.text("DROP INDEX IF EXISTS ix_rooms_slug"))
        op.drop_table("rooms")
