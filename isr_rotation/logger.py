import database as db
from isr_rotation import app


class Logger:

    @staticmethod
    def debug(message):
        log_level = app.config['LOG_LEVEL'] if 'LOG_LEVEL' in app.config else ''
        if log_level == 'DEBUG':
            db.write_log('DEBUG', message)
        print message

    @staticmethod
    def info(message):
        log_level = app.config['LOG_LEVEL'] if 'LOG_LEVEL' in app.config else 'INFO'
        if log_level == 'INFO':
            db.write_log('INFO', message)
        print message

    @staticmethod
    def error(message):
        db.write_log('ERROR', message)
        print message

