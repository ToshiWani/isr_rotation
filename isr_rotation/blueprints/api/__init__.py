from flask import Blueprint, request, jsonify
import isr_rotation.mailer as mailer
from isr_rotation import database as db

bp = Blueprint('api', __name__)


@bp.route('/get_user', methods=['POST'])
def get_user():
    if request.is_json:
        req = request.get_json()
        response = []
        for i, user in enumerate(req['off_duty']):
            result = db.update_rotation(user, False, -1)
            response.append({user: result.raw_result})

        for i, user in enumerate(req['on_duty']):
            result = db.update_rotation(user, True, i)
            response.append({user: result.raw_result})

    return jsonify(response)


