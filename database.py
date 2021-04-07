import logging
from sqlalchemy import create_engine, Boolean, ForeignKey, Column, String, DateTime, Integer
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import Settings

LOG_FORMAT = ('%(asctime)s,%(msecs)d %(levelname)s: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

config = Settings()

base_path = config.get("base", "path")

if not base_path:
    base_path = './base.db'
    config.set("base", "path", "./base.db")
    config.commit()

Model = declarative_base()

DATABASE = {
    'drivername': 'sqlite',
    'database': base_path
}

dbengine = create_engine(URL(**DATABASE), connect_args={'check_same_thread': False})
Session = sessionmaker(bind=dbengine)
LOGGER.log(logging.INFO, msg="Creating session with database %s" % base_path)
session = Session()


class Bot(Model):
    __tablename__ = 'bots'
    name = Column(String, primary_key=True)
    platform = Column(String)
    token = Column(String, unique=True)
    start_message = Column(String)
    default_response = Column(String)
    start_callback = Column(String)
    message_callback = Column(String)
    callback_auth = Column(Boolean)
    callback_login = Column(String)
    callback_password = Column(String)
    custom_handler = Column(String)
    access_token = Column(String)

    def __init__(self, name, platform, token, start_message=None,
                 default_response=None, custom_handler=None, start_callback=None, message_callback=None,
                 callback_auth=False, callback_login=None, callback_password=None, access_token=None):
        self.name = name
        self.platform = platform
        self.token = token
        self.start_message = start_message
        self.default_response = default_response
        self.start_callback = start_callback
        self.message_callback = message_callback
        self.custom_handler = custom_handler
        self.callback_auth = callback_auth
        self.callback_login = callback_login
        self.callback_password = callback_password
        self.access_token = access_token

    def __repr__(self):
        return "<Bot(%s, %s)>" % (self.name, self.platform)

    def save(self):
        try:
            session.add(self)
            session.commit()
            LOGGER.log(logging.INFO, msg="Registered new bot %s by HTTP query" % self.name)
        except Exception as e:
            session.rollback()
            LOGGER.log(logging.INFO, msg="Failed to save bot in database %s" % e)

    def delete(self):
        try:
            session.query(Bot).filter_by(token=self.bot.token).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            LOGGER.log(logging.INFO, msg="Failed to remove bot because %s" % e)

    @staticmethod
    def get_all():
        try:
            bots = session.query(Bot).all()
            return bots
        except Exception as e:
            LOGGER.log(logging.INFO, msg="Failed to query all bots because %s" % e)


class Message(Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    sender = Column(String, ForeignKey('users.user_id'))
    recipient = Column(String, ForeignKey('bots.name'))
    body = Column(String)
    processed = Column(Boolean)

    def __init__(self, message_id, date, sender, recipient, body, processed):
        self.message_id = message_id
        self.date = date
        self.sender = sender
        self.recipient = recipient
        self.body = body
        self.processed = processed

    def __repr__(self):
        return "<Message(%s, %s)>" % (self.id, self.recipient)

    def save(self):
        try:
            session.add(self)
            session.commit()
            LOGGER.log(logging.INFO, msg="Saved message %s from %s" % (self.message_id, self.sender))
        except Exception as e:
            session.rollback()
            LOGGER.log(logging.INFO, msg="Failed to save new user because %s" % e)

    @staticmethod
    def get(message_id):
        message = session.query(Message).filter_by(id=message_id).one_or_none()
        return message


class User(Model):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    platform = Column(String)

    def __init__(self, user_id, first_name, last_name, username, platform):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.platform = platform

    def __repr__(self):
        return "<User(%s, %s)>" % (self.user_id, self.username)

    def save(self):
        try:
            session.add(self)
            session.commit()
            LOGGER.log(logging.INFO, msg='Saved user %s:%s as known' % (self.platform, self.username))
        except Exception as e:
            session.rollback()
            LOGGER.log(logging.INFO, msg="Failed to save new message because %s" % e)

    def delete(self):
        try:
            session.query(User).filter_by(user_id=self.user_id).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            LOGGER.log(logging.INFO, msg="Failed to remove user because %s" % e)

    @staticmethod
    def get(user_id):
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        return user


Model.metadata.create_all(dbengine)
