from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *
import datetime


class ServerStorage:
    class AllUsers:
        def __init__(self, username):
            self.id = None
            self.username = username
            self.last_login = datetime.datetime.now()

    class ActiveUsers:
        def __init__(self, user_id, user_ip, user_port, login_time):
            self.id = None
            self.user_id = user_id
            self.user_ip = user_ip
            self.user_port = user_port
            self.login_time = login_time

    class UsersContacts:
        def __init__(self, user_id, contact_id):
            self.id = None
            self.user_id = user_id
            self.contact_id = contact_id

    class UsersHistory:
        def __init__(self, user_id):
            self.id = None
            self.user_id = user_id
            self.sent = 0
            self.accepted = 0

    class LoginHistory:
        def __init__(self, user_id, date, user_ip, user_port):
            self.id = None
            self.user_id = user_id
            self.date_time = date
            self.user_ip = user_ip
            self.user_port = user_port

    def __init__(self):
        self.database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('username', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('Users.id'), unique=True),
                                   Column('user_ip', String),
                                   Column('user_port', String),
                                   Column('login_time', DateTime)
                                   )

        users_contacts = Table('Users_contacts', self.metadata,
                               Column('id', Integer, primary_key=True),
                               Column('user_id', ForeignKey('Users.id')),
                               Column('contact_id', ForeignKey('Users.id'))
                               )

        users_history = Table('Users_history', self.metadata,
                              Column('id', Integer, primary_key=True),
                              Column('user_id', ForeignKey('Users.id')),
                              Column('sent', Integer),
                              Column('accepted', Integer)
                              )

        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('user_ip', String),
                                   Column('user_port', String)
                                   )

        self.metadata.create_all(self.database_engine)

        mapper(self.AllUsers, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.UsersContacts, users_contacts)
        mapper(self.UsersHistory, users_history)
        mapper(self.LoginHistory, user_login_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, user_ip, user_port):
        print(f'{username} {user_ip}:{user_port} connected')
        result = self.session.query(self.AllUsers).filter_by(username=username)
        if result.count():
            user = result.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)

            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = self.ActiveUsers(user.id, user_ip, user_port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(), user_ip, user_port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        self.session.query(self.ActiveUsers).filter_by(user_id=user.id).delete()
        self.session.commit()

    def process_message(self, sender, recipient):
        sender = self.session.query(self.AllUsers).filter_by(username=sender).first().id
        recipient = self.session.query(self.AllUsers).filter_by(username=recipient).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user_id=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user_id=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, username, contact):
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()
        if not contact or self.session.query(self.UsersContacts).filter_by(user_id=user.id, contact_id=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, username, contact):
        user = self.session.query(self.AllUsers).filter_by(username=username).first()
        contact = self.session.query(self.AllUsers).filter_by(username=contact).first()

        if not contact:
            return

        self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user_id == user.id,
            self.UsersContacts.contact_id == contact.id
        ).delete()
        self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
        )

        return query.all()

    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.username,
            self.ActiveUsers.user_ip,
            self.ActiveUsers.user_port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)

        return query.all()

    def login_history(self, username=None):
        query = self.session.query(
            self.AllUsers.username,
            self.LoginHistory.date_time,
            self.LoginHistory.user_ip,
            self.LoginHistory.user_port,
        ).join(self.AllUsers)

        if username:
            query = query.filter(self.AllUsers.username == username)

        return query.all()

    def get_contact(self, username):
        user = self.session.query(self.AllUsers).filter_by(username=username).one()

        query = self.session.query(self.UsersContacts, self.AllUsers.username). \
            filter_by(user_id=user.id).join(
            self.AllUsers, self.UsersContacts.contact_id == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.AllUsers.username,
            self.AllUsers.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.AllUsers)

        return query.all()


if __name__ == '__main__':
    test_db = ServerStorage()
    # выполняем 'подключение' пользователя
    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    test_db.user_login('client_3', '192.168.1.6', 7878)
    # выводим список кортежей - активных пользователей
    print(test_db.active_users_list())
    # выполянем 'отключение' пользователя
    test_db.user_logout('client_1')

    # выводим список активных пользователей
    print(test_db.active_users_list())
    # запрашиваем историю входов по пользователю
    test_db.login_history('client_1')
    # выводим список известных пользователей
    print(test_db.users_list())

    print(test_db.message_history())
    test_db.process_message('client_2', 'client_3')
    print(test_db.message_history())
    print()
    print(test_db.get_contact('client_2'))
    print(test_db.get_contact('client_3'))
    print()
    test_db.add_contact('client_2', 'client_3')
    print(test_db.get_contact('client_2'))
    print(test_db.get_contact('client_3'))
    print()
    test_db.remove_contact('client_2', 'client_3')

    print(test_db.get_contact('client_2'))
    print(test_db.get_contact('client_3'))
