from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import ItemReport, Match, User
from app.core.security import verified_user, optional_user
from app.features.search.service import search_reports
from app.features.reports.service import report_dict
from app.core.time import utc_isoformat

router = APIRouter()
@router.get('/items')
def search(q: str = '', kind: str = '', category: str = '', location: str = '', sort: str = 'newest', page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    if sort not in ('newest','oldest','name') or page < 1 or not 1 <= limit <= 100: raise HTTPException(422, 'Invalid sort or pagination values')
    return search_reports(db,q,kind,category,location,sort,page,limit)

@router.get('/items/{item_id}')
def item_detail(item_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    item = db.get(ItemReport,item_id)
    if not item or (item.status in ('Pending Approval','Rejected') and (not user or (user.id != item.owner_id and user.role != 'Administrator'))): raise HTTPException(404,'Item not found')
    return report_dict(item, bool(user and (user.id == item.owner_id or user.role == 'Administrator')))

@router.get('/items/{item_id}/matches')
def matches(item_id: int, db: Session = Depends(get_db), user: User = Depends(verified_user)):
    item = db.get(ItemReport,item_id)
    if not item or item.owner_id != user.id: raise HTTPException(404,'Item not found')
    if item.kind == 'lost':
        rows = db.query(Match).filter_by(lost_report_id=item.id).order_by(Match.score.desc()).limit(10).all()
        pairs = [(row, db.get(ItemReport, row.found_report_id)) for row in rows]
    else:
        rows = db.query(Match).filter_by(found_report_id=item.id).order_by(Match.score.desc()).limit(10).all()
        pairs = [(row, db.get(ItemReport, row.lost_report_id)) for row in rows]
    return [{'match_id': row.match_id, 'score': row.score, 'confidence': row.confidence,
             'status': row.status, 'created_at': utc_isoformat(row.created_at), 'item': report_dict(candidate)}
            for row, candidate in pairs if candidate]
