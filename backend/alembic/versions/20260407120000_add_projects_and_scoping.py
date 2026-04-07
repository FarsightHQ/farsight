"""Add projects, memberships, invitations, project_assets; scope far_requests.

Revision ID: 20260407120000
Revises: 20260404160000
Create Date: 2026-04-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "20260407120000"
down_revision = "20260404160000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    op.create_table(
        "projects",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "legacy_unrestricted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_sub", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_slug"), "projects", ["slug"], unique=True)

    op.create_table(
        "project_members",
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("user_sub", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_sub"),
    )

    op.create_table(
        "project_invitations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("invited_by_sub", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_project_invitations_token_hash"),
    )
    op.create_index(
        op.f("ix_project_invitations_project_id"),
        "project_invitations",
        ["project_id"],
        unique=False,
    )

    op.create_table(
        "project_assets",
        sa.Column("project_id", sa.BigInteger(), nullable=False),
        sa.Column("asset_registry_id", sa.BigInteger(), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("linked_by_sub", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_registry_id"], ["asset_registry.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "asset_registry_id"),
    )

    op.add_column("far_requests", sa.Column("project_id", sa.BigInteger(), nullable=True))

    conn.execute(
        text(
            """
            INSERT INTO projects (name, slug, description, legacy_unrestricted, created_by_sub)
            VALUES (
                'Default',
                'default',
                'Migrated workspace; any authenticated user may access while legacy_unrestricted is true.',
                true,
                'system'
            )
            """
        )
    )
    default_pid = conn.execute(text("SELECT id FROM projects WHERE slug = 'default'")).scalar()

    conn.execute(
        text("UPDATE far_requests SET project_id = :pid WHERE project_id IS NULL"),
        {"pid": default_pid},
    )

    op.alter_column(
        "far_requests",
        "project_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_far_requests_project_id",
        "far_requests",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_far_requests_project_id"), "far_requests", ["project_id"], unique=False)

    conn.execute(
        text(
            """
            INSERT INTO project_assets (project_id, asset_registry_id, linked_at, linked_by_sub)
            SELECT :pid, ar.id, NOW(), 'system'
            FROM asset_registry ar
            ON CONFLICT DO NOTHING
            """
        ),
        {"pid": default_pid},
    )

    batch_cols = [c["name"] for c in sa.inspect(conn).get_columns("asset_upload_batches")]
    if "project_id" not in batch_cols:
        op.add_column(
            "asset_upload_batches",
            sa.Column("project_id", sa.BigInteger(), nullable=True),
        )
        op.create_foreign_key(
            "fk_asset_upload_batches_project_id",
            "asset_upload_batches",
            "projects",
            ["project_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(
            op.f("ix_asset_upload_batches_project_id"),
            "asset_upload_batches",
            ["project_id"],
            unique=False,
        )
        conn.execute(
            text("UPDATE asset_upload_batches SET project_id = :pid WHERE project_id IS NULL"),
            {"pid": default_pid},
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "asset_upload_batches" in inspector.get_table_names():
        batch_cols = [c["name"] for c in inspector.get_columns("asset_upload_batches")]
        if "project_id" in batch_cols:
            op.drop_index(
                op.f("ix_asset_upload_batches_project_id"),
                table_name="asset_upload_batches",
            )
            op.drop_constraint(
                "fk_asset_upload_batches_project_id",
                "asset_upload_batches",
                type_="foreignkey",
            )
            op.drop_column("asset_upload_batches", "project_id")

    op.drop_index(op.f("ix_far_requests_project_id"), table_name="far_requests")
    op.drop_constraint("fk_far_requests_project_id", "far_requests", type_="foreignkey")
    op.drop_column("far_requests", "project_id")

    op.drop_table("project_assets")
    op.drop_index(op.f("ix_project_invitations_project_id"), table_name="project_invitations")
    op.drop_table("project_invitations")
    op.drop_table("project_members")
    op.drop_index(op.f("ix_projects_slug"), table_name="projects")
    op.drop_table("projects")
