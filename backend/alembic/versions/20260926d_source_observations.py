"""Add source provenance and historical observations

Revision ID: 20260926d
Revises: 20260926c
Create Date: 2026-09-26 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260926d"
down_revision = "20260926c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    source_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("product_sources")}
    if "data_type" not in source_columns:
        with op.batch_alter_table("product_sources") as batch_op:
            batch_op.add_column(sa.Column("data_type", sa.String(length=20), nullable=True))
        op.execute("UPDATE product_sources SET data_type = 'stored' WHERE data_type IS NULL")
        with op.batch_alter_table("product_sources") as batch_op:
            batch_op.alter_column("data_type", existing_type=sa.String(length=20), nullable=False)

    constraints = {constraint["name"] for constraint in sa.inspect(op.get_bind()).get_unique_constraints("product_sources")}
    if "uq_product_sources_product_source" not in constraints:
        with op.batch_alter_table("product_sources") as batch_op:
            batch_op.create_unique_constraint("uq_product_sources_product_source", ["product_id", "source_name"])

    if "source_observations" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "source_observations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("product_source_id", sa.Integer(), nullable=False),
            sa.Column("price", sa.Numeric(12, 2), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=True),
            sa.Column("rating", sa.Float(), nullable=True),
            sa.Column("review_count", sa.Integer(), nullable=True),
            sa.Column("availability", sa.Boolean(), nullable=True),
            sa.Column("data_type", sa.String(length=20), nullable=False),
            sa.Column("observed_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["product_source_id"], ["product_sources.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_source_observations_id", "source_observations", ["id"], unique=False)
        op.create_index("ix_source_observations_product_source_id", "source_observations", ["product_source_id"], unique=False)
        op.create_index("ix_source_observations_observed_at", "source_observations", ["observed_at"], unique=False)


def downgrade() -> None:
    op.drop_table("source_observations")
    with op.batch_alter_table("product_sources") as batch_op:
        batch_op.drop_constraint("uq_product_sources_product_source", type_="unique")
        batch_op.drop_column("data_type")
