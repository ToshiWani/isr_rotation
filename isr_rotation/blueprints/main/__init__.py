from flask import Blueprint, render_template, redirect, request, url_for, current_app, flash, g, abort
from isr_rotation import database as db
import isr_rotation.mailer as mailer
import isr_rotation.authentication as authentication
from flask_login import current_user, login_user, login_required, logout_user
from flask_ldap3_login.forms import LDAPLoginForm
from isr_rotation.caching import get_cache, set_cache
import textwrap


bp = Blueprint('main', __name__, template_folder='templates')


@bp.before_request
def before_request():
    g.user = current_user
    pass


@bp.route('/', methods=['GET'])
# @login_required
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

# region User


@bp.route('/add-user', methods=['POST'])
# @login_required
def add_user():
    email = request.form.get('email')
    display_name = request.form.get('display_name')

    if email and display_name:
        db.add_user(request.form['email'], request.form['display_name'])
        current_app.logger.info(f'Added a new user, {display_name} ({email})')
    else:
        flash('Email and/or display name cannot be empty')

    return redirect('/')


@bp.route('/edit-user/<email>', methods=['GET', 'POST'])
def edit_user(email):
    if request.method == 'POST':
        display_name = request.form.get('display-name', '')
        if display_name != '':
            db.update_user(email, request.form.get('display-name'))

        return redirect('/')

    else:
        user = db.get_user(email)
        return render_template('/main/edit-user.html', user=user)


# endregion

# region Login


@bp.route('/auth-tester', methods=['GET', 'POST'])
def auth_tester():
    formatted_data = None
    result = None

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        result = authentication.authenticate(email, password)

        cache_key = f'formatted_ldap_user_data_{email}'
        formatted_data = get_cache(cache_key)

        if formatted_data is None:
            ldap_user_data = authentication.get_ldap_user(email)
            formatted_data = dict()
            for key in ldap_user_data:
                formatted_data.update({
                    key: textwrap.shorten(str(ldap_user_data[key]), width=2000)
                })

            set_cache(cache_key, formatted_data)

    return render_template('/main/auth-tester.html', ldap_user_data=formatted_data, result=result)


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
# @login_required
def logout():
    logout_user()
    return redirect('/')


# endregion

# region Settings

@bp.route('/holiday', methods=['GET', 'POST'])
# @login_required
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
    except KeyError as e:
        flash(e.args)

    user = db.get_user(email)
    return render_template('/main/vacation.html', user=user)


@bp.route('/system_log', methods=['GET', 'POST'])
def system_log():
    record_count = 100

    if request.method == 'POST':
        record_count = int(request.form.get('record-count', 100))
        record_count = 100 if record_count < 1 else record_count

    logs = db.get_log(record_count)
    return render_template('/main/system_log.html', logs=logs, record_count=record_count)


# endregion

# region Email


@bp.route('/email_settings', methods=['GET'])
def email_settings():
    settings = db.get_email_settings()
    placeholders = mailer.get_email_placeholders()
    return render_template(
        '/main/email_settings.html',
        from_email=settings.get('from_email'),
        subject=settings.get('subject'),
        body=settings.get('body'),
        placeholders=placeholders
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
