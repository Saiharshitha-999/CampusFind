from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.time import utc_isoformat
from app.models import ItemImage, ItemReport

ALLOWED_IMAGE_TYPES={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}

def report_dict(report: ItemReport, include_private=False):
    data={'report_id':report.id,'id':report.id,'owner_id':report.owner_id,'kind':report.kind,'item_name':report.item_name,'category':report.category,'description':report.description,
          'occurred_at':report.occurred_at.isoformat(),'location':report.location,'custody_location':report.custody_location,
          'status':report.status,'created_at':utc_isoformat(report.created_at),'images':[f'/uploads/{image.filename}' for image in report.images]}
    if include_private: data.update(contact_email=report.contact_email,moderation_comment=report.moderation_comment)
    return data

async def store_report_images(images: list[UploadFile], report_id: int, db: Session):
    if len(images)>5: raise HTTPException(422,'Upload no more than five images')
    pending=[]
    for upload in images:
        extension=ALLOWED_IMAGE_TYPES.get(upload.content_type or '')
        if not extension: raise HTTPException(415,'Only JPEG, PNG, and WebP images are allowed')
        content=await upload.read(settings.max_upload_bytes+1)
        if len(content)>settings.max_upload_bytes: raise HTTPException(413,'Each image must be at most 5 MB')
        valid=(extension=='.jpg' and content.startswith(b'\xff\xd8\xff')) or (extension=='.png' and content.startswith(b'\x89PNG\r\n\x1a\n')) or (extension=='.webp' and content.startswith(b'RIFF') and content[8:12]==b'WEBP')
        if not valid: raise HTTPException(415,'Image contents do not match the declared file type')
        pending.append((uuid4().hex+extension,content))
    folder=Path(settings.upload_dir); folder.mkdir(parents=True,exist_ok=True)
    for filename,content in pending:
        (folder/filename).write_bytes(content)
        db.add(ItemImage(item_id=report_id,filename=filename))
