from datetime import datetime

import requests
from mailjet_rest import Client

import isr_rotation.database as db
from isr_rotation.logger import Logger
from isr_rotation import app


def _send_email(preview_only=False, ignore_weekend=False):
    """
    Send email
    :param preview_only: True to preview
    :return: True for success
    """

    if not ignore_weekend and datetime.today().weekday() > 4:  # 0=Monday, 6=Sunday
        Logger.info('Not sending an email - Today is a weekend.')
        return False

    if db.is_holiday():
        Logger.info('Not sending an email - Today is holiday.')
        return False

    config = db.get_config()

    from_name = config.email_from_name
    from_email = config.email_from_address
    req = requests.get('https://api.ipify.org?format=json')
    ip = req.json()['ip'] if req.ok else '0.0.0.0'

    if db.count_on_duty() == 0:
        subject = 'No one is in charge of IS Request today'
        msg = 'No one is in charge of IS Request today. Manage user from here http://{ip}'.format(ip=ip)
    else:
        onduty_user = db.get_on_duty_user()
        to_name = onduty_user.name
        subject = config.email_subject.format(name=to_name)
        msg = config.email_body.format(name=to_name, ip=ip)

    email = {
        'FromName': from_name,
        'FromEmail': from_email,
        'Subject': subject,
        'Text-Part': msg,
        'To': ', '.join(e.email for e in db.get_all_email())
    }

    Logger.info('Sending an email. Data => {}'.format(email))

    if preview_only:
        return True

    mailjet = Client(auth=(app.config.get('EMAIL_API_KEY'), app.config.get('EMAIL_API_SECRET')))
    res = mailjet.send.create(email)
    if res.ok:
        Logger.info('Sent an email successfully')
    else:
        Logger.info('Error occurred while sending an email. Data => {}', res)

    return res.ok


def send(preview_only=False):
    result = _send_email(preview_only)
    # result = _send_email(True, True)
    if result:
        db.move_next()
    return result


def resend(preview_only=False):
    return _send_email(preview_only)
    # return _send_email(True, True)


def move_next(preview_only=False):
    db.move_next()
    result = _send_email(preview_only)
    # result = _send_email(True, True)
    return result

