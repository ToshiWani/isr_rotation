from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from isr_rotation import Base


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    on_duty = Column(Boolean, nullable=False, default=False)
    seq = Column(Integer, default=-1)

    def __init__(self, email, name):
        self.email = email
        self.name = name

    def __repr__(self):
        return '<User id={id} email={email!r} name={name!r} on_duty={on_duty} seq={seq}>'.format(
            id=self.id, email=self.email, name=self.name, on_duty=self.on_duty, seq=self.seq
        )


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    current_seq = Column(Integer, nullable=False, default=-1)
    email_from_address = Column(String)
    email_from_name = Column(String)
    email_subject = Column(String)
    email_body = Column(String)
    last_sent = Column(DateTime)

    def __repr__(self):
        return '<Config id={id} current_seq={current_seq} email_from_address={email_from_address} ' \
               'email_from_name={email_from_name} email_subject={email_subject} email_body={email_body}>' \
            .format(
                id=self.id,
                current_seq=self.current_seq,
                email_from_address=self.email_from_address,
                email_from_name=self.email_from_name,
                email_subject=self.email_subject,
                email_body=self.email_body
            )


class Vacation(Base):
    __tablename__ = 'vacation'

    id = Column(Integer, primary_key=True)
    userid = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.now())

    def __init__(self, userid, start_date, end_date):
        self.userid = userid
        self.start_date = start_date
        self.end_date = end_date

    def __repr__(self):
        return '<Vacation id={id} userid={userid} start_date={start_date} end_date={end_date} created_on={created_on}>'\
            .format(
                id=self.id, userid=self.userid,
                start_date=datetime.strftime(self.start_date, '%m/%d/%Y'),
                end_date=datetime.strftime(self.end_date, '%m/%d/%Y'),
                created_on=self.created_on
            )


class Holiday(Base):
    __tablename__ = 'holiday'

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer)  # Future expansion
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    remarks = Column(String)
    created_on = Column(DateTime, nullable=False, default=datetime.now())

    def __init__(self, start_date, end_date, remarks):
        self.start_date = start_date
        self.end_date = end_date
        self.remarks = remarks

    def __repr__(self):
        return '<Holiday id={id} group_id={group_id} start_date={start_date} end_date={end_date} ' \
               'remarks={remarks} created_on={created_on}>' \
            .format(
                id=self.id,
                group_id=self.group_id,
                start_date=datetime.strftime(self.start_date, '%m/%d/%Y'),
                end_date=datetime.strftime(self.end_date, '%m/%d/%Y'),
                created_on=datetime.strftime(self.created_on, '%m/%d/%Y'),
                remarks=self.remarks
            )


class Log(Base):
    __tablename__ = 'log'

    id = Column(Integer, primary_key=True)
    created_on = Column(DateTime, nullable=False, default=datetime.now())
    level = Column(String, nullable=False)
    message = Column(String)

    def __init__(self, level, message):
        self.level = level
        self.message = message

    def __repr__(self):
        return '<Log id={id} created_on={created_on} level={level} message={message}>'.format(
            id=self.id,
            created_on=self.created_on,
            level=self.level,
            message=self.message
        )

