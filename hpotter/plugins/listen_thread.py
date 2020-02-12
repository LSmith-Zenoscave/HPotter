"""HPotter exposed port Listener Thread functionality
"""
import socket
import threading
import ssl
import tempfile
import os

from OpenSSL import crypto

from hpotter.logger import LOGGER
from hpotter.plugins.container_thread import ContainerThread


class ListenThread(threading.Thread):
    """Thread for exposing a socket externally to be attached to a docker port
    """

    def __init__(self, db, config, table=None, limit=None):
        super().__init__()
        self.db_conn = db
        self.config = config
        self.table = table
        self.limit = limit
        self.shutdown_requested = False
        self.context = None
        self.container_list = []

    # https://stackoverflow.com/questions/27164354/create-a-self-signed-x509-certificate-in-python
    def _gen_cert(self):
        if 'key_file' in self.config:
            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.context.load_cert_chain(
                self.config['cert_file'], self.config['key_file'])
        else:
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 4096)
            cert = crypto.X509()
            cert.get_subject().C = "UK"
            cert.get_subject().ST = "London"
            cert.get_subject().L = "Diagon Alley"
            cert.get_subject().OU = "The Leaky Caldron"
            cert.get_subject().O = "J.K. Incorporated"  # noqa: E741
            cert.get_subject().CN = socket.gethostname()
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, 'sha1')

            # can't use an iobyte file for this as load_cert_chain only take a
            # filesystem path :/
            cert_file = tempfile.NamedTemporaryFile(delete=False)
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            cert_file.close()

            key_file = tempfile.NamedTemporaryFile(delete=False)
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
            key_file.close()

            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.context.load_cert_chain(
                certfile=cert_file.name, keyfile=key_file.name)

            os.remove(cert_file.name)
            os.remove(key_file.name)

    def run(self):
        """Thread entry point
        This opens a socket listener and connects its container port in docker.
        """
        listen_address = (self.config['listen_IP'],
                          int(self.config['listen_port']))
        LOGGER.info('Listening to %s', listen_address)
        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if self.config.get('TLS', False):
            self._gen_cert()
            listen_socket = self.context.wrap_socket(listen_socket)

        # check for shutdown request every five seconds
        listen_socket.settimeout(5)
        listen_socket.bind(listen_address)
        listen_socket.listen()

        while True:
            source = None
            try:
                source, _ = listen_socket.accept()
            except socket.timeout:
                if self.shutdown_requested:
                    LOGGER.info('ListenThread shutting down')
                    break
                continue
            # TODO: find exact exceptions raised here. If any.
            except Exception as exc:  # pylint: disable=W0703
                LOGGER.info(exc)

            container = ContainerThread(self.db_conn, source, self.config)
            self.container_list.append(container)
            container.start()

        if listen_socket:
            listen_socket.close()
            LOGGER.info('Socket closed')

    def shutdown(self):
        """Thread cleanup/exit point
        """
        self.shutdown_requested = True
        for container in self.container_list:
            if container.is_alive():
                container.shutdown()
