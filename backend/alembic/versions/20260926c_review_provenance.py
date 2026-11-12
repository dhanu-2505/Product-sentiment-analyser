"""Add explicit review provenance and product source relationship

Revision ID: 20260926c
Revises: 20260926b
Create Date: 2026-09-26 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260926c"
down_revision = "20260926b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    review_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("reviews")}
    if "source_id" not in review_columns:
        with op.batch_alter_table("reviews") as batch_op:
            batch_op.add_column(sa.Column("source_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_reviews_source_id_product_sources",
                "product_sources",
                ["source_id"],
                ["id"],
            )

    if "data_type" not in review_columns:
        with op.batch_alter_table("reviews") as batch_op:
            batch_op.add_column(
                sa.Column("data_type", sa.String(length=20), nullable=False, server_default="seeded_demo")
            )
        op.execute(
            "UPDATE reviews SET data_type = CASE WHEN is_demo THEN 'seeded_demo' ELSE 'live_scraped' END"
        )
        with op.batch_alter_table("reviews") as batch_op:
            batch_op.alter_column("data_type", existing_type=sa.String(length=20), server_default=None)

    indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("reviews")}
    for index_name, column_name in (("ix_reviews_source_id", "source_id"), ("ix_reviews_data_type", "data_type")):
        if index_name not in indexes:
            op.create_index(index_name, "reviews", [column_name], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_index("ix_reviews_data_type")
        batch_op.drop_index("ix_reviews_source_id")
        batch_op.drop_column("data_type")
        batch_op.drop_constraint("fk_reviews_source_id_product_sources", type_="foreignkey")
        batch_op.drop_column("source_id")
