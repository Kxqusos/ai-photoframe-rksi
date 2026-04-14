"""extend llm routing settings with provider credentials

Revision ID: 20260414_01_llm_route_providers
Revises: 20260317_01_routing_setting
Create Date: 2026-04-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260414_01_llm_route_providers"
down_revision: str | None = "20260317_01_routing_setting"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "llm_routing_settings",
        sa.Column("provider_base_url", sa.Text(), nullable=False, server_default="https://openrouter.ai/api/v1"),
    )
    op.add_column(
        "llm_routing_settings",
        sa.Column("provider_api_key", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "llm_routing_settings",
        sa.Column("custom_providers_json", sa.Text(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("llm_routing_settings", "custom_providers_json")
    op.drop_column("llm_routing_settings", "provider_api_key")
    op.drop_column("llm_routing_settings", "provider_base_url")
