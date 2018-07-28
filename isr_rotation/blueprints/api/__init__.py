from flask import Blueprint, request
import isr_rotation.mailer as mailer

bp = Blueprint('api', __name__)


@bp.route('/get_user')
def get_user():
    return 'ok'


