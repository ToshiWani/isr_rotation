from datetime import datetime

from sqlalchemy.sql import func

from isr_rotation import session, engine
from isr_rotation.models import User, Config, Vacation, Holiday, Log
from isr_rotation.logger import Logger

def init_db():
    """
    Import all modules here that might define models so that they will be registered properly on the metadata.
    Otherwise, you will have to import them first before calling init_db()
    """
    from isr_rotation import Base
    Base.metadata.create_all(bind=engine)

    if session.query(Config).count() == 0:
        config = Config()
        config.current_seq = -1
        session.add(config)
        session.commit()


# region GET - User Info


def get_all_users():
    # type: () -> list[User]

    return User.query.all()


def get_user_by_id(user_id):
    # type: (int) -> User
    return User.query.filter(User.id == user_id).first()


def get_all_email():
    return User.query.with_entities(User.email).all()


def count_on_duty():
    return User.query.filter(User.on_duty).count()


def get_on_duty_user():
    if count_on_duty() > 0:
        return User.query.join(Config, User.seq == Config.current_seq).first()
    else:
        return None


# endregion

# region GET - Sequence


def get_current_seq():
    # type: () -> int

    return Config.query.with_entities(Config.current_seq).first().current_seq


def get_max_seq():
    # type: () -> int
    return session.query(func.max(User.seq).label("max_seq")).first().max_seq


def get_user_by_seq(seq):
    return User.query.filter(User.seq == seq).first()


def get_next_seq():
    # type: () -> int

    """
        :return: -1
            - If nobody is on-duty
            - If everyone is vacation

        :return: same as current:
            - If only one is on-duty

        Count on-duty users

        Foreach till user count:
            - Increment seq
            - Check vacation of seq. If so, repeat until number of on-duty users

        :return: incremented seq
    """
    Logger.debug('Finding next on-duty user (sequence)')

    # Check if nobody is on-duty
    if is_nobody_on_duty():
        Logger.debug('...... Nobody is on-duty')
        return -1

    max_seq = get_max_seq()
    cur_seq = get_current_seq()

    # Check if only one is on-duty
    if max_seq == 1:
        user = get_user_by_seq(cur_seq)
        Logger.debug('...... Currently only {} is on-duty (Seq {})'.format(user.name, cur_seq))
        return 1

    # Current seq is set to -1
    elif cur_seq < 0:
        Logger.debug('...... Currently nobody is on duty.  Reset the sequence to 0')
        cur_seq = 0

    else:
        cur_user = get_user_by_seq(cur_seq)
        Logger.debug('...... Currently {} is on-duty. Will move to the next on-duty user. (Seq {})'
                    .format(cur_user.name, cur_seq))

    next_seq = cur_seq
    exit_loop = False

    for i in range(max_seq):
        if exit_loop:
            break

        next_seq = 1 if next_seq >= max_seq else next_seq + 1
        vacations = get_vac_by_seq(next_seq)

        if len(vacations) == 0:
            break

        for j, vac in enumerate(vacations):
            is_vacation = vac.start_date <= datetime.now() <= vac.end_date

            if is_vacation:
                next_user = get_user_by_seq(next_seq)
                Logger.debug('...... {} is on vacation today. Will move to the next on-duty user. (Seq {})'
                            .format(next_user.name, next_seq))
                break
            elif j == len(vacations) - 1:
                exit_loop = True

    final_user = get_user_by_seq(next_seq)
    Logger.debug('...... {} is the next on-duty user. (Seq {})'.format(final_user.name, next_seq))
    return next_seq


# endregion

# region GET - Vacation


def get_vac_by_seq(seq):
    # type: (int) -> list[Vacation]

    return session.query(Vacation).join(
        User, Vacation.userid == User.id
    ).filter(
        User.seq == seq
    ).all()


def is_nobody_on_duty():
    # type: () -> bool

    # Check if nobody is on-duty
    user_count = count_on_duty()
    if user_count == 0:
        return True

    # Check if everybody is vacation
    on_duty_users = User.query.filter(User.on_duty == True).all()

    on_vacation = False

    for u in on_duty_users:
        vac = Vacation.query.filter(Vacation.userid == u.id).first()
        if vac is None:
            return False

        on_vacation = vac.start_date <= datetime.now() <= vac.end_date

        if not on_vacation:
            return False

    return on_vacation


def is_on_vacation(seq):
    # type: (int) -> bool

    vac = get_vac_by_seq(seq)
    for v in vac:
        if v.start_date <= datetime.now() <= v.end_date:
            return True

    return False


# endregion

# region Config


def get_config():
    # type: () -> Config
    return Config.query.first()


def update_email_config(address, name, subject, body):
    data = {
        'email_from_address': address,
        'email_from_name': name,
        'email_subject': subject,
        'email_body': body
    }

    Config.query.update(data)
    session.commit()
    Logger.info('Updated email config.  Data => {}'.format(data))


# endregion

# region Holiday


def get_holiday():
    # type: () -> list[Holiday]

    return Holiday.query.all()


def is_holiday():
    # type: () -> bool
    holiday = get_holiday()

    for h in holiday:
        start = datetime(h.start_date.year, h.start_date.month, h.start_date.day)
        end = datetime(h.end_date.year, h.end_date.month, h.end_date.day, 23, 59, 59)

        if start < datetime.today() < end:
            return True

    return False


def add_holiday(start_date, end_date, remarks):
    # type: (datetime, datetime, str) -> None

    session.add(Holiday(start_date=start_date, end_date=end_date, remarks=remarks))
    session.commit()


def delete_holiday(id):
    # type: (int) -> None

    Holiday.query.filter(Holiday.id == id).delete()
    session.commit()


# endregion

# region UPDATE


def move_next():
    next_seq = get_next_seq()
    Config.query.update({'current_seq': next_seq})
    session.commit()
    Logger.info('Moved to the next seq: {}'.format(next_seq))


def reset_seq():
    max_seq = session.query(func.max(User.seq).label("max_seq")).first().max_seq

    if max_seq > 0:
        for i in range(1, max_seq + 1):
            if not is_on_vacation(i):
                Config.query.update({'current_seq': i})
                break
    else:
        Config.query.update({'current_seq': -1})

    session.commit()


# endregion

# region DELETE

def delete_vacation(vacation_id):
    session.query(Vacation).filter(Vacation.id == vacation_id).delete()
    session.commit()

# endregion

# region Log


def get_log():
    # type: () -> list[Log]
    return Log.query.all()


def write_log(level, message):
    session.add(Log(level, message))
    session.commit()


# endregion

