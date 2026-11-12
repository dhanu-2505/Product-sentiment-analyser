"""Initial ReviewLens schema

Revision ID: 20260925
Revises: 
Create Date: 2026-09-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260925"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    core_tables = {
        "users",
        "products",
        "reviews",
        "saved_products",
        "search_history",
        "sentiment_results",
        "analysis_history",
    }
    if core_tables.issubset(existing_tables):
        return

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("brand", sa.String(length=150), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("product_url", sa.String(length=500), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("features", sa.Text(), nullable=True),
        sa.Column("price", sa.String(length=50), nullable=True),
        sa.Column("average_rating", sa.Float(), nullable=True),
        sa.Column("total_reviews", sa.Integer(), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"], unique=False)
    op.create_index(op.f("ix_products_name"), "products", ["name"], unique=False)

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("reviewer_name", sa.String(length=150), nullable=True),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_date", sa.DateTime(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reviews_id"), "reviews", ["id"], unique=False)
    op.create_index(op.f("ix_reviews_product_id"), "reviews", ["product_id"], unique=False)

    op.create_table(
        "saved_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("saved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_saved_products_id"), "saved_products", ["id"], unique=False)
    op.create_index(op.f("ix_saved_products_product_id"), "saved_products", ["product_id"], unique=False)
    op.create_index(op.f("ix_saved_products_user_id"), "saved_products", ["user_id"], unique=False)

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("searched_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_search_history_id"), "search_history", ["id"], unique=False)
    op.create_index(op.f("ix_search_history_user_id"), "search_history", ["user_id"], unique=False)

    op.create_table(
        "sentiment_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("sentiment_label", sa.String(length=20), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=False),
        sa.Column("compound_score", sa.Float(), nullable=False),
        sa.Column("positive_score", sa.Float(), nullable=False),
        sa.Column("neutral_score", sa.Float(), nullable=False),
        sa.Column("negative_score", sa.Float(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sentiment_results_id"), "sentiment_results", ["id"], unique=False)
    op.create_index(op.f("ix_sentiment_results_review_id"), "sentiment_results", ["review_id"], unique=True)

    op.create_table(
        "analysis_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("total_reviews", sa.Integer(), nullable=False),
        sa.Column("positive_count", sa.Integer(), nullable=False),
        sa.Column("neutral_count", sa.Integer(), nullable=False),
        sa.Column("negative_count", sa.Integer(), nullable=False),
        sa.Column("positive_percentage", sa.Float(), nullable=False),
        sa.Column("neutral_percentage", sa.Float(), nullable=False),
        sa.Column("negative_percentage", sa.Float(), nullable=False),
        sa.Column("average_rating", sa.Float(), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_history_id"), "analysis_history", ["id"], unique=False)
    op.create_index(op.f("ix_analysis_history_product_id"), "analysis_history", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_table("analysis_history")
    op.drop_table("sentiment_results")
    op.drop_table("search_history")
    op.drop_table("saved_products")
    op.drop_table("reviews")
    op.drop_table("products")
    op.drop_table("users")
