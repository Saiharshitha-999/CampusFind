from app.models import AuditEvent, StatusHistory


def record_status_change(db, *, entity_type: str, entity_id: int, old_status: str,
                         new_status: str, actor_id: int | None):
    db.add(StatusHistory(entity_type=entity_type, entity_id=entity_id,
                         old_status=old_status, new_status=new_status,
                         changed_by=actor_id))
    db.add(AuditEvent(actor_id=actor_id, action=f"{old_status} -> {new_status}",
                      entity_type=entity_type, entity_id=entity_id))
