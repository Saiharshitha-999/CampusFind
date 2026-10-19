import pytest
from urllib.parse import parse_qs, urlparse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app
from app.models import User
from app.features.auth.service import hash_password

engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine,autoflush=False,expire_on_commit=False)
Base.metadata.create_all(engine)
def override_db():
    db=TestingSession()
    try: yield db
    finally: db.close()
app.dependency_overrides[get_db]=override_db
client=TestClient(app)

@pytest.fixture(autouse=True)
def clean_db(monkeypatch):
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    sent_emails = []
    from app.core.config import settings
    from unittest.mock import MagicMock
    smtp_context = MagicMock(); smtp_context.__enter__.return_value = MagicMock()
    monkeypatch.setattr(settings, 'smtp_host', 'test.smtp.local')
    monkeypatch.setattr(settings, 'smtp_from_email', 'campusfind@example.edu')
    monkeypatch.setattr('app.features.notifications.service.smtplib.SMTP', lambda *args, **kwargs: smtp_context)
    monkeypatch.setattr('app.features.auth.router.send_email', lambda email, subject, message: sent_emails.append((email, subject, message)) or True)
    app.state.test_sent_emails = sent_emails
    yield

def register(email='student@example.edu'):
    res=client.post('/api/v1/auth/register',json={'email':email,'password':'correct horse battery','display_name':'Student'})
    assert res.status_code==201
    token=parse_qs(urlparse(app.state.test_sent_emails[-1][2].splitlines()[2]).query)['token'][0]
    assert client.post('/api/v1/auth/verify-email',json={'token':token}).status_code==200
    login=client.post('/api/v1/auth/login',json={'email':email,'password':'correct horse battery'})
    return login.json()['access_token']

def test_registration_verification_and_login():
    response=client.post('/api/v1/auth/register',json={'email':'a@example.edu','password':'eightcharacterpass','display_name':'A'})
    assert response.status_code==201
    assert client.post('/api/v1/auth/login',json={'email':'a@example.edu','password':'eightcharacterpass'}).status_code==403
    verify_url=app.state.test_sent_emails[-1][2].splitlines()[2]
    assert 'development_token' not in response.json()
    assert client.post('/api/v1/auth/verify-email',json={'token':parse_qs(urlparse(verify_url).query)['token'][0]}).status_code==200
    assert client.post('/api/v1/auth/login',json={'email':'a@example.edu','password':'eightcharacterpass'}).status_code==200

def test_registration_requires_email_delivery(monkeypatch):
    monkeypatch.setattr('app.features.auth.router.send_email', lambda *args: False)
    response=client.post('/api/v1/auth/register',json={'email':'mail-failure@example.edu','password':'correct horse battery','display_name':'Student'})
    assert response.status_code==503
    with TestingSession() as db:
        assert db.query(User).filter_by(email='mail-failure@example.edu').first() is None

def test_verification_resend_and_password_reset_use_email_links():
    registration=client.post('/api/v1/auth/register',json={'email':'links@example.edu','password':'correct horse battery','display_name':'Links'})
    assert registration.status_code==201
    sent=app.state.test_sent_emails[-1]
    assert '/verify-email?token=' in sent[2]
    resend=client.post('/api/v1/auth/verification/request',json={'email':'links@example.edu'})
    assert resend.status_code==200 and 'sent' in resend.json()['message']
    assert len(app.state.test_sent_emails)==2
    reset=client.post('/api/v1/auth/password-reset/request',json={'email':'links@example.edu'})
    assert reset.status_code==200 and 'development_token' not in reset.json()
    assert '/password-reset/confirm?token=' in app.state.test_sent_emails[-1][2]

def test_email_requests_report_missing_smtp_configuration(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'smtp_host','')
    monkeypatch.setattr(settings,'smtp_from_email','')
    verification=client.post('/api/v1/auth/verification/request',json={'email':'unknown@example.edu'})
    reset=client.post('/api/v1/auth/password-reset/request',json={'email':'unknown@example.edu'})
    assert verification.status_code==503 and reset.status_code==503

