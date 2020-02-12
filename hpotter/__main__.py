"""HPotter HoneyPot runner.
"""

import signal
import time
import yaml

from hpotter.logger import LOGGER
from hpotter.plugins.listen_thread import ListenThread
from hpotter.db import DB


# https://stackoverflow.com/questions/18499497/how-to-process-sigterm-signal-gracefully
# pylint: disable=too-few-public-methods
class GracefulKiller:
    """Signal Handler for graceful exiting.
    """
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """Set the exit flag when signaled.
        """
        del signum
        del frame
        LOGGER.info('In exit_gracefully')
        self.kill_now = True


class HP():
    """HoneyPot executor class.
    """
    def __init__(self):
        self.db_conn = DB()
        self.listen_threads = []

    def startup(self):
        """Satrt the Honey Pot server listen threads.
        """
        self.db_conn.open()

        with open('plugins.yml') as conf_file:
            for config in yaml.safe_load_all(conf_file):
                thread = ListenThread(self.db_conn, config)
                self.listen_threads.append(thread)
                thread.start()

    def shutdown(self):
        """Shutdown and close all server threads.
        """
        self.db_conn.close()

        for thread in self.listen_threads:
            if thread.is_alive():
                thread.shutdown()


def main():
    """Main execution method.
    """
    hpotter = HP()
    hpotter.startup()

    killer = GracefulKiller()
    while not killer.kill_now:
        time.sleep(5)

    hpotter.shutdown()


if __name__ == "__main__":
    main()
