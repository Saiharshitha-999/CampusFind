"""Create an administrator interactively: python -m app.create_admin"""
from getpass import getpass
from app.db.session import SessionLocal
from app.models import User
from app.features.auth.service import hash_password

def main():
    email=input('Administrator email: ').strip().lower()
    name=input('Display name: ').strip()
    password=getpass('Password (minimum 12 characters): ')
    if len(password)<12: raise SystemExit('Password must contain at least 12 characters')
    with SessionLocal() as db:
        if db.query(User).filter_by(email=email).first(): raise SystemExit('That email already exists')
        db.add(User(email=email,display_name=name,password_hash=hash_password(password),role='Administrator',verified=True,active=True))
        db.commit()
    print('Administrator created.')

if __name__=='__main__': main()
