from flask import Blueprint, render_template, redirect, request, url_for, current_app, flash, g, abort
from isr_rotation import database as db
import isr_rotation.mailer as mailer
import isr_rotation.authentication as authentication
from flask_login import current_user, login_user, login_required, logout_user
from flask_ldap3_login.forms import LDAPLoginForm
from isr_rotation.caching import get_cache, set_cache
import datetime


bp = Blueprint('main', __name__, template_folder='templates')


@bp.before_request
def before_request():
    g.user = current_user
    pass


@bp.route('/', methods=['GET'])
@login_required
def home():
    on_duty_users = sorted(db.get_all_on_duty_user(), key=lambda u: u.get('seq'))
    off_duty_users = db.get_all_off_duty_user()
    current_rotation = db.get_current_rotation()
    next_rotation = db.get_next_rotation()

    return render_template(
        '/main/index.html',
        on_duty_users=on_duty_users,
        off_duty_users=off_duty_users,
        current_rotation=current_rotation,
        next_rotation=next_rotation
    )


@bp.route('/add_user', methods=['POST'])
@login_required
def add_user():
    email = request.form.get('email')
    display_name = request.form.get('display_name')

    if email and display_name:
        db.add_user(request.form['email'], request.form['display_name'])
    else:
        flash('Email and/or display name cannot be empty')

    return redirect('/')


@bp.route('/update_user/<email>', methods=['GET', 'POST'])
def update_user(email):
    if request.method == 'POST':
        db.update_user(email, request.form.get('display_name'))
        return redirect('/')
    else:
        cache_key = 'ldap_user_' + email
        ldap_user = get_cache(cache_key)

        if ldap_user is None:
            ldap_user = authentication.get_ldap_user(email)
            set_cache(cache_key, ldap_user)

        user = db.get_user(email)
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


@bp.route('/holiday', methods=['GET', 'POST'])
@login_required
def holiday():
    if request.method == 'POST':
        date = request.form.get('date')
        remarks = request.form.get('remarks')
        db.upasert_holiday(date, remarks)

    holidays = db.get_holidays()
    return render_template('/main/holiday.html', holidays=holidays)


@bp.route('/vacation/<email>', methods=['GET'])
def vacation(email):
    user = db.get_user(email)
    if user is None:
        return abort(404)
    else:
        return render_template('/main/vacation.html', user=user)


@bp.route('/vacation/<email>', methods=['POST'])
def post_vacation(email):
    start_date = request.form.get('start-date')
    end_date = request.form.get('end-date')
    remarks = request.form.get('remarks')

    try:
        result = db.add_vacation(email, start_date, end_date, remarks)
    except KeyError:
        flash('Start date and end date are duplicated')

    user = db.get_user(email)
    return render_template('/main/vacation.html', user=user)


# region Email

@bp.route('/email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        mailer.send_custom(
            [request.form.get('recipient')],
            current_app.config.get('MAIL_DEFAULT_SUBJECT', 'ISR Rotation'),
            request.form.get('body')
        )
        return redirect('/')
    else:
        return render_template('/main/email.html')


@bp.route('/email_settings', methods=['GET'])
def email_settings():
    settings = db.get_email_settings()
    return render_template(
        '/main/email_settings.html',
        from_email=settings.get('from_email'),
        subject=settings.get('subject'),
        body=settings.get('body'),
    )


@bp.route('/email_settings', methods=['POST'])
def email_settings_post():
    from_email = request.form.get('from_email')
    subject = request.form.get('subject')
    body = request.form.get('body')

    if from_email and subject and body:
        db.update_email_settings(from_email, subject, body)
        flash('<i class="material-icons">check_circle</i> Saved!')

    return redirect('/email_settings')

# endregion

