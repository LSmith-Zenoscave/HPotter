import threading

from hpotter.tables import Data
from hpotter.logger import logger


class OneWayThread(threading.Thread):
    def __init__(self, db, source, dest, config, kind, connection):
        super().__init__()
        self.db = db
        self.source = source
        self.dest = dest
        self.config = config
        self.kind = kind
        self.connection = connection
        self.total = b''
        self.data = b''
        self.save = False
        self.shutdown_requested = False

    def read(self):
        try:
            self.data = self.source.recv(4096)
        except Exception as exception:
            logger.info(exception)
            return False

        logger.debug('Reading from: ' + str(self.source) +
                     ', read: ' + str(self.data))

        if self.data == b'' or not self.data:
            logger.debug('No data read, stopping')
            return False

        if self.save:
            self.total += self.data

        return True

    def write(self):
        logger.debug('Sending to: ' + str(self.dest) +
                     ', sent: ' + str(self.data))
        try:
            self.dest.sendall(self.data)
        except Exception as exception:
            logger.info(exception)
            return False

        return True

    def run(self):
        if self.kind:
            s = self.kind + '_length'
            if s in self.config and self.config[s] > 0:
                self.save = True
                length = self.config[s]

        while True:
            if not self.read():
                break

            if not self.write():
                break

            if self.shutdown_requested:
                break

            if self.save and len(self.total) >= length:
                logger.debug('Limit exceeded, stopping')
                break

        if self.save and len(self.total) > 0:
            self.db.write(
                Data(data=str(self.total),
                     kind=self.kind,
                     connection=self.connection)
            )
