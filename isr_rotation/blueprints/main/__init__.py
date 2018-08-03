from flask import Blueprint, render_template, redirect, request, url_for, current_app
from isr_rotation import database as db
import isr_rotation.mailer as mailer
import isr_rotation.authentication as authentication
from flask_login import current_user, login_user
from flask_ldap3_login.forms import LDAPLoginForm


bp = Blueprint('main', __name__, template_folder='templates')


@bp.route('/', methods=['GET'])
def home():
    users = db.get_all_user()
    if current_user.is_authenticated:
        user_data = authentication.get_ldap_user(current_user.username)

    return render_template('/main/index.html', users=users, current_user=current_user, user_data=user_data)


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


@bp.route('/email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        mailer.send(
            [request.form.get('recipient')],
            current_app.config.get('MAIL_DEFAULT_SUBJECT', 'ISR Rotation'),
            request.form.get('body')
        )
        return redirect('/')
    else:
        return render_template('/main/email.html')


@bp.route('/auth', methods=['GET', 'POST'])
def auth():
    user = None
    result = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        result = authentication.authenticate(email, password)
        user = authentication.get_ldap_user(email)
        photo = user.get('thumbnailPhoto')

    return render_template('/main/authentication.html', user=user, result=result)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LDAPLoginForm()
    result = form.validate_on_submit()
    if result:
        # Successfully logged in, We can now access the saved user object
        # via form.user.
        login_user(form.user)  # Tell flask-login to log them in.
        return redirect('/')  # Send them home

    return render_template('/main/login.html', form=form)

