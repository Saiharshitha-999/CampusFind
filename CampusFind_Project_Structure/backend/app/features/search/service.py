from app.models import ItemReport
from app.features.reports.router import report_dict
from app.features.matching.service import score_match

def search_reports(db, q='', kind='', category='', location='', sort='newest', page=1, limit=20):
    query = db.query(ItemReport).filter(ItemReport.status.notin_(('Pending Approval', 'Rejected')))
    for field, value in [('kind',kind),('category',category),('location',location)]:
        if value: query = query.filter(getattr(ItemReport, field).ilike(f'%{value}%'))
    if q: query = query.filter(ItemReport.item_name.ilike(f'%{q}%') | ItemReport.description.ilike(f'%{q}%'))
    query = query.order_by(ItemReport.occurred_at.asc() if sort == 'oldest' else ItemReport.item_name.asc() if sort == 'name' else ItemReport.created_at.desc())
    total = query.count(); items = query.offset((page-1)*limit).limit(limit).all()
    return {'items':[report_dict(x) for x in items], 'total':total, 'page':page, 'pages':(total+limit-1)//limit}