def test_local_mailpit_delivery_does_not_require_starttls(monkeypatch):
    from unittest.mock import MagicMock
    from app.core.config import settings
    from app.features.notifications.service import send_email
    smtp = MagicMock()
    smtp_context = MagicMock()
    smtp_context.__enter__.return_value = smtp
    monkeypatch.setattr(settings, 'smtp_host', 'localhost')
    monkeypatch.setattr(settings, 'smtp_port', 1025)
    monkeypatch.setattr(settings, 'smtp_starttls', False)
    monkeypatch.setattr(settings, 'smtp_from_email', 'no-reply@campusfind.local')
    monkeypatch.setattr('app.features.notifications.service.smtplib.SMTP', lambda *args, **kwargs: smtp_context)

    assert send_email('student@example.edu', 'Verify', 'Open the link') is True
    smtp.starttls.assert_not_called()
    smtp.send_message.assert_called_once()

def test_report_moderation_and_approved_only_search():
    admin_token=register('admin@example.edu')
    with TestingSession() as db:
        admin=db.query(User).filter_by(email='admin@example.edu').one(); admin.role='Administrator'; db.commit()
    user_token=register('owner@example.edu')
    headers={'Authorization':f'Bearer {user_token}'}
    response=client.post('/api/v1/reports/found',headers=headers,data={'item_name':'Red umbrella','category':'Umbrella','description':'Wood handle','occurred_at':'2026-10-14T10:00:00','location':'Library','contact_email':'owner@example.edu','custody_location':'Front desk'})
    assert response.status_code==201
    item=response.json()
    assert client.get(f"/api/v1/items/{item['id']}").status_code==404
    assert client.get('/api/v1/items').json()['total']==0
    admin_headers={'Authorization':f'Bearer {admin_token}'}
    decision=client.post(f"/api/v1/admin/reports/{item['id']}/decision",headers=admin_headers,json={'decision':'approve','comment':'Reviewed'})
    assert decision.status_code==200
    results=client.get('/api/v1/items').json()
    assert results['total']==1 and results['items'][0]['item_name']=='Red umbrella'
    assert 'contact_email' not in results['items'][0]
    public_detail=client.get(f"/api/v1/items/{item['id']}")
    assert public_detail.status_code==200 and 'contact_email' not in public_detail.json()
    with TestingSession() as db:
        from app.models import AuditLog
        assert db.query(AuditLog).filter_by(entity_type='report',entity_id=item['id']).count()==1

def test_matching_confidence_and_token_password_helpers():
    from types import SimpleNamespace
    from datetime import datetime, timezone
    from app.features.matching.service import score_match
    a=SimpleNamespace(category='Keys',description='silver keyring with blue tag',location='Library',occurred_at=datetime.now(timezone.utc))
    b=SimpleNamespace(category='Keys',description='silver keyring with blue tag',location='Library',occurred_at=datetime.now(timezone.utc))
    assert score_match(a,b)['confidence']=='High'
    encoded=hash_password('a secure password')
    from app.features.auth.service import verify_password
    assert verify_password('a secure password',encoded)
    assert not verify_password('incorrect',encoded)

def test_admin_endpoint_rejects_student():
    token=register()
    response=client.get('/api/v1/admin/reports/pending',headers={'Authorization':f'Bearer {token}'})
    assert response.status_code==403
    assert client.get('/api/v1/admin/claims/pending',headers={'Authorization':f'Bearer {token}'}).status_code==403
    assert client.get('/api/v1/admin/recoveries',headers={'Authorization':f'Bearer {token}'}).status_code==403
    assert client.get('/api/v1/admin/audit',headers={'Authorization':f'Bearer {token}'}).status_code==403

