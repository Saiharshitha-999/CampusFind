from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import current_user
from app.db.session import get_db
from app.models import User
from app.features.auth.schemas import RegistrationRequest, LoginRequest, TokenResponse, TokenRequest, PasswordResetRequest, PasswordResetConfirm
from app.features.auth.service import hash_password, verify_password, create_token, read_token
from app.features.notifications.service import send_email
from urllib.parse import urlencode

router = APIRouter()
def public_user(user): return {'user_id': user.id, 'id': user.id, 'name': user.display_name,
                               'email': user.email, 'display_name': user.display_name,
                               'role': user.role, 'verification_status': user.verification_status,
                               'verified': user.verified, 'active': user.active}

def frontend_link(path: str, token: str) -> str:
    return f"{settings.frontend_origin.rstrip('/')}{path}?{urlencode({'token': token})}"

def email_setup_message() -> str:
    if settings.app_env.lower() == 'development':
        return 'Email is not configured for this local app. Add SMTP settings to CampusFind_Project_Structure/.env and restart the backend.'
    return 'Email delivery is temporarily unavailable. Please try again later.'

@router.post('/register', status_code=201)
def register(body: RegistrationRequest, db: Session = Depends(get_db)):
    email = str(body.email).lower()
    if db.query(User).filter_by(email=email).first(): raise HTTPException(409, 'Email is already registered')
    user = User(email=email, display_name=body.display_name, password_hash=hash_password(body.password))
    db.add(user); db.flush()
    token = create_token(user.id, 'verify', 86400)
    verify_url = frontend_link('/verify-email', token)
    delivered = send_email(user.email, 'Verify your CampusFind account',
                           f"Welcome to CampusFind. Verify your email by opening this link:\n\n{verify_url}\n\nThis link expires in 24 hours.")
    if not delivered:
        db.rollback()
        raise HTTPException(503, email_setup_message())
    db.commit(); db.refresh(user)
    return {'user': public_user(user), 'message': 'Check your email for a link to verify your account.'}

@router.post('/verify-email')
def verify_email(body: TokenRequest, db: Session = Depends(get_db)):
    user_id = read_token(body.token, 'verify'); user = db.get(User, user_id) if user_id else None
    if not user: raise HTTPException(400, 'Verification token is invalid or expired')
    user.verified = True; user.verification_status = 'Verified'; db.commit()
    return {'message': 'Email verified. You can now sign in.'}

@router.post('/verification/request')
def request_verification(body: PasswordResetRequest, db: Session = Depends(get_db)):
    if not (settings.smtp_host and settings.smtp_from_email):
        raise HTTPException(503, email_setup_message())
    user = db.query(User).filter_by(email=str(body.email).lower()).first()
    if user and not user.verified:
        token = create_token(user.id, 'verify', 86400)
        verify_url = frontend_link('/verify-email', token)
        if not send_email(user.email, 'Verify your CampusFind account',
                          f"Verify your CampusFind account by opening this link:\n\n{verify_url}\n\nThis link expires in 24 hours."):
            raise HTTPException(503, email_setup_message())
    return {'message': 'If an unverified account exists for that email, a verification link has been sent.'}

@router.post('/login', response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=str(body.email).lower()).first()
    if not user or not verify_password(body.password, user.password_hash): raise HTTPException(401, 'Email or password is incorrect')
    if not user.active: raise HTTPException(403, 'This account has been deactivated')
    if not user.verified: raise HTTPException(403, 'Verify your email before signing in')
    return {'access_token': create_token(user.id), 'user': public_user(user)}

@router.get('/me')
def me(user: User = Depends(current_user)): return public_user(user)

@router.post('/password-reset/request')
def reset_request(body: PasswordResetRequest, db: Session = Depends(get_db)):
    if not (settings.smtp_host and settings.smtp_from_email):
        raise HTTPException(503, email_setup_message())
    user = db.query(User).filter_by(email=str(body.email).lower()).first()
    result = {'message': 'If the account exists, reset instructions have been sent.'}
    if user:
        token = create_token(user.id, 'reset', 3600)
        reset_url = frontend_link('/password-reset/confirm', token)
        send_email(user.email, 'CampusFind password reset',
                   f"Reset your CampusFind password by opening this link:\n\n{reset_url}\n\nThis link expires in one hour.")
    return result

@router.post('/password-reset/confirm')
def reset_confirm(body: PasswordResetConfirm, db: Session = Depends(get_db)):
    user_id = read_token(body.token, 'reset'); user = db.get(User, user_id) if user_id else None
    if not user: raise HTTPException(400, 'Reset token is invalid or expired')
    user.password_hash = hash_password(body.password); db.commit()
    return {'message': 'Password updated. Sign in with your new password.'}
