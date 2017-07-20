from datetime import datetime, timedelta

from flask import Blueprint, request, redirect, render_template, jsonify

import isr_rotation.database as db
from isr_rotation.models import User, Vacation
from isr_rotation.logger import Logger

bp = Blueprint('rotation_app', __name__)


# region Pages


@bp.route('/')
def default():
    users = db.get_all_users()
    return render_template('default.html', users=sorted(users, key=lambda k: k.seq))


@bp.route('/log')
def log():
    logs = db.get_log()
    return render_template('log.html', model=logs)


@bp.route('/vacation/<userid>', methods=['GET'])
def vacation(userid):
    query = Vacation.query.filter(Vacation.userid == userid).all()
    user = db.get_user_by_id(userid)

    model = []
    for q in query:
        model.append({
            'id': q.id,
            'userid': q.userid,
            'start_date': datetime.strftime(q.start_date, '%m/%d/%Y'),
            'end_date': datetime.strftime(q.end_date, '%m/%d/%Y')
        })

    return render_template('vacation.html', user=user, model=model)


@bp.route('/vacation/<userid>', methods=['POST'])
def add_vacation(userid):
    start = datetime.strptime(request.form['start_date'], '%m/%d/%Y')
    end = datetime.strptime(request.form['end_date'], '%m/%d/%Y')

    # Set end of day
    end = end + timedelta(days=1) - timedelta(seconds=1)

    current_vac = Vacation.query.filter(Vacation.userid == userid).all()
    can_add = True

    # Find overlapping to existing schedules
    if any(current_vac):
        for v in current_vac:
            latest_start = max(v.start_date, start)
            earliest_end = min(v.end_date, end)
            overlap = (earliest_end - latest_start).days + 1

            if overlap > 0:
                can_add = False
                break

    if can_add:
        vac = Vacation(userid=userid, start_date=start, end_date=end)
        db.session.add(vac)
        db.session.commit()

    return redirect('/vacation/{}'.format(userid))


@bp.route('/vacation/delete/<userid>/<id>')
def delete_vacation(userid, id):
    db.delete_vacation(id)
    return redirect('/vacation/{}'.format(userid))


@bp.route('/holiday', methods=['GET'])
def holiday():
    query = db.get_holiday()
    model = []
    for q in query:
        model.append({
            'id': q.id,
            'start': datetime.strftime(q.start_date, '%m/%d/%Y'),
            'end': datetime.strftime(q.end_date, '%m/%d/%Y'),
            'start_datetime': q.start_date,
            'active': datetime.today() > datetime(q.end_date.year, q.end_date.month, q.end_date.day, 23, 59, 59),
            'remarks': q.remarks,
            'group_id': q.group_id
        })

    return render_template('holiday.html', model=sorted(model, key=lambda k: k['start_datetime'], reverse=True))


@bp.route('/holiday/add', methods=['POST'])
def add_holiday():
    db.add_holiday(
        start_date=datetime.strptime(request.form['start_date'], '%m/%d/%Y'),
        end_date=datetime.strptime(request.form['end_date'], '%m/%d/%Y'),
        remarks=request.form['remarks']
    )
    return redirect(location='/holiday')


@bp.route('/holiday/delete', methods=['POST'])
def delete_holiday():
    db.delete_holiday(request.form['id'])
    return redirect(location='/holiday')


@bp.route('/email-config', methods=['GET'])
def email_config():
    model = db.get_config()

    from_address = '' if model.email_from_address is None else model.email_from_address
    name = '' if model.email_from_name is None else model.email_from_name
    subject = '' if model.email_subject is None else model.email_subject
    body = '' if model.email_body is None else model.email_body

    return render_template('email_config.html', from_address=from_address, name=name, subject=subject, body=body)


@bp.route('/email-config', methods=['POST'])
def update_email_config():
    db.update_email_config(request.form['email_from_address'],
                           request.form['email_from_name'],
                           request.form['email_subject'],
                           request.form['email_body'])
    return redirect(location='/')


# endregion


# region APIs

@bp.route('/api/add-user', methods=['POST'])
def add_user():
    user = User(email=request.form['email'], name=request.form['name'])
    db.session.add(user)
    db.session.commit()
    return jsonify(result='ok')


@bp.route('/api/delete-user', methods=['POST'])
def delete_user():
    ids = request.form.getlist('deleteUserIds')
    if bool(ids):
        for id in ids:
            db.session.query(User).filter(User.id == id).delete()

        db.session.commit()

    return jsonify(result='ok')


@bp.route('/api/update-user', methods=['POST'])
def update_user():
    id = request.form['id']
    email = request.form['email']
    name = request.form['name']

    db.session.query(User).filter(User.id == id).update({
        'name': name,
        'email': email
    })
    db.session.commit()
    return jsonify()


@bp.route('/api/user/<userid>')
def get_user(userid):
    model = db.session.query(User).filter(User.id == userid).all()

    if any(model):
        return jsonify({
            'id': model[0].id,
            'email': model[0].email,
            'name': model[0].name,
            'on_duty': model[0].on_duty,
            'seq': model[0].seq
        })

    return jsonify()


@bp.route('/api/set-user', methods=['POST'])
def user_on_duty():
    req = request.get_json()
    Logger.info('Sequences were updated. Data => {}'.format(req))

    on_duty = req['onDuty']  # type: dict

    for i in on_duty:
        user_id = i['userid']
        seq = i['index'] + 1  # Starts from 1, not 0

        User.query.filter(User.id == user_id).update({
            'seq': seq,
            'on_duty': True
        })

    off_duty = req['offDuty']  # type: dict

    for i in off_duty:
        user_id = i['userid']
        User.query.filter(User.id == user_id).update({
            'seq': -1,
            'on_duty': False
        })

    db.reset_seq()

    return jsonify(status='ok')


@bp.route('/api/resend', methods=['POST'])
def resend():
    from isr_rotation.mail_sender import resend
    return jsonify(status='ok') if resend() else jsonify(status='error')


@bp.route('/api/move-next', methods=['POST'])
def move_next():
    from isr_rotation.mail_sender import move_next
    return jsonify(status='ok') if move_next() else jsonify(status='error')


@bp.route('/api/get-status', methods=['GET'])
def get_status():
    users = db.get_all_users()
    current_seq = db.get_current_seq()
    next_seq = db.get_next_seq()

    result = []

    for u in users:
        if u.seq == -1:
            continue

        result.append({
            'name': u.name,
            'user_id': u.id,
            'seq': u.seq,
            'is_current': u.seq == current_seq,
            'is_next': u.seq == next_seq,
            'is_vacation': db.is_on_vacation(u.seq)
        })

    return jsonify(users=result)

# endregion
