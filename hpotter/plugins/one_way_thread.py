"""Simple One-way socket thread with data records.
"""

import threading
from socket import error as SocketError

from hpotter.tables import Data
from hpotter.logger import LOGGER


class OneWayThread(threading.Thread):
    """Simple One-way socket thread with data records.
    """
    # TODO: work on data passing structure for args
    # pylint: disable=R0913
    def __init__(self, db, source, dest, config, kind, connection):
        super().__init__()
        self.db_conn = db
        self.source = source
        self.dest = dest
        self.config = config
        self.kind = kind
        self.connection = connection
        self.shutdown_requested = False

    def _read(self):
        try:
            data = self.source.recv(4096)
        except SocketError as exception:
            LOGGER.info(exception)
            return None

        LOGGER.debug('Reading from: %s, read: %s',
                     self.source, data)

        if data == b'' or not data:
            LOGGER.debug('No data read, stopping')
            return None

        return data

    def _write(self, data):
        LOGGER.debug('Sending to: %s, sent: %s',
                     self.dest, data)
        try:
            self.dest.sendall(data)
        except SocketError as exception:
            LOGGER.info(exception)
            return False

        return True

    def run(self):
        """Data pipe with db recording of passed bytes
        """
        save = False
        total = b''
        if self.kind:
            data_conf = self.kind + '_length'
            if self.config.get(data_conf, -1) > 0:
                save = True
                length = self.config[data_conf]

        while True:
            data = self._read()
            if data is None:
                break

            if not self._write(data):
                break

            if self.shutdown_requested:
                break

            total += data
            if save and len(total) >= length:
                LOGGER.debug('Limit exceeded, stopping')
                break

        if save and len(total) > 0:
            self.db_conn.write(
                Data(data=str(total),
                     kind=self.kind,
                     connection=self.connection)
            )
