"""Initial CampusFind tables.

Revision ID: 0001_initial
Revises:
"""
from alembic import op
from app.db.session import Base
from app import models

revision='0001_initial'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    Base.metadata.create_all(bind=bind)

def downgrade():
    # Do not drop application tables or user data through a migration rollback.
    pass
