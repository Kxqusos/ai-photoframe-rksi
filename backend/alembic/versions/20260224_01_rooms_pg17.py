"""add rooms schema and room_id fks for prompts/jobs"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from photoframe_backend.shared.public_ids import generate_public_id, is_public_id

revision = "20260224_01_rooms_pg17"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_ROOM_ID = 1
DEFAULT_ROOM_SLUG = "ph000000"
DEFAULT_ROOM_NAME = "Main"
DEFAULT_ROOM_MODEL = "openai/gpt-5-image"


def _default_room_id(bind) -> int:
    room_id = bind.execute(sa.text("SELECT id FROM rooms WHERE slug = :slug"), {"slug": DEFAULT_ROOM_SLUG}).scalar()
    if room_id is None:
        raise RuntimeError("default room was not created")
    return int(room_id)


def _ensure_default_room(bind) -> None:
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


def _generate_unique_room_slug(used_slugs: set[str]) -> str:
    while True:
        candidate = generate_public_id()
        if candidate not in used_slugs:
            return candidate


def _migrate_room_slugs(bind) -> None:
    rows = bind.execute(sa.text("SELECT id, slug FROM rooms ORDER BY id ASC")).fetchall()
    if not rows:
        return

    used_slugs: set[str] = set()
    for row in rows:
        slug = str(row[1] or "").strip().lower()
        if is_public_id(slug):
            used_slugs.add(slug)

    for row in rows:
        room_id = int(row[0])
        current_slug = str(row[1] or "")
        normalized = current_slug.strip().lower()

        if is_public_id(normalized):
            if normalized != current_slug:
                bind.execute(sa.text("UPDATE rooms SET slug = :slug WHERE id = :id"), {"slug": normalized, "id": room_id})
            continue

        if DEFAULT_ROOM_SLUG not in used_slugs and (room_id == DEFAULT_ROOM_ID or normalized == "main"):
            new_slug = DEFAULT_ROOM_SLUG
        else:
            new_slug = _generate_unique_room_slug(used_slugs)

        bind.execute(sa.text("UPDATE rooms SET slug = :slug WHERE id = :id"), {"slug": new_slug, "id": room_id})
        used_slugs.add(new_slug)


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


def _ensure_generation_jobs_qr_hash() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "generation_jobs" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("generation_jobs")}
    if "qr_hash" not in columns:
        op.add_column("generation_jobs", sa.Column("qr_hash", sa.String(length=64), nullable=True))

    bind.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_generation_jobs_qr_hash ON generation_jobs (qr_hash)"))


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
    _ensure_default_room(bind)
    _migrate_room_slugs(bind)

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

    _ensure_generation_jobs_qr_hash()


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
