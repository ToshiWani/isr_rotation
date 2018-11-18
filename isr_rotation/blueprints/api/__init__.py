from flask import Blueprint, request, jsonify, abort, current_app
from datetime import datetime
import isr_rotation.mailer as mailer
from isr_rotation import database as db


bp = Blueprint('api', __name__)

#
# TODO: Rename end points for complying REST naming conventions
#


@bp.route('/users', methods=['POST'])
def get_user():
    response = []

    if request.is_json:
        req = request.get_json()
        for i, user in enumerate(req['inactive_users']):
            result = db.update_rotation(user, False, -1)
            response.append({user: result.raw_result})

        for i, user in enumerate(req['active_users']):
            result = db.update_rotation(user, True, i)
            response.append({user: result.raw_result})

    #   Reset current rotation
    db.set_current_rotation(0)

    return jsonify(response)


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


@bp.route('/users/<email>/vacations/<vacation_hash>', methods=['DELETE'])
def delete_vacation(email, vacation_hash):
    user = db.get_user(email)
    if user is None:
        abort(500)

    result = db.delete_vacation(email, vacation_hash)

    return jsonify({'status': 'ok', 'modified_count': result.modified_count})


@bp.route('/move-next', methods=['POST'])
def move_next():
    # Is today weekend?
    if datetime.today().weekday() in [5, 6] and not current_app.config.get('ENABLE_WEEKEND'):
        current_app.logger.info('Today is weekend')
        return jsonify({'status': 'skipped', 'message': 'Today is weekend'})

    # Any active users?
    if db.count_on_duty_users() == 0:
        current_app.logger.info('No active users found')
        return jsonify({'status': 'skipped', 'message': 'No active users found'})

    # Is everyone vacation?
    if db.is_everyone_on_vacation():
        current_app.logger.info('All active users are vacation')
        return jsonify({'status': 'skipped', 'message': 'All active users are vacation'})

    try:
        db.move_next()
        current_app.logger.info('Moved to the next person')

        # None seems meaning "success"
        result = mailer.send()
        return jsonify({'status': 'ok', 'message': result})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(type(e))}), 500


@bp.route('/email/resend', methods=['POST'])
def resend_email():
    try:
        # Any active users?
        if db.count_on_duty_users() == 0:
            current_app.logger.info('No active users found')
            return jsonify({'status': 'skipped', 'message': 'No active users found'})

        # Is everyone vacation?
        if db.is_everyone_on_vacation():
            current_app.logger.info('All active users are vacation')
            return jsonify({'status': 'skipped', 'message': 'All active users are vacation'})

        result = mailer.send()
        return jsonify({'status': 'ok', 'message': result})
    except Exception as e:
        return jsonify({'status': 'ok', 'message': str(type(e))})


def _encoding_mongo(mongo_obj):
    result = []
    for kvp in mongo_obj:
        if '_id' in kvp:
            kvp['_id'] = str(kvp['_id'])
            result.append(kvp)
    return result
