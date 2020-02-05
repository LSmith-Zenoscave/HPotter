import socket
import threading
import docker
import time
from enum import Enum

from hpotter.tables import Connections, TCP

from hpotter.logger import logger
from hpotter.plugins.OneWayThread import OneWayThread


class RorR(Enum):
    request = 1
    response = 2
    neither = 3


class ContainerThread(threading.Thread):
    def __init__(self, db, source, config):
        super().__init__()
        self.db = db
        self.source = source
        self.config = config
        self.connection = None
        self.dest = self.thread1 = self.thread2 = self.container = None

    '''
    Need to make a different one for macos as docker desktop for macos
    doesn't allow connecting to a docker-defined network. I'm thinking of
    using 127.0.0.1 and mapping the internal port to one in the range
    25000-25999 as those don't appear to be claimed in
    https://support.apple.com/en-us/HT202944
    I believe client sockets start in the 40000's
    '''

    def connect_to_container(self):
        nwsettings = self.container.attrs['NetworkSettings']
        IPAddress = nwsettings['Networks']['bridge']['IPAddress']
        logger.debug(IPAddress)

        ports = nwsettings['Ports']
        assert len(ports) == 1
        port_key = list(ports.keys())[0]
        port = int(port_key.split('/')[0])
        logger.debug(port)

        sock_addr = (IPAddress, port)
        host = IPAddress + ':' + str(port)
        for _ in range(9):
            try:
                self.dest = socket.create_connection(sock_addr, timeout=2)
                break
            except OSError as err:
                if err.errno == 111:
                    time.sleep(2)
                    continue
                logger.info('Unable to connect to ' + host)
                logger.info(err)
                raise err

    def save_connection(self):
        if 'add_dest' in self.config:
            self.connection = Connections(
                sourceIP=self.source.getsockname()[0],
                sourcePort=self.source.getsockname()[1],
                destIP=self.dest.getsockname()[0],
                destPort=self.dest.getsockname()[1],
                proto=TCP)
            self.db.write(self.connection)
        else:
            self.connection = Connections(
                sourceIP=self.source.getsockname()[0],
                sourcePort=self.source.getsockname()[1],
                proto=TCP)
            self.db.write(self.connection)

    def run(self):
        try:
            client = docker.from_env()
            self.container = client.containers.run(
                self.config['container'], detach=True)
            logger.info('Started: %s', self.container)
            self.container.reload()
        except Exception as err:
            logger.info(err)
            return

        try:
            self.connect_to_container()
        except Exception as err:
            logger.info(err)
            self.stop_and_remove()
            return

        self.save_connection()

        # TODO: startup dynamic iptables rules code here.

        logger.debug('Starting thread1')
        self.thread1 = OneWayThread(self.db, self.source, self.dest,
                                    {'request_length': 4096}, 'request',
                                    self.connection)
        self.thread1.start()
        logger.debug('Starting thread2')
        self.thread2 = OneWayThread(self.db, self.dest, self.source,
                                    self.config, 'response', self.connection)
        self.thread2.start()

        logger.debug('Joining thread1')
        self.thread1.join()
        logger.debug('Joining thread2')
        self.thread2.join()

        # TODO: shutdown dynamic iptables rules code here.

        self.dest.close()
        self.stop_and_remove()

    def stop_and_remove(self):
        logger.debug(str(self.container.logs()))
        logger.info('Stopping: %s', self.container)
        self.container.stop()
        logger.info('Removing: %s', self.container)
        self.container.remove()

    def shutdown(self):
        self.thread1.shutdown()
        self.thread2.shutdown()
        self.dest.close()
        self.stop_and_remove()
