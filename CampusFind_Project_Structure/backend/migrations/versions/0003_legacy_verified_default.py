"""Allow new ORM accounts in databases that retain the legacy verified column.

Revision ID: 0003_legacy_verified_default
Revises: 0002_uml_workflows
"""
from alembic import op
from sqlalchemy import Boolean, false, inspect

revision = "0003_legacy_verified_default"
down_revision = "0002_uml_workflows"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "users" not in tables:
        return
    columns = {column["name"]: column for column in inspect(bind).get_columns("users")}
    # Older project databases still have a NOT NULL `verified` boolean column.
    # Current ORM writes verification_status instead, so give that retained
    # compatibility column the correct default for newly registered accounts.
    if "verified" in columns and columns["verified"].get("default") is None:
        if bind.dialect.name == "sqlite":
            with op.batch_alter_table("users") as batch:
                batch.alter_column("verified", existing_type=Boolean(), server_default=false())
        else:
            op.alter_column(
                "users",
                "verified",
                existing_type=Boolean(),
                server_default=false(),
            )


def downgrade():
    # Keep this compatibility default in place during downgrade; removing it
    # would make current application writes fail against the retained column.
    pass
