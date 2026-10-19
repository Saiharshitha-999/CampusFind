from app.models import AuditEvent


def recent_audit_events(db, limit=500):
    return db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
