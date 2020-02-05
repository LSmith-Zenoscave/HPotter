import os
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database

from hpotter.tables import base
from hpotter.logger import logger

class DB():
    def __init__(self):
        self.lock_needed = False
        self.session = None

    def get_DB_string(self):
        # move to config.yml
        DB=os.getenv('HPOTTER_DB', 'sqlite')
        DB_USER=os.getenv('HPOTTER_DB_USER', 'root')
        DB_PASSWORD=os.getenv('HPOTTER_DB_PASSWORD', '')
        DB_HOST=os.getenv('HPOTTER_DB_HOST', '127.0.0.1')
        DB_PORT=os.getenv('HPOTTER_DB_PORT', '')
        DB_DB=os.getenv('HPOTTER_DB_DB', 'hpotter')

        if DB != 'sqlite':
            if DB_PASSWORD:
                DB_PASSWORD = ':' + DB_PASSWORD

            if DB_PORT:
                DB_PORT = ':' + DB_PORT

            if DB_DB:
                DB_DB = '/' + DB_DB

            return '{0}://{1}{2}@{3}{4}{5}'.format(DB, DB_USER, DB_PASSWORD, \
                DB_HOST, DB_PORT, DB_DB)
        else:
            self.lock_needed = True
            return 'sqlite:///main.db'

    def write(self, table):
        if self.lock_needed:
            db_lock = threading.Lock()
            with db_lock:
                self.session.add(table)
                self.session.commit()
        else:
            self.session.add(table)
            self.session.commit()

    def open(self):
        engine = create_engine(self.get_DB_string())
        # engine = create_engine(db, echo=True)

        # https://stackoverflow.com/questions/6506578/how-to-create-a-new-database-using-sqlalchemy
        if not database_exists(engine.url):
            create_database(engine.url)

        base.metadata.create_all(engine)

        self.session = scoped_session(sessionmaker(engine))()

    def close(self):
        logger.debug('Closing db')
        self.session.commit()
        self.session.close()
        logger.debug('Done closing db')
