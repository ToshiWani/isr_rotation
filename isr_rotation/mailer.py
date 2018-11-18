from flask_mail import Mail, Message
from isr_rotation import database as db

mail = Mail()


def send():
    current_user = db.get_current_user()

    if current_user is None:
        return 'No Active Users'

    settings = db.get_email_settings()
    users = db.get_all_user()
    recipients = list(map(lambda u: u.get('email'), users))


    placeholders = {
        'display_name': current_user.get('display_name')
    }

    body = '' if settings.get('body') is None else settings.get('body').format_map(placeholders)
    subject = '' if settings.get('subject') is None else settings.get('subject').format_map(placeholders)

    msg = Message(
        recipients=recipients,
        body=body,
        subject=subject,
        sender=settings.get('from_mail')
    )

    # None seems meaning "success"
    return mail.send(msg)
