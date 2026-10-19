from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import ValidationError
from app.core.security import verified_user
from app.db.session import get_db
from app.models import ItemReport, LostReport, FoundReport, User
from app.features.reports.schemas import ReportCreate
from app.features.reports.service import report_dict, store_report_images

router = APIRouter()
@router.post('/{kind}', status_code=201)
async def create_report(kind: str, item_name: str = Form(...), category: str = Form(...), description: str = Form(...), occurred_at: str = Form(...), location: str = Form(...), custody_location: str = Form(''), images: list[UploadFile] = File(default=[]), user: User = Depends(verified_user), db: Session = Depends(get_db)):
    if kind not in ('lost', 'found'): raise HTTPException(404, 'Report type must be lost or found')
    try:
        body = ReportCreate(item_name=item_name, category=category, description=description, occurred_at=occurred_at, location=location, custody_location=custody_location)
    except ValidationError as error:
        raise HTTPException(422, 'Report fields are invalid') from error
    if kind == 'found' and not custody_location.strip(): raise HTTPException(422, 'Custody location is required for found items')
    report = ItemReport(owner_id=user.id, kind=kind, item_name=body.item_name, category=body.category, description=body.description,
                        occurred_at=body.occurred_at, location=body.location, contact_email=user.email, custody_location=custody_location or None,
                        status='Pending Approval')
    db.add(report); db.flush()
    # Keep the normalized UML report entity in sync with the compatibility API
    # row while existing clients still submit the legacy form fields.
    report_id = report.id
    if kind == 'lost':
        db.add(LostReport(report_id=report_id, owner_id=user.id, category=body.category,
                          description=body.description, location=body.location,
                          date_lost=body.occurred_at.date(), status='Pending Approval'))
    else:
        db.add(FoundReport(report_id=report_id, finder_id=user.id, category=body.category,
                           description=body.description, found_location=body.location,
                           date_found=body.occurred_at.date(), custody_location=custody_location or None,
                           status='Pending Approval'))
    # Explicit shared report IDs keep the legacy REST identifier stable.
    if db.bind.dialect.name == 'postgresql':
        table = 'lost_reports' if kind == 'lost' else 'found_reports'
        db.flush()
        db.execute(__import__('sqlalchemy').text(
            f"SELECT setval(pg_get_serial_sequence('{table}','report_id'), GREATEST((SELECT COALESCE(MAX(report_id),1) FROM {table}), 1), true)"))
    await store_report_images(images, report.id, db)
    db.commit(); db.refresh(report)
    return report_dict(report, True)

@router.get('/mine')
def mine(user: User = Depends(verified_user), db: Session = Depends(get_db)):
    return [report_dict(r, True) for r in db.query(ItemReport).filter_by(owner_id=user.id).order_by(ItemReport.created_at.desc()).all()]
