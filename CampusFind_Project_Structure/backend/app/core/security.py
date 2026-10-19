from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.features.auth.service import read_token

bearer = HTTPBearer(auto_error=False)
def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    user_id = read_token(credentials.credentials) if credentials else None
    user = db.get(User, user_id) if user_id else None
    if not user or not user.active: raise HTTPException(401, 'Valid login required')
    return user
def optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User | None:
    user_id = read_token(credentials.credentials) if credentials else None
    user = db.get(User, user_id) if user_id else None
    return user if user and user.active and user.verified else None
def verified_user(user: User = Depends(current_user)) -> User:
    if not user.verified: raise HTTPException(403, 'Verify your email before continuing')
    return user
def admin_user(user: User = Depends(verified_user)) -> User:
    if user.role != 'Administrator': raise HTTPException(403, 'Administrator access required')
    return user
