"""Default the retained legacy notifications.read column for ORM inserts.

Revision ID: 0004_notify_read_default
Revises: 0003_legacy_verified_default
"""
from alembic import op
from sqlalchemy import Boolean, false, inspect

revision = "0004_notify_read_default"
down_revision = "0003_legacy_verified_default"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "notifications" not in set(inspect(bind).get_table_names()):
        return
    columns = {column["name"]: column for column in inspect(bind).get_columns("notifications")}
    # The legacy boolean remains NOT NULL after 0002 copies it into read_at.
    # Current Notification inserts no longer write that compatibility column.
    if "read" not in columns or columns["read"].get("default") is not None:
        return
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("notifications") as batch:
            batch.alter_column("read", existing_type=Boolean(), server_default=false())
    else:
        op.alter_column(
            "notifications",
            "read",
            existing_type=Boolean(),
            server_default=false(),
        )


def downgrade():
    # Keep the default in place so current notification writes remain valid.
    pass
