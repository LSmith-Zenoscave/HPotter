import os
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database

from hpotter.tables import Base
from hpotter.logger import logger

DB=os.getenv('HPOTTER_DB', 'sqlite')
DB_USER=os.getenv('HPOTTER_DB_USER', 'root')
DB_PASSWORD=os.getenv('HPOTTER_DB_PASSWORD', '')
DB_HOST=os.getenv('HPOTTER_DB_HOST', '127.0.0.1')
DB_PORT=os.getenv('HPOTTER_DB_PORT', '')
DB_DB=os.getenv('HPOTTER_DB_DB', 'hpotter')

db = None
if DB != 'sqlite':
    if DB_PASSWORD:
        DB_PASSWORD = ':' + DB_PASSWORD

    if DB_PORT:
        DB_PORT = ':' + DB_PORT

    if DB_DB:
        DB_DB = '/' + DB_DB

    db = '{0}://{1}{2}@{3}{4}{5}'.format(DB, DB_USER, DB_PASSWORD, \
        DB_HOST, DB_PORT, DB_DB)
    logger.debug(db)

    def write_db(table):
        session.add(table)
        session.commit()
else:
    db = 'sqlite:///main.db'

    db_lock = threading.Lock()
    def write_db(table):
        with db_lock:
            session.add(table)
            session.commit()

def open_db():
    global session
    engine = create_engine(db)
    # engine = create_engine(db, echo=True)

    # https://stackoverflow.com/questions/6506578/how-to-create-a-new-database-using-sqlalchemy
    if not database_exists(engine.url):
        create_database(engine.url)

    Base.metadata.create_all(engine)
    session = scoped_session(sessionmaker(engine))()

def close_db():
    logger.info('Closing db')
    session.commit()
    session.close()
    logger.info('Done closing db')