def test_claim_requires_matched_state_and_only_admin_can_decide():
    owner_token=register('custodian@example.edu')
    found=client.post('/api/v1/reports/found',headers={'Authorization':f'Bearer {owner_token}'},data={'item_name':'Blue notebook','category':'Stationery','description':'Green sticker on back','occurred_at':'2026-10-14T10:00:00','location':'Cafeteria','contact_email':'custodian@example.edu','custody_location':'Reception'})
    item_id=found.json()['id']
    claimant_token=register('claimant@example.edu'); claimant_headers={'Authorization':f'Bearer {claimant_token}'}
    early_claim=client.post(f'/api/v1/items/{item_id}/claims',headers=claimant_headers,files={'file':('proof.pdf',b'%PDF-1.4\nevidence','application/pdf')})
    assert early_claim.status_code==404
    with TestingSession() as db:
        db.query(__import__('app.models',fromlist=['ItemReport']).ItemReport).filter_by(id=item_id).one().status='Match Found'; db.commit()
        db.query(__import__('app.models',fromlist=['FoundReport']).FoundReport).filter_by(report_id=item_id).one().status='Match Found'; db.commit()
    claim=client.post(f'/api/v1/items/{item_id}/claims',headers=claimant_headers,files={'file':('proof.pdf',b'%PDF-1.4\nevidence','application/pdf')})
    assert claim.status_code==201
    assert client.get(f'/api/v1/items/{item_id}').json()['status']=='Claim Requested'
    owner_headers={'Authorization':f'Bearer {owner_token}'}
    owner_notices=client.get('/api/v1/notifications',headers=owner_headers).json()
    assert any('claim was submitted' in row['message'] for row in owner_notices)
    notification=next(row for row in owner_notices if 'claim was submitted' in row['message'])
    outsider_token=register('outsider@example.edu')
    assert client.post(f"/api/v1/notifications/{notification['id']}/read",headers={'Authorization':f'Bearer {outsider_token}'}).status_code==404
    decision=client.post(f"/api/v1/claims/{claim.json()['id']}/decision",headers=owner_headers,json={'decision':'approve','comment':'Verified'})
    assert decision.status_code==403
    admin_token=register('reviewer@example.edu')
    with TestingSession() as db: db.query(User).filter_by(email='reviewer@example.edu').one().role='Administrator'; db.commit()
    admin_headers={'Authorization':f'Bearer {admin_token}'}
    decision=client.post(f"/api/v1/claims/{claim.json()['id']}/decision",headers=admin_headers,json={'decision':'approve','comment':'Verified'})
    assert decision.status_code==200 and decision.json()['status']=='Approved for Return'
    assert client.get(f'/api/v1/items/{item_id}',headers=owner_headers).json()['status']=='Approved for Return'
    handoff=client.post(f'/api/v1/items/{item_id}/status',headers=owner_headers,json={'status':'Returned'})
    assert handoff.status_code==200
    assert client.post(f'/api/v1/items/{item_id}/close',headers=owner_headers).status_code==403
    assert client.post(f'/api/v1/items/{item_id}/close',headers=admin_headers).json()['status']=='Closed'
    notices=client.get('/api/v1/notifications',headers=claimant_headers).json()
    assert any('Approved for Return' in row['message'] for row in notices)
    unread=next(row for row in notices if 'Approved for Return' in row['message'])
    marked=client.post(f"/api/v1/notifications/{unread['id']}/read",headers=claimant_headers)
    assert marked.json()['read'] is True

def test_report_validation_and_invalid_status_transition():
    token=register('validation@example.edu'); headers={'Authorization':f'Bearer {token}'}
    invalid=client.post('/api/v1/reports/found',headers=headers,data={'item_name':'Test','category':'Other','description':'Test','occurred_at':'not-a-date','location':'Hall','contact_email':'not-an-email'})
    assert invalid.status_code==422
    found=client.post('/api/v1/reports/found',headers=headers,data={'item_name':'Test','category':'Other','description':'Test','occurred_at':'2026-10-14T10:00:00','location':'Hall','contact_email':'validation@example.edu','custody_location':'Office'})
    item_id=found.json()['id']
    response=client.post(f"/api/v1/items/{item_id}/status",headers=headers,json={'status':'returned'})
    assert response.status_code==409
    with TestingSession() as db:
        from app.models import ItemReport, AuditLog
        db.query(ItemReport).filter_by(id=item_id).one().status='Approved for Return'; db.commit()
    changed=client.post(f'/api/v1/items/{item_id}/status',headers=headers,json={'status':'Returned'})
    assert changed.status_code==200 and changed.json()['status']=='Returned'
    with TestingSession() as db:
        from app.models import StatusHistory
        assert db.query(StatusHistory).filter_by(entity_type='report',entity_id=item_id,new_status='Returned').count()==1

