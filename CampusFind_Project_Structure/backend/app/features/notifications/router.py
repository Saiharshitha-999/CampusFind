from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import verified_user
from app.models import Notification, User
from app.core.time import utc_isoformat

router=APIRouter()
@router.get('')
def history(user:User=Depends(verified_user),db:Session=Depends(get_db)):
    rows=db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [{'notification_id':n.id,'id':n.id,'recipient_id':n.recipient_id,'type':n.type,'message':n.message,'read':n.read,
             'read_at':utc_isoformat(n.read_at) if n.read_at else None,
             'delivery_status':n.delivery_status,'created_at':utc_isoformat(n.created_at)} for n in rows]

@router.post('/{notification_id}/read')
def mark_read(notification_id:int,user:User=Depends(verified_user),db:Session=Depends(get_db)):
    notification=db.get(Notification,notification_id)
    if not notification or notification.user_id!=user.id: raise HTTPException(404,'Notification not found')
    notification.read=True; db.commit(); return {'notification_id':notification.id,'id':notification.id,'read_at':utc_isoformat(notification.read_at),'read':True}
