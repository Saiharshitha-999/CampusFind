"""Restore the legacy audit table used alongside normalized audit events.

Revision ID: 0005_audit_log_table
Revises: 0004_notify_read_default
"""
from alembic import op
from sqlalchemy import inspect
from app.models import AuditLog

revision = "0005_audit_log_table"
down_revision = "0004_notify_read_default"
branch_labels = None
depends_on = None


def upgrade():
    # Some databases were initialized before audit_logs was part of the schema.
    # Report and claim moderation still dual-write to this compatibility table.
    if "audit_logs" not in inspect(op.get_bind()).get_table_names():
        AuditLog.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade():
    # Keep audit history on downgrade.
    pass