def test_claim_proof_is_private_to_claimant_report_owner_and_admin(tmp_path,monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings,'upload_dir',str(tmp_path/'uploads'))
    owner_token=register('proof-owner@example.edu')
    response=client.post('/api/v1/reports/found',headers={'Authorization':f'Bearer {owner_token}'},data={'item_name':'Silver ring','category':'Jewelry','description':'Small engraved mark','occurred_at':'2026-10-14T10:00:00','location':'Gym','contact_email':'proof-owner@example.edu','custody_location':'Gym desk'})
    item_id=response.json()['id']
    with TestingSession() as db:
        from app.models import ItemReport
        db.query(ItemReport).filter_by(id=item_id).one().status='Match Found'; db.commit()
        db.query(__import__('app.models',fromlist=['FoundReport']).FoundReport).filter_by(report_id=item_id).one().status='Match Found'; db.commit()
    claimant_token=register('proof-claimant@example.edu'); claimant_headers={'Authorization':f'Bearer {claimant_token}'}
    invalid=client.post(f'/api/v1/items/{item_id}/claims',headers=claimant_headers,files={'file':('bad.pdf',b'not a pdf','application/pdf')})
    assert invalid.status_code==415
    assert client.get(f'/api/v1/items/{item_id}').json()['status']=='Match Found'
    claim=client.post(f'/api/v1/items/{item_id}/claims',headers=claimant_headers,files={'file':('evidence.pdf',b'%PDF-1.4\nprivate evidence', 'application/pdf')})
    assert claim.status_code==201
    proof_path=f"/api/v1/claims/{claim.json()['id']}/proof"
    assert client.get(proof_path,headers=claimant_headers).status_code==200
    assert client.get(proof_path,headers={'Authorization':f'Bearer {owner_token}'}).status_code==404
    outsider_token=register('proof-outsider@example.edu')
    assert client.get(proof_path,headers={'Authorization':f'Bearer {outsider_token}'}).status_code==404
    admin_token=register('proof-admin@example.edu')
    with TestingSession() as db:
        db.query(User).filter_by(email='proof-admin@example.edu').one().role='Administrator'; db.commit()
    assert client.get(proof_path,headers={'Authorization':f'Bearer {admin_token}'}).status_code==200


def test_approval_persists_high_match_notifies_both_report_owners_and_records_audit():
    from app.models import AuditEvent, FoundReport, LostReport, Match, Notification, ItemReport
    admin_token=register('match-admin@example.edu')
    with TestingSession() as db:
        db.query(User).filter_by(email='match-admin@example.edu').one().role='Administrator'; db.commit()
    lost_owner=register('lost-owner@example.edu')
    found_owner=register('found-owner@example.edu')
    lost=client.post('/api/v1/reports/lost',headers={'Authorization':f'Bearer {lost_owner}'},data={
        'item_name':'Silver keys','category':'Keys','description':'Silver keys with a blue star tag',
        'occurred_at':'2026-10-14T10:00:00','location':'Main Library','contact_email':'lost-owner@example.edu'})
    found=client.post('/api/v1/reports/found',headers={'Authorization':f'Bearer {found_owner}'},data={
        'item_name':'Keys found','category':'Keys','description':'Silver keys with a blue star tag',
        'occurred_at':'2026-10-14T11:00:00','location':'Main Library','contact_email':'found-owner@example.edu',
        'custody_location':'Library desk'})
    assert lost.status_code==201 and found.status_code==201
    admin_headers={'Authorization':f'Bearer {admin_token}'}
    first=client.post(f"/api/v1/admin/reports/{lost.json()['id']}/decision",headers=admin_headers,json={'decision':'approve'})
    second=client.post(f"/api/v1/admin/reports/{found.json()['id']}/decision",headers=admin_headers,json={'decision':'approve'})
    assert first.json()['status']=='Active' and second.json()['status']=='Match Found'
    with TestingSession() as db:
        assert db.query(Match).filter_by(lost_report_id=lost.json()['id'],found_report_id=found.json()['id'],confidence='High').count()==1
        assert db.get(LostReport,lost.json()['id']).status=='Match Found'
        assert db.get(FoundReport,found.json()['id']).status=='Match Found'
        assert db.query(AuditEvent).filter_by(entity_type='report').count()>=3
    lost_notices=client.get('/api/v1/notifications',headers={'Authorization':f'Bearer {lost_owner}'}).json()
    found_notices=client.get('/api/v1/notifications',headers={'Authorization':f'Bearer {found_owner}'}).json()
    assert any('high-confidence' in row['message'] for row in lost_notices)
    assert any('high-confidence' in row['message'] for row in found_notices)
    with TestingSession() as db:
        assert db.query(Notification).filter(Notification.type=='match',Notification.delivery_status=='Sent').count()==2
        assert db.query(ItemReport).filter(ItemReport.status=='Pending Approval').count()==0


