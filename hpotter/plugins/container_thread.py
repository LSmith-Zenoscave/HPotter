"""HPotter's Docker port to threaded socket communication functionality
"""

import socket
import threading
import time

import docker
import docker.errors

from hpotter.tables import Connections, TCP
from hpotter.logger import LOGGER
from hpotter.plugins.one_way_thread import OneWayThread


class ContainerThread(threading.Thread):
    """A container thread connects a port exposed on a docker container to an
    existing listening thread.
    """
    def __init__(self, db, source, config):
        super().__init__()
        self.db_conn = db
        self.source = source
        self.config = config
        self.connection = None
        self.dest = None
        self.container = None
        self.threads = []

    def connect_to_container(self):
        """Creates OneWayThread instances connected to the container.

        Note:
        Need to make a different one for macos as docker desktop for macos
        doesn't allow connecting to a docker-defined network. I'm thinking of
        using 127.0.0.1 and mapping the internal port to one in the range
        25000-25999 as those don't appear to be claimed in
        https://support.apple.com/en-us/HT202944
        I believe client sockets start in the 40000's
        """
        nwsettings = self.container.attrs['NetworkSettings']
        ip_address = nwsettings['Networks']['bridge']['IPAddress']
        LOGGER.debug(ip_address)

        ports = nwsettings['Ports']
        port_key = list(ports.keys())[0]
        port = int(port_key.split('/')[0])
        LOGGER.debug(port)

        sock_addr = (ip_address, port)
        host = ip_address + ':' + str(port)
        LOGGER.debug("Connect to docker host: %s", host)
        for _ in range(20):
            try:
                self.dest = socket.create_connection(sock_addr, timeout=2)
                break
            except OSError as err:
                if err.errno == 111:
                    LOGGER.info(err)
                    time.sleep(2)
                    continue
                LOGGER.info('Unable to connect to %s', host)
                LOGGER.info(err)
                raise err
        if self.dest is not None:
            LOGGER.debug('Connected.')
        else:
            raise TimeoutError("Could not connect.")

    def save_connection(self):
        """Write connection information to HPotter db.

        Includes source ip and port, destination ip and port, and TCP/UDP.
        """
        if 'add_dest' in self.config:
            self.connection = Connections(
                sourceIP=self.source.getsockname()[0],
                sourcePort=self.source.getsockname()[1],
                destIP=self.dest.getsockname()[0],
                destPort=self.dest.getsockname()[1],
                proto=TCP)
            self.db_conn.write(self.connection)
        else:
            self.connection = Connections(
                sourceIP=self.source.getsockname()[0],
                sourcePort=self.source.getsockname()[1],
                proto=TCP)
            self.db_conn.write(self.connection)

    def run(self):
        """Thread entry point
        Runs the container and connects to its exposed ports.

        Should remove/cleanup on shutdown.
        """
        try:
            client = docker.from_env()
            self.container = client.containers.run(
                self.config['container'],
                detach=True,
                environment=self.config.get('environment', []))
            LOGGER.info('Started: %s', self.container)
            self.container.reload()
        except (docker.errors.ContainerError,
                docker.errors.ImageNotFound,
                docker.errors.APIError) as err:
            LOGGER.info(err)
            return

        try:
            self.connect_to_container()
        except (OSError, TimeoutError) as err:
            LOGGER.info(err)
            self.stop_and_remove()
            return

        self.save_connection()

        # TODO: startup dynamic iptables rules code here.

        self.threads.append(OneWayThread(self.db_conn, self.source, self.dest,
                                         {'request_length': 4096}, 'request',
                                         self.connection))

        self.threads.append(OneWayThread(self.db_conn, self.dest, self.source,
                                         self.config, 'response',
                                         self.connection))

        LOGGER.debug('Starting threads')
        for thread in self.threads:
            thread.start()

        LOGGER.debug('Joining threads')
        for thread in self.threads:
            thread.join()

        # TODO: shutdown dynamic iptables rules code here.

        self.dest.close()
        self.stop_and_remove()

    def stop_and_remove(self):
        """Stop and cleanup docker container
        """

        LOGGER.debug(str(self.container.logs()))
        LOGGER.info('Stopping: %s', self.container)
        self.container.stop()
        LOGGER.info('Removing: %s', self.container)
        self.container.remove()

    def shutdown(self):
        """Thread exit point.
        """
        for thread in self.threads:
            thread.shutdown()
        self.dest.close()
        self.stop_and_remove()
