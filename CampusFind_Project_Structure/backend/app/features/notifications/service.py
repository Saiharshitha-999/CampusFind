import smtplib
import logging
from email.message import EmailMessage
from app.core.config import settings
from app.models import Notification

logger = logging.getLogger(__name__)

def notify(db, user_id, message, email=None, notification_type='general'):
    notice = Notification(recipient_id=user_id, type=notification_type, message=message,
                          delivery_status='Pending')
    db.add(notice)
    # Flush all pending report, audit, and notification writes before sending
    # email. This prevents a database constraint error from producing a false
    # "approved" email while rolling back the actual report decision.
    db.flush()
    if email and settings.smtp_host and settings.smtp_from_email:
        try:
            mail = EmailMessage(); mail['Subject']='CampusFind update'; mail['From']=settings.smtp_from_email; mail['To']=email; mail.set_content(message)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=8) as smtp:
                if settings.smtp_starttls: smtp.starttls()
                if settings.smtp_username: smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(mail)
            notice.delivery_status = 'Sent'
        except Exception:
            # Persist the in-app notification even when mail delivery is temporarily unavailable.
            notice.delivery_status = 'Failed'
            logger.exception('Could not deliver notification email')

def send_email(email, subject, message):
    if not (settings.smtp_host and settings.smtp_from_email):
        logger.error('Email delivery is not configured; account email was not sent')
        return False
    try:
        mail=EmailMessage(); mail['Subject']=subject; mail['From']=settings.smtp_from_email; mail['To']=email; mail.set_content(message)
        with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=8) as smtp:
            if settings.smtp_starttls: smtp.starttls()
            if settings.smtp_username: smtp.login(settings.smtp_username,settings.smtp_password)
            smtp.send_message(mail)
        return True
    except Exception:
        logger.exception('Could not deliver account email')
        return False