def test_rejected_claim_restores_match_found_and_audits_the_state_change():
    from app.models import ItemReport, StatusHistory
    owner=register('reject-owner@example.edu')
    report=client.post('/api/v1/reports/found',headers={'Authorization':f'Bearer {owner}'},data={
        'item_name':'Blue water bottle','category':'Bottle','description':'Blue bottle with a small scratch',
        'occurred_at':'2026-10-14T10:00:00','location':'Gym','contact_email':'reject-owner@example.edu',
        'custody_location':'Gym front desk'})
    item_id=report.json()['id']
    with TestingSession() as db:
        db.get(ItemReport,item_id).status='Match Found'
        db.get(__import__('app.models',fromlist=['FoundReport']).FoundReport,item_id).status='Match Found'
        db.commit()
    claimant=register('reject-claimant@example.edu')
    claim=client.post(f'/api/v1/items/{item_id}/claims',headers={'Authorization':f'Bearer {claimant}'},
        files={'file':('proof.pdf',b'%PDF-1.4\nproof','application/pdf')})
    admin=register('reject-admin@example.edu')
    with TestingSession() as db: db.query(User).filter_by(email='reject-admin@example.edu').one().role='Administrator'; db.commit()
    response=client.post(f"/api/v1/claims/{claim.json()['id']}/decision",headers={'Authorization':f'Bearer {admin}'},
        json={'decision':'reject','comment':'The identifying detail did not match.'})
    assert response.status_code==200 and response.json()['status']=='Rejected'
    assert client.get(f'/api/v1/items/{item_id}').json()['status']=='Match Found'
    with TestingSession() as db:
        assert db.query(StatusHistory).filter_by(entity_type='report',entity_id=item_id,old_status='Claim Requested',new_status='Match Found').count()==1
        assert db.query(StatusHistory).filter_by(entity_type='claim',new_status='Rejected').count()==1


def test_report_rejection_requires_reason_is_hidden_and_audited():
    from app.models import AuditLog, ItemReport
    reporter=register('rejected-report@example.edu')
    admin=register('reject-report-admin@example.edu')
    with TestingSession() as db:
        db.query(User).filter_by(email='reject-report-admin@example.edu').one().role='Administrator'; db.commit()
    report=client.post('/api/v1/reports/lost',headers={'Authorization':f'Bearer {reporter}'},data={
        'item_name':'Black umbrella','category':'Umbrella','description':'Wooden handle',
        'occurred_at':'2026-10-14T10:00:00','location':'Lecture Hall','contact_email':'rejected-report@example.edu'})
    url=f"/api/v1/admin/reports/{report.json()['id']}/decision"
    headers={'Authorization':f'Bearer {admin}'}
    assert client.post(url,headers=headers,json={'decision':'reject'}).status_code==422
    rejected=client.post(url,headers=headers,json={'decision':'reject','comment':'Insufficient report details.'})
    assert rejected.status_code==200 and rejected.json()['status']=='Rejected'
    assert client.get(f"/api/v1/items/{report.json()['id']}").status_code==404
    assert all(row['id']!=report.json()['id'] for row in client.get('/api/v1/items').json()['items'])
    with TestingSession() as db:
        row=db.get(ItemReport,report.json()['id'])
        assert row.moderation_comment=='Insufficient report details.'
        assert db.query(AuditLog).filter_by(entity_type='report',entity_id=row.id,detail='Insufficient report details.').count()==1
