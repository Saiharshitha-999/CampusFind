"""Add normalized UML records and migrate the legacy schema without dropping data.

Revision ID: 0002_uml_workflows
Revises: 0001_initial
"""
from alembic import op
from sqlalchemy import Boolean, DateTime, Integer, String, inspect, text
from app.models import AuditEvent, Claim, FoundReport, LostReport, Match, StatusHistory

revision = '0002_uml_workflows'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def _columns(bind, table):
    return {column['name'] for column in inspect(bind).get_columns(table)}


def _rename(table, old, new, type_):
    bind = op.get_bind()
    if table not in inspect(bind).get_table_names():
        return
    names = _columns(bind, table)
    if old in names and new not in names:
        op.alter_column(table, old, new_column_name=new, existing_type=type_)


def _add(table, name, column):
    bind = op.get_bind()
    if name not in _columns(bind, table):
        op.add_column(table, column)


def upgrade():
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if 'users' not in tables:
        return

    # Rename fields in place; this preserves existing account IDs and password hashes.
    _rename('users', 'id', 'user_id', Integer())
    _rename('users', 'display_name', 'name', String(120))
    _add('users', 'verification_status', __import__('sqlalchemy').Column('verification_status', String(20), nullable=False, server_default='Unverified'))
    _add('users', 'active', __import__('sqlalchemy').Column('active', Boolean(), nullable=False, server_default=__import__('sqlalchemy').true()))
    names = _columns(bind, 'users')
    if 'verified' in names:
        bind.execute(text("UPDATE users SET verification_status = CASE WHEN verified THEN 'Verified' ELSE 'Unverified' END"))
    if 'role' in names:
        bind.execute(text("UPDATE users SET role = CASE WHEN lower(role) IN ('admin','administrator') THEN 'Administrator' ELSE 'Campus User' END"))

    # Add the UML entities. Existing legacy report rows are copied below.
    for model_table in (LostReport.__table__, FoundReport.__table__, Match.__table__, AuditEvent.__table__, StatusHistory.__table__):
        model_table.create(bind=bind, checkfirst=True)

    tables = set(inspect(bind).get_table_names())
    if 'item_reports' in tables:
        bind.execute(text("""UPDATE item_reports SET status = CASE status
            WHEN 'pending_review' THEN 'Pending Approval' WHEN 'approved' THEN 'Active'
            WHEN 'rejected' THEN 'Rejected' WHEN 'matched' THEN 'Match Found'
            WHEN 'claimed' THEN 'Claim Requested' WHEN 'returned' THEN 'Returned'
            WHEN 'closed' THEN 'Closed' ELSE status END"""))
        date_expr = "date(occurred_at)" if bind.dialect.name == 'sqlite' else "CAST(occurred_at AS DATE)"
        bind.execute(text(f"""INSERT INTO lost_reports (report_id, owner_id, category, description, location, date_lost, status, created_at)
            SELECT i.id, i.owner_id, i.category, i.description, i.location, {date_expr}, i.status, i.created_at
            FROM item_reports i WHERE i.kind='lost' AND NOT EXISTS (SELECT 1 FROM lost_reports l WHERE l.report_id=i.id)"""))
        bind.execute(text(f"""INSERT INTO found_reports (report_id, finder_id, category, description, found_location, date_found, custody_location, status, created_at)
            SELECT i.id, i.owner_id, i.category, i.description, i.location, {date_expr}, i.custody_location, i.status, i.created_at
            FROM item_reports i WHERE i.kind='found' AND NOT EXISTS (SELECT 1 FROM found_reports f WHERE f.report_id=i.id)"""))

    if 'claims' in set(inspect(bind).get_table_names()):
        _rename('claims', 'id', 'claim_id', Integer())
        _rename('claims', 'item_id', 'report_id', Integer())
        _rename('claims', 'proof_description', 'proof_reference', String())
        _add('claims', 'reviewer_id', __import__('sqlalchemy').Column('reviewer_id', Integer(), nullable=True))
        _add('claims', 'decided_at', __import__('sqlalchemy').Column('decided_at', DateTime(), nullable=True))
        bind.execute(text("UPDATE claims SET status = CASE lower(status) WHEN 'pending' THEN 'Pending' WHEN 'approved' THEN 'Approved for Return' WHEN 'rejected' THEN 'Rejected' ELSE status END"))
        # Replace the legacy report FK with the UML FoundReport FK while keeping
        # every old claim row in a retained table.
        foreign_keys = inspect(bind).get_foreign_keys('claims')
        if any(fk.get('referred_table') == 'item_reports' for fk in foreign_keys):
            _add('claims', 'proof_filename', __import__('sqlalchemy').Column('proof_filename', String(255), nullable=True))
            for index in inspect(bind).get_indexes('claims'):
                if index.get('name'):
                    op.drop_index(index['name'], table_name='claims')
            op.rename_table('claims', 'claims_legacy')
            Claim.__table__.create(bind=bind, checkfirst=True)
            bind.execute(text("""INSERT INTO claims
                (claim_id, report_id, claimant_id, proof_reference, status, reviewer_id, decision_comment, created_at, decided_at)
                SELECT claim_id, report_id, claimant_id, COALESCE(proof_filename, ''), status, reviewer_id, decision_comment, created_at, decided_at
                FROM claims_legacy"""))
            if bind.dialect.name == 'postgresql':
                bind.execute(text("SELECT setval(pg_get_serial_sequence('claims','claim_id'), GREATEST((SELECT COALESCE(MAX(claim_id),1) FROM claims),1), true)"))

    if 'notifications' in set(inspect(bind).get_table_names()):
        _rename('notifications', 'id', 'notification_id', Integer())
        _rename('notifications', 'user_id', 'recipient_id', Integer())
        _add('notifications', 'type', __import__('sqlalchemy').Column('type', String(60), nullable=False, server_default='general'))
        _add('notifications', 'delivery_status', __import__('sqlalchemy').Column('delivery_status', String(12), nullable=False, server_default='Pending'))
        _add('notifications', 'read_at', __import__('sqlalchemy').Column('read_at', DateTime(), nullable=True))
        if 'read' in _columns(bind, 'notifications'):
            read_expr = "CASE WHEN read THEN CURRENT_TIMESTAMP ELSE NULL END"
            bind.execute(text(f"UPDATE notifications SET read_at = {read_expr} WHERE read_at IS NULL"))


def downgrade():
    # Keep migrated user data intact. A schema rollback needs a separately
    # reviewed backup/restore plan; it must never drop the database volume.
    pass
