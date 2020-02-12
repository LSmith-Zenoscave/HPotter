"""HPotter Database connection wrapper.
"""
import threading
import os

from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine

from hpotter.tables import BASE
from hpotter.logger import LOGGER


class DB():
    """Database connection wrapper.
    """
    def __init__(self):
        self.lock_needed = False
        self.session = None

    def get_connection_string(self):
        """Grabs a connection url from os environment.
        """
        # move to config.yml
        db_type = os.getenv('HPOTTER_DB', 'sqlite')
        db_user = os.getenv('HPOTTER_DB_USER', 'root')
        db_password = os.getenv('HPOTTER_DB_PASSWORD', '')
        db_host = os.getenv('HPOTTER_DB_HOST', '127.0.0.1')
        db_port = os.getenv('HPOTTER_DB_PORT', '')
        db_table = os.getenv('HPOTTER_DB_DB', 'hpotter')

        if db_type == 'sqlite':
            self.lock_needed = True
            return 'sqlite:///main.db'

        if db_password:
            db_password = ':' + db_password

        if db_port:
            db_port = ':' + db_port

        if db_table:
            db_table = '/' + db_table

        return '{0}://{1}{2}@{3}{4}{5}'.format(db_type, db_user, db_password,
                                               db_host, db_port, db_table)

    def write(self, table):
        """Writes to a session using locking if needed.
        """
        if self.lock_needed:
            db_lock = threading.Lock()
            with db_lock:
                self.session.add(table)
                self.session.commit()
        else:
            self.session.add(table)
            self.session.commit()

    def open(self):
        """Creates the sqlalchemy engine and connects to/creates the db session
        """
        engine = create_engine(self.get_connection_string())
        # engine = create_engine(db, echo=True)

        # https://stackoverflow.com/questions/6506578/how-to-create-a-new-database-using-sqlalchemy
        if not database_exists(engine.url):
            create_database(engine.url)

        BASE.metadata.create_all(engine)

        self.session = scoped_session(sessionmaker(engine))()

    def close(self):
        """closes the db session
        """
        LOGGER.debug('Closing db')
        self.session.commit()
        self.session.close()
        LOGGER.debug('Done closing db')
