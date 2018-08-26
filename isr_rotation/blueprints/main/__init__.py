from flask import Blueprint, render_template, redirect, request, url_for, current_app, flash, g
from isr_rotation import database as db
import isr_rotation.mailer as mailer
import isr_rotation.authentication as authentication
from flask_login import current_user, login_user, login_required, logout_user
from flask_ldap3_login.forms import LDAPLoginForm


bp = Blueprint('main', __name__, template_folder='templates')


@bp.before_request
def before_request():
    g.user = current_user
    pass


@bp.route('/', methods=['GET'])
@login_required
def home():
    users = db.get_all_user()
    return render_template(
        '/main/index.html',
        on_duty_users=[u for u in users if u['is_duty']],
        off_duty_users=[u for u in users if not u['is_duty']],
        current_user=current_user,
    )


@bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'GET':
        return render_template('/main/add_user.html')
    else:
        db.upsert_user(request.form['email'], request.form['display_name'])
        return redirect('/')


@bp.route('/update_user/<email>', methods=['GET', 'POST'])
def update_user(email):
    user = db.get_user(email)
    if request.method == 'POST':
        db.upsert_user(email, request.form.get('display_name'))
        return redirect('/')
    else:
        ldap_user = authentication.get_ldap_user(email)
        return render_template('/main/update_user.html', user=user, ldap_user=ldap_user)


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


@bp.route('/login', methods=['GET'])
def login():
    bypass_login = current_app.config.get('DEBUG_BYPASS_LOGIN', False)
    if bypass_login:
        debug_user = current_app.config.get('DEBUG_BYPASS_USERNAME', 'debug_user')
        login_user(authentication.get_debug_user(debug_user))
        return redirect('/')
    else:
        form = LDAPLoginForm()
        return render_template('/main/login.html', form=form)


@bp.route('/login', methods=['POST'])
def login_post():
    form = LDAPLoginForm()

    if form.validate_on_submit():
        if login_user(form.user):
            return redirect('/')  # Send them home
        else:
            form.errors['password'] = ['User not authorized']

    return render_template('/main/login.html', form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


