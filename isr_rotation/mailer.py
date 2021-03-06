from flask import current_app
from flask_mail import Mail, Message
from isr_rotation import database as db
from string import Template
from datetime import datetime


mail = Mail()


def send():
    try:
        current_user = db.get_current_user()
        if current_user is None:
            raise LookupError('No current user was found')

        users = db.get_all_user()
        recipients = list(map(lambda u: u.get('email'), users))

        settings = _get_email_settings()
        placeholders = get_email_placeholders()

        body_template = Template('' if settings.get('body') is None else settings.get('body'))
        body = body_template.safe_substitute(placeholders)

        subject_template = Template('' if settings.get('subject') is None else settings.get('subject'))
        subject = subject_template.safe_substitute(placeholders)

        msg = Message(
            recipients=recipients,
            body=body,
            subject=subject,
            sender=settings.get('from_mail')
        )

        # None seems meaning "success"
        result = mail.send(msg)
        log_msg = f'Email has been sent. Subject: "{subject}"'
        current_app.logger.info(log_msg)
        return result

    except LookupError as e:
        current_app.logger.critical(e.args)

    except Exception as e:
        current_app.logger.critical('Failed to send notification email')
        raise e


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


def get_email_placeholders() -> dict:
    current_user = db.get_current_user()
    display_name = current_user.get('display_name', '') if current_user else ''
    return {
        'display_name': display_name,
        'timestamp': datetime.now().strftime('%b %d, %Y %X %Z')
    }


def _get_email_settings():
    return db.get_email_settings()

