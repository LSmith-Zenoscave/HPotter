import socket
import threading

from hpotter import tables
from hpotter.logger import logger
from hpotter.db import write_db

# read and write between two sockets with a possible upper limit. write to
# db if table passed in.
class OneWayThread(threading.Thread):
    def __init__(self, source, dest, table=None, limit=0):
        super().__init__()
        self.source = source
        self.dest = dest
        logger.debug(str(self.source))
        logger.debug(str(self.dest))
        self.table = table
        self.limit = limit
        self.shutdown_requested = False

        '''
        if self.table:
            self.connection = tables.Connections(
                sourceIP=self.source.getsockname()[0],
                sourcePort=self.source.getsockname()[1],
                destIP=self.dest.getsockname()[0],
                destPort=self.dest.getsockname()[1],
                proto=tables.TCP)
            write_db(self.connection)
        '''

    def run(self):
        logger.debug(str(self.source))
        logger.debug(str(self.dest))
        total = b''
        while 1:
            try:
                data = self.source.recv(4096)
            except Exception as exception:
                logger.info(exception)
                break
            logger.debug('Reading from: ' + str(self.source) \
                + ', read: ' + str(data))

            if self.shutdown_requested:
                break

            if data == b'' or not data:
                logger.debug('No data read, stopping')
                break

            if self.table or self.limit > 0:
                total += data

            try:
                self.dest.sendall(data)
            except Exception as exception:
                logger.info(exception)
                break
            logger.debug('Sending to: ' + str(self.dest) \
                + ', sent: ' + str(data))

            if self.shutdown_requested:
                break

            if self.limit > 0 and len(total) >= self.limit:
                logger.debug('Limit exceeded, stopping')
                break

        if self.table and len(total) > 0:
            write_db(self.table(request=str(total), connection=self.connection))

    def shutdown(self):
        self.shutdown_requested = True
