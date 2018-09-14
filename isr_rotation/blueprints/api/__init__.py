from flask import Blueprint, request, jsonify
import isr_rotation.mailer as mailer
from isr_rotation import database as db

bp = Blueprint('api', __name__)


@bp.route('/get_user', methods=['POST'])
def get_user():
    response = []

    if request.is_json:
        req = request.get_json()
        for i, user in enumerate(req['off_duty']):
            result = db.update_rotation(user, False, -1)
            response.append({user: result.raw_result})

        for i, user in enumerate(req['on_duty']):
            result = db.update_rotation(user, True, i)
            response.append({user: result.raw_result})

    return jsonify(response)


@bp.route('/move_next', methods=['POST'])
def move_next():
    response = db.move_next()
    if request.is_json:
        req = request.get_json()
    data = {'users': _encoding_mongo(response)}
    return jsonify(data)


@bp.route('/user/delete', methods=['POST'])
def delete_user():
    result = {}
    if request.is_json:
        data = request.get_json()
        email = data.get('email')
        if email:
            result = db.delete_user(email).raw_result
    return jsonify(result)


@bp.route('/holiday/delete', methods=['POST'])
def delete_holiday():
    result = {}
    if request.is_json:
        data = request.get_json()
        holiday_id = data.get('holiday_id')
        if holiday_id:
            result = db.delete_holiday(holiday_id).raw_result
    return jsonify(result)



def _encoding_mongo(mongo_obj):
    result = []
    for kvp in mongo_obj:
        if '_id' in kvp:
            kvp['_id'] = str(kvp['_id'])
            result.append(kvp)
    return result
