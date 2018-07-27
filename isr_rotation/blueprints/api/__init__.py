from flask import Blueprint, request
from isr_rotation import database as db

bp = Blueprint('api', __name__)


@bp.route('/get_user')
def get_user():
    return 'ok'




