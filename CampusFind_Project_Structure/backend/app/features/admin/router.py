from datetime import datetime
from app.core.time import utc_isoformat
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import admin_user
from app.models import AuditEvent, AuditLog, Claim, FoundReport, ItemReport, LostReport, Match, User
from app.features.reports.service import report_dict
from app.features.claims.service import claim_data
from app.features.notifications.service import notify
from app.features.matching.service import score_match
from app.features.status.service import record_status_change
from app.features.audit.service import recent_audit_events

router = APIRouter()

class Decision(BaseModel):
    decision: str
    comment: str = Field(default='', max_length=2000)


def run_matching(db: Session, approved: ItemReport, actor_id: int):
    candidates = db.query(ItemReport).filter(
        ItemReport.kind != approved.kind,
        ItemReport.status.in_(('Active', 'Match Found')),
        ItemReport.id != approved.id,
    ).all()
    for candidate in candidates:
        lost, found = (approved, candidate) if approved.kind == 'lost' else (candidate, approved)
        lost_row, found_row = db.get(LostReport, lost.id), db.get(FoundReport, found.id)
        if not lost_row or not found_row:
            continue
        result = score_match(approved, candidate)
        if db.query(Match).filter_by(lost_report_id=lost.id, found_report_id=found.id).first():
            continue
        db.add(Match(lost_report_id=lost.id, found_report_id=found.id, score=result['score'],
                     confidence=result['confidence'], status='Match Found'))
        for report in (lost, found):
            old = report.status
            if old == 'Active':
                report.status = 'Match Found'
                if report.kind == 'lost':
                    db.get(LostReport, report.id).status = 'Match Found'
                else:
                    db.get(FoundReport, report.id).status = 'Match Found'
                record_status_change(db, entity_type='report', entity_id=report.id,
                                     old_status=old, new_status='Match Found', actor_id=actor_id)
        if result['confidence'] == 'High':
            message = f'A high-confidence possible match was found for your {lost.kind} report "{lost.item_name}".'
            notify(db, lost.owner_id, message, lost.contact_email, notification_type='match')
            notify(db, found.owner_id, f'A high-confidence possible match was found for your found report "{found.item_name}".', found.contact_email, notification_type='match')


@router.get('/reports/pending')
def pending(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [report_dict(r, True) for r in db.query(ItemReport).filter_by(status='Pending Approval').order_by(ItemReport.created_at.asc()).all()]


@router.post('/reports/{report_id}/decision')
def moderate(report_id: int, body: Decision, user: User = Depends(admin_user), db: Session = Depends(get_db)):
    report = db.query(ItemReport).filter_by(id=report_id).with_for_update().one_or_none()
    if not report:
        raise HTTPException(404, 'Report not found')
    if report.status != 'Pending Approval' or body.decision not in ('approve', 'reject'):
        raise HTTPException(409, 'Report is not awaiting a valid decision')
    if body.decision == 'reject' and not body.comment.strip():
        raise HTTPException(422, 'A rejection reason is required')
    old = report.status
    report.status = 'Active' if body.decision == 'approve' else 'Rejected'
    report.moderation_comment = body.comment.strip() or None
    record_status_change(db, entity_type='report', entity_id=report.id, old_status=old,
                         new_status=report.status, actor_id=user.id)
    if report.kind == 'lost':
        row = db.get(LostReport, report.id)
    else:
        row = db.get(FoundReport, report.id)
    if row:
        row.status = report.status
    db.add(AuditLog(actor_id=user.id, action=f'report.{body.decision}', entity_type='report', entity_id=report.id, detail=body.comment))
    audit_action = f'report.{body.decision}'
    if body.decision == 'reject':
        audit_action = f'{audit_action}: {body.comment.strip()}'
    db.add(AuditEvent(actor_id=user.id, action=audit_action, entity_type='report', entity_id=report.id))
    if body.decision == 'approve':
        run_matching(db, report, user.id)
        message = f'Your {report.kind} report "{report.item_name}" was approved.'
    else:
        message = f'Your {report.kind} report "{report.item_name}" was rejected: {body.comment.strip()}'
    notify(db, report.owner_id, message, report.contact_email, notification_type=f'report.{body.decision}')
    db.commit()
    return report_dict(report, True)


@router.get('/claims/pending')
def pending_claims(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    rows = db.query(Claim).filter_by(status='Pending').order_by(Claim.created_at.asc()).all()
    return [claim_data(c) for c in rows]


@router.get('/audit')
def audit_records(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    rows = recent_audit_events(db)
    return [{'event_id': row.event_id, 'actor_id': row.actor_id, 'action': row.action,
             'entity_type': row.entity_type, 'entity_id': row.entity_id,
             'timestamp': utc_isoformat(row.timestamp)} for row in rows]


@router.get('/recoveries')
def recoveries(user: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [report_dict(r, True) for r in db.query(ItemReport).filter_by(status='Returned').order_by(ItemReport.created_at.asc()).all()]
