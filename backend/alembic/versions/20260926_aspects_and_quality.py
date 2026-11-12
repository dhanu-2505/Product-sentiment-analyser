"""Add aspects, sentiment metrics, quality score and verified purchase

Revision ID: 20260926
Revises: 20260925
Create Date: 2026-09-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260926"
down_revision = "20260925"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    review_columns = {column["name"] for column in inspector.get_columns("reviews")}
    if "verified_purchase" not in review_columns:
        with op.batch_alter_table("reviews") as batch_op:
            batch_op.add_column(sa.Column("verified_purchase", sa.Boolean(), server_default="1", nullable=False))

    sentiment_columns = {column["name"] for column in inspector.get_columns("sentiment_results")}
    sentiment_additions = {
        "polarity_score": sa.Column("polarity_score", sa.Float(), server_default="0.0", nullable=False),
        "subjectivity_score": sa.Column("subjectivity_score", sa.Float(), server_default="0.0", nullable=False),
        "confidence_score": sa.Column("confidence_score", sa.Float(), server_default="0.0", nullable=False),
        "aspects_json": sa.Column("aspects_json", sa.Text(), server_default="{}", nullable=True),
        "quality_score": sa.Column("quality_score", sa.Float(), server_default="1.0", nullable=False),
    }
    missing_additions = [column for name, column in sentiment_additions.items() if name not in sentiment_columns]
    if missing_additions:
        with op.batch_alter_table("sentiment_results") as batch_op:
            for column in missing_additions:
                batch_op.add_column(column)


def downgrade() -> None:
    with op.batch_alter_table("sentiment_results") as batch_op:
        batch_op.drop_column("quality_score")
        batch_op.drop_column("aspects_json")
        batch_op.drop_column("confidence_score")
        batch_op.drop_column("subjectivity_score")
        batch_op.drop_column("polarity_score")

    with op.batch_alter_table("reviews") as batch_op:
        batch_op.drop_column("verified_purchase")
