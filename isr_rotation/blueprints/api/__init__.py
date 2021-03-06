from flask import Blueprint, request, jsonify, abort, current_app
from datetime import datetime
import isr_rotation.mailer as mailer
from isr_rotation import database as db


bp = Blueprint('api', __name__)


@bp.route('/rotation', methods=['POST'])
def save_rotation():
    response = []
    summary = []
    if request.is_json:
        req = request.get_json()
        for i, user in enumerate(req['inactive_users']):
            result = db.update_rotation(user, False, -1)
            response.append({user: result.raw_result})
            summary.append({user: {'state': 'inactive'}})

        for i, user in enumerate(req['active_users']):
            result = db.update_rotation(user, True, i)
            response.append({user: result.raw_result})
            summary.append({user: {'state': 'active', 'seq': i}})

    #   Reset current rotation
    db.set_current_rotation(0)

    log_msg = f'Rotation order has been updated.  {summary}'
    current_app.logger.info(log_msg)

    return jsonify(summary)


@bp.route('/users/<email>', methods=['DELETE'])
def delete_user(email):
    result = {}
    if email:
        result = db.delete_user(email).raw_result
        log_msg = f'The user ({email}) has been deleted'
        current_app.logger.info(log_msg)

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
    # Is today holiday?
    if db.is_holiday_now():
        current_app.logger.info('Today is holiday')
        return jsonify({'status': 'skipped', 'message': 'Today is holiday'})

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


@bp.route('/logs', methods=['DELETE'])
def purge_log():
    """
    GET: /logs?days_old=365
    :return: json
    """
    try:
        days_old = request.args.get('days_old', default=0, type=int)
        rows = db.purge_log(days_old)
        return jsonify({'status': 'ok', 'rows_affected': rows})
    except Exception as e:
        msg = ', '.join(e.args)
        return jsonify({'status': 'ok', 'message': msg})


def _encoding_mongo(mongo_obj):
    result = []
    for kvp in mongo_obj:
        if '_id' in kvp:
            kvp['_id'] = str(kvp['_id'])
            result.append(kvp)
    return result

