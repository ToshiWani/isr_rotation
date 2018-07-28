from flask_mail import Mail, Message

mail = Mail()


def send(recipients, subject, message):
    msg = Message(recipients=recipients, body=message, subject=subject)
    return mail.send(msg)


