"""Create local demo accounts and a lost/found report pair.

Supply SEED_ADMIN_EMAIL/PASSWORD and SEED_USER1_EMAIL/PASSWORD and
SEED_USER2_EMAIL/PASSWORD in the local shell environment before running.
Existing users and reports are never changed or deleted.
"""
import os
from datetime import date, datetime
from sqlalchemy import text
from app.db.session import SessionLocal
from app.features.auth.service import hash_password
from app.models import FoundReport, ItemReport, LostReport, User


def required_env(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise SystemExit(f"Set {name} in your local environment before running the seed command.")
    return value


def get_or_create_user(db, email, name, password, role):
    user = db.query(User).filter_by(email=email.lower()).one_or_none()
    if user:
        if role == 'Administrator' and user.role != 'Administrator':
            raise SystemExit(f"{email} already exists without the Administrator role; no account was changed.")
        return user
    if len(password) < 12:
        raise SystemExit(f"Seed password for {email} must be at least 12 characters.")
    user = User(email=email.lower(), display_name=name, password_hash=hash_password(password),
                role=role, verification_status='Verified', active=True)
    db.add(user); db.flush()
    return user


def main():
    admin = (required_env('SEED_ADMIN_EMAIL'), required_env('SEED_ADMIN_PASSWORD'), 'Campus Administrator', 'Administrator')
    first = (required_env('SEED_USER1_EMAIL'), required_env('SEED_USER1_PASSWORD'), 'Demo Lost Reporter', 'Campus User')
    second = (required_env('SEED_USER2_EMAIL'), required_env('SEED_USER2_PASSWORD'), 'Demo Finder', 'Campus User')
    with SessionLocal() as db:
        get_or_create_user(db, admin[0], admin[2], admin[1], admin[3])
        lost_owner = get_or_create_user(db, first[0], first[2], first[1], first[3])
        found_owner = get_or_create_user(db, second[0], second[2], second[1], second[3])
        db.flush()
        today = date.today()
        examples = [
            ('lost', lost_owner, 'Silver keys with blue tag', 'Main Library'),
            ('found', found_owner, 'Silver keys with blue tag', 'Main Library'),
        ]
        for kind, owner, description, location in examples:
            if db.query(ItemReport).filter_by(owner_id=owner.id, kind=kind, item_name=description).first():
                continue
            row = ItemReport(owner_id=owner.id, kind=kind, item_name=description, category='Keys',
                             description='Silver keyring with a small blue star tag.',
                             occurred_at=datetime.combine(today, datetime.min.time()), location=location,
                             contact_email=owner.email, custody_location='Library reception' if kind == 'found' else None,
                             status='Pending Approval')
            db.add(row); db.flush()
            if kind == 'lost':
                db.add(LostReport(report_id=row.id, owner_id=owner.id, category=row.category,
                                  description=row.description, location=row.location, date_lost=today,
                                  status=row.status))
                table = 'lost_reports'
            else:
                db.add(FoundReport(report_id=row.id, finder_id=owner.id, category=row.category,
                                   description=row.description, found_location=row.location, date_found=today,
                                   custody_location=row.custody_location, status=row.status))
                table = 'found_reports'
            if db.bind.dialect.name == 'postgresql':
                db.flush()
                db.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}','report_id'), GREATEST((SELECT COALESCE(MAX(report_id),1) FROM {table}),1), true)"))
        db.commit()
    print('Seed accounts and sample reports are ready. Existing records were left unchanged.')


if __name__ == '__main__':
    main()
