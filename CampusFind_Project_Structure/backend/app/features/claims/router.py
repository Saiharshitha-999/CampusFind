from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
from uuid import uuid4
from fastapi.responses import FileResponse
from app.core.config import settings
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import verified_user, admin_user
from app.models import Claim, FoundReport, ItemReport, User, AuditEvent, StatusHistory
from app.features.status.service import record_status_change
from app.models import AuditLog
from app.features.claims.service import claim_data
from app.features.notifications.service import notify

router=APIRouter()

@router.post('/items/{item_id}/claims',status_code=201)
async def create_claim(item_id:int, file:UploadFile=File(...), user:User=Depends(verified_user), db:Session=Depends(get_db)):
    item=db.query(ItemReport).filter_by(id=item_id).with_for_update().one_or_none()
    if not item or item.status!='Match Found' or item.kind!='found': raise HTTPException(404,'Claimable matched found item not found')
    if item.owner_id==user.id: raise HTTPException(400,'You cannot claim your own report')
    if db.query(Claim).filter_by(report_id=item_id,claimant_id=user.id,status='Pending').first(): raise HTTPException(409,'You already have a pending claim')
    ext={ 'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','application/pdf':'.pdf' }.get(file.content_type or '')
    if not ext: raise HTTPException(415,'Proof must be a JPEG, PNG, WebP, or PDF')
    content=await file.read(settings.max_upload_bytes+1)
    if len(content)>settings.max_upload_bytes: raise HTTPException(413,'Proof must be at most 5 MB')
    valid=(ext=='.jpg' and content.startswith(b'\xff\xd8\xff')) or (ext=='.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (ext=='.webp' and content.startswith(b'RIFF') and content[8:12]==b'WEBP') or (ext=='.pdf' and content.startswith(b'%PDF-'))
    if not valid: raise HTTPException(415,'Proof contents do not match the declared file type')
    folder=Path(settings.upload_dir).parent/'private-proof'; folder.mkdir(parents=True,exist_ok=True)
    filename=uuid4().hex+ext; (folder/filename).write_bytes(content)
    claim=Claim(report_id=item_id,claimant_id=user.id,proof_reference=filename,status='Pending'); db.add(claim); db.flush()
    old=item.status; item.status='Claim Requested'
    db.get(FoundReport,item.id).status=item.status
    record_status_change(db,entity_type='report',entity_id=item.id,old_status=old,new_status=item.status,actor_id=user.id)
    db.add(StatusHistory(entity_type='claim',entity_id=claim.id,old_status='',new_status='Pending',changed_by=user.id))
    admins=db.query(User).filter(User.role=='Administrator',User.active.is_(True)).all()
    for administrator in admins:
        notify(db,administrator.id,f'A claim was submitted for found report {item.id}.',administrator.email,notification_type='claim.submitted')
    notify(db,item.owner_id,f'A claim was submitted for your found report "{item.item_name}".',item.contact_email,notification_type='claim.submitted')
    db.commit(); db.refresh(claim)
    return claim_data(claim)

@router.get('/claims/mine')
def mine(user:User=Depends(verified_user),db:Session=Depends(get_db)):
    return [claim_data(c) for c in db.query(Claim).filter_by(claimant_id=user.id).order_by(Claim.created_at.desc()).all()]

@router.get('/claims/received')
def received(user:User=Depends(verified_user),db:Session=Depends(get_db)):
    return [claim_data(c, include_proof=False) for c in db.query(Claim).join(ItemReport,Claim.report_id==ItemReport.id).filter(ItemReport.owner_id==user.id).order_by(Claim.created_at.desc()).all()]

@router.post('/claims/{claim_id}/proof')
async def upload_proof(claim_id:int, file:UploadFile=File(...), user:User=Depends(verified_user), db:Session=Depends(get_db)):
    claim=db.get(Claim,claim_id)
    if not claim or claim.claimant_id!=user.id: raise HTTPException(404,'Claim not found')
    if claim.status!='Pending' or claim.proof_reference: raise HTTPException(409,'Proof can only be added to a pending claim that has no proof yet')
    ext={ 'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','application/pdf':'.pdf' }.get(file.content_type or '')
    if not ext: raise HTTPException(415,'Proof must be a JPEG, PNG, WebP, or PDF')
    content=await file.read(settings.max_upload_bytes+1)
    if len(content)>settings.max_upload_bytes: raise HTTPException(413,'Proof must be at most 5 MB')
    valid=(ext=='.jpg' and content.startswith(b'\xff\xd8\xff')) or (ext=='.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (ext=='.webp' and content.startswith(b'RIFF') and content[8:12]==b'WEBP') or (ext=='.pdf' and content.startswith(b'%PDF-'))
    if not valid: raise HTTPException(415,'Proof contents do not match the declared file type')
    folder=Path(settings.upload_dir).parent/'private-proof'; folder.mkdir(parents=True,exist_ok=True)
    name=uuid4().hex+ext; (folder/name).write_bytes(content); claim.proof_reference=name; db.commit()
    return {'message':'Proof uploaded securely'}

@router.get('/claims/{claim_id}/proof')
def download_proof(claim_id:int,user:User=Depends(verified_user),db:Session=Depends(get_db)):
    claim=db.get(Claim,claim_id)
    if not claim or not claim.proof_reference: raise HTTPException(404,'Proof not found')
    if user.id != claim.claimant_id and user.role != 'Administrator': raise HTTPException(404,'Proof not found')
    reference=Path(claim.proof_reference)
    if reference.name != claim.proof_reference or reference.suffix.lower() not in ('.jpg','.png','.webp','.pdf'):
        raise HTTPException(404,'Proof not found')
    path=Path(settings.upload_dir).parent/'private-proof'/reference
    if not path.exists(): raise HTTPException(404,'Proof not found')
    return FileResponse(path,filename=path.name)

class ClaimDecision(BaseModel):
    decision:str
    comment:str=Field(default='',max_length=2000)

@router.post('/claims/{claim_id}/decision')
def decide(claim_id:int, body:ClaimDecision, user:User=Depends(admin_user),db:Session=Depends(get_db)):
    claim=db.get(Claim,claim_id)
    if not claim: raise HTTPException(404,'Claim not found')
    item=db.query(ItemReport).filter_by(id=claim.item_id).with_for_update().one_or_none()
    if not item: raise HTTPException(404,'Item not found')
    if claim.status!='Pending' or item.status!='Claim Requested' or body.decision not in ('approve','reject'): raise HTTPException(409,'Claim is not awaiting a valid decision')
    if not claim.proof_reference: raise HTTPException(409,'Claim proof has not been uploaded')
    if body.decision=='approve' and item.status != 'Claim Requested':
        raise HTTPException(409,'This item can no longer be awarded to a claimant')
    if body.decision=='reject' and not body.comment.strip():
        raise HTTPException(422,'A decision comment is required when rejecting a claim')
    claim.status='Approved for Return' if body.decision=='approve' else 'Rejected'; claim.decision_comment=body.comment or None
    claim.reviewer_id=user.id; claim.decided_at=__import__('datetime').datetime.utcnow()
    db.add(StatusHistory(entity_type='claim',entity_id=claim.id,old_status='Pending',new_status=claim.status,changed_by=user.id))
    audit_action=f'claim.{body.decision}'
    if body.comment.strip(): audit_action=f'{audit_action}: {body.comment.strip()}'
    db.add(AuditEvent(actor_id=user.id,action=audit_action,entity_type='claim',entity_id=claim.id))
    if body.decision=='approve':
        old=item.status; item.status='Approved for Return'
        db.get(FoundReport,item.id).status=item.status
        record_status_change(db,entity_type='report',entity_id=item.id,old_status=old,new_status=item.status,actor_id=user.id)
        other_claims=db.query(Claim).filter(Claim.report_id==item.id,Claim.id!=claim.id,Claim.status=='Pending').all()
        for other in other_claims:
            other.status='Rejected'; other.decision_comment='Another claim for this item was approved.'; other.reviewer_id=user.id; other.decided_at=__import__('datetime').datetime.utcnow()
            db.add(StatusHistory(entity_type='claim',entity_id=other.id,old_status='Pending',new_status='Rejected',changed_by=user.id))
            db.add(AuditEvent(actor_id=user.id,action='claim.auto_reject',entity_type='claim',entity_id=other.id))
            db.add(AuditLog(actor_id=user.id,action='claim.auto_reject',entity_type='claim',entity_id=other.id,detail=other.decision_comment))
            other_user=db.get(User,other.claimant_id)
            notify(db,other.claimant_id,f'Your claim for "{item.item_name}" was rejected because another claimant was approved.',other_user.email if other_user else None,notification_type='claim.rejected')
    else:
        old=item.status; item.status='Match Found'
        db.get(FoundReport,item.id).status=item.status
        record_status_change(db,entity_type='report',entity_id=item.id,old_status=old,new_status=item.status,actor_id=user.id)
    db.add(AuditLog(actor_id=user.id,action=f'claim.{body.decision}',entity_type='claim',entity_id=claim.id,detail=body.comment))
    claimant=db.get(User,claim.claimant_id)
    notify(db,claim.claimant_id,f'Your claim for "{item.item_name}" was {claim.status}.',claimant.email if claimant else None,notification_type='claim.decision')
    db.commit(); return claim_data(claim)
