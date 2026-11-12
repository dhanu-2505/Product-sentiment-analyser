"""Add product_sources, review_aspects, alerts, reports tables and search_history.product_id

Revision ID: 20260926b
Revises: 20260926
Create Date: 2026-09-26 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260926b"
down_revision = "20260926"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    auxiliary_tables = {"product_sources", "review_aspects", "alerts", "reports"}
    if auxiliary_tables.issubset(existing_tables):
        return

    op.create_table(
        "product_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("product_url", sa.String(length=500), nullable=True),
        sa.Column("source_product_id", sa.String(length=255), nullable=True),
        sa.Column("last_scraped_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_sources_id"), "product_sources", ["id"], unique=False)
    op.create_index(op.f("ix_product_sources_product_id"), "product_sources", ["product_id"], unique=False)

    op.create_table(
        "review_aspects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("aspect", sa.String(length=100), nullable=False),
        sa.Column("sentiment", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default="0.0"),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_aspects_id"), "review_aspects", ["id"], unique=False)
    op.create_index(op.f("ix_review_aspects_review_id"), "review_aspects", ["review_id"], unique=False)
    op.create_index(op.f("ix_review_aspects_aspect"), "review_aspects", ["aspect"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False, server_default="sentiment_change"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)
    op.create_index(op.f("ix_alerts_user_id"), "alerts", ["user_id"], unique=False)
    op.create_index(op.f("ix_alerts_product_id"), "alerts", ["product_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False, server_default="product_summary"),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("generated_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_id"), "reports", ["id"], unique=False)
    op.create_index(op.f("ix_reports_user_id"), "reports", ["user_id"], unique=False)
    op.create_index(op.f("ix_reports_product_id"), "reports", ["product_id"], unique=False)

    search_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("search_history")}
    if "product_id" not in search_columns:
        with op.batch_alter_table("search_history") as batch_op:
            batch_op.add_column(sa.Column("product_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_search_history_product_id_products",
                "products",
                ["product_id"],
                ["id"],
            )
    search_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("search_history")}
    if op.f("ix_search_history_product_id") not in search_indexes:
        op.create_index(op.f("ix_search_history_product_id"), "search_history", ["product_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("search_history") as batch_op:
        batch_op.drop_column("product_id")

    op.drop_table("reports")
    op.drop_table("alerts")
    op.drop_table("review_aspects")
    op.drop_table("product_sources")
