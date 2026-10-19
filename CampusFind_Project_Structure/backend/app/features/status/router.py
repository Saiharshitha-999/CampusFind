from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import admin_user, verified_user
from app.db.session import get_db
from app.features.status.schemas import StatusUpdate
from app.core.time import utc_isoformat
from app.features.status.service import record_status_change
from app.features.notifications.service import notify
from app.models import FoundReport, ItemReport, User, StatusHistory

router = APIRouter()
OWNER_TRANSITIONS = {"Approved for Return": "Returned"}


@router.post('/items/{item_id}/status')
def update_status(item_id: int, body: StatusUpdate, user: User = Depends(verified_user), db: Session = Depends(get_db)):
    item = db.query(ItemReport).filter_by(id=item_id).with_for_update().one_or_none()
    if not item or item.owner_id != user.id:
        raise HTTPException(404, 'Item not found')
    expected = OWNER_TRANSITIONS.get(item.status)
    if expected != body.status:
        raise HTTPException(409, 'Only the report owner can confirm handoff from Approved for Return to Returned')
    old = item.status
    item.status = body.status
    found = db.get(FoundReport, item.id)
    if found:
        found.status = body.status
    record_status_change(db, entity_type='report', entity_id=item.id, old_status=old,
                         new_status=body.status, actor_id=user.id)
    notify(db, user.id, f'You confirmed the handoff for "{item.item_name}".')
    db.commit()
    return {'id': item.id, 'status': item.status}


@router.post('/items/{item_id}/close')
def close_recovery(item_id: int, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    item = db.query(ItemReport).filter_by(id=item_id).with_for_update().one_or_none()
    if not item:
        raise HTTPException(404, 'Item not found')
    if item.status != 'Returned':
        raise HTTPException(409, 'Only a Returned recovery can be closed')
    old = item.status
    item.status = 'Closed'
    found = db.get(FoundReport, item.id)
    if found:
        found.status = item.status
    record_status_change(db, entity_type='report', entity_id=item.id, old_status=old,
                         new_status=item.status, actor_id=user.id)
    notify(db, item.owner_id, f'Recovery for "{item.item_name}" has been closed.', item.contact_email)
    db.commit()
    return {'id': item.id, 'status': item.status}


@router.get('/items/{item_id}/history')
def status_history(item_id: int, user: User = Depends(verified_user), db: Session = Depends(get_db)):
    item = db.get(ItemReport, item_id)
    if not item or (item.owner_id != user.id and user.role != 'Administrator'):
        raise HTTPException(404, 'Item not found')
    rows = db.query(StatusHistory).filter_by(entity_type='report', entity_id=item_id).order_by(StatusHistory.changed_at.asc()).all()
    return [{'history_id': row.history_id, 'old_status': row.old_status, 'new_status': row.new_status,
             'changed_by': row.changed_by, 'changed_at': utc_isoformat(row.changed_at)} for row in rows]
