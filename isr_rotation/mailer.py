from flask_mail import Mail, Message
from isr_rotation import database as db

mail = Mail()


def send():
    settings = db.get_email_settings()
    users = db.get_all_user()
    recipients = list(map(lambda u: u.get('email'), users))
    msg = Message(
        recipients=recipients,
        body=settings.get('body'),
        subject=settings.get('subject'),
        sender=settings.get('from_mail')
    )

    # None seems meaning "success"
    return mail.send(msg)
