from flask import request
from flask_mail import Mail, Message
from isr_rotation import database as db
from string import Template

mail = Mail()


def send():
    current_user = db.get_current_user()
    if current_user is None:
        return 'No Active Users'

    users = db.get_all_user()
    recipients = list(map(lambda u: u.get('email'), users))

    settings = _get_email_settings()

    body_template = Template('' if settings.get('body') is None else settings.get('body'))
    body = body_template.safe_substitute(get_email_placeholders())

    subject_template = Template('' if settings.get('subject') is None else settings.get('subject'))
    subject = subject_template.safe_substitute(get_email_placeholders())

    msg = Message(
        recipients=recipients,
        body=body,
        subject=subject,
        sender=settings.get('from_mail')
    )

    # None seems meaning "success"
    return mail.send(msg)


def send_custom(recipients, subject, body):
    settings = _get_email_settings()
    msg = Message(
        recipients=recipients,
        body=body,
        subject=subject,
        sender=settings.get('from_mail')
    )

    # None seems meaning "success"
    return mail.send(msg)


def get_email_placeholders():
    current_user = db.get_current_user()
    return {
        'display_name': current_user.get('display_name'),
        'app_url': request.host_url
    }


def _get_email_settings():
    return db.get_email_settings()

