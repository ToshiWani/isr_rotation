from flask import Blueprint, render_template, redirect, request, url_for
from isr_rotation import database as db

bp = Blueprint('main', __name__, template_folder='templates')


@bp.route('/', methods=['GET'])
def home():
    users = db.get_all_user()
    return render_template('/main/index.html', users=users)


@bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'GET':
        return render_template('/main/add_user.html')
    else:
        db.upsert_user(request.form['email'], request.form['display_name'])
        return redirect('/')


@bp.route('/update_user', methods=['GET', 'POST'])
def update_user():
    email = request.args.get('email')
    user = db.get_user(email)

    if request.method == 'POST':
        db.upsert_user(email, request.form.get('display_name'))
        return redirect('/')
    else:
        return render_template('/main/update_user.html', user=user)


@bp.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    users = db.get_all_user()
    if request.method == 'POST':
        emails = request.form.getlist('delete')
        db.delete_users(emails)
        return redirect('/')
    else:
        return render_template('/main/delete_user.html', users=users)


@bp.route('/<email>')
def user(email):
    user = db.get_user(email)
    return None if user is None else user[0]['display_name']


@bp.route('/upsert/<email>/<display_name>')
def upsert(email, display_name):
    user = db.upsert_user(email, display_name)
    return str(user.upserted_id)


@bp.route('/delete/<email>')
def delete(email):
    result = db.delete_user(email)
    return result.delete_count

