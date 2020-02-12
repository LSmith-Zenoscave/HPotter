"""plugins/one_way_thread.py test suite
"""

import unittest
from unittest.mock import call
from hpotter.plugins.one_way_thread import OneWayThread


class TestOneWayThread(unittest.TestCase):
    """OneWayThread Test Driver
    """

    # pylint: disable=R0201
    def test_send_single(self):
        """Should create a single call to the request thread
        """
        request = unittest.mock.Mock()
        request.recv.side_effect = \
            [bytes(i, 'utf-8') for i in 'a']+[bytes('', 'utf-8')]
        response = unittest.mock.Mock()

        db_conn = unittest.mock.Mock()
        owt = OneWayThread(db_conn, request, response, {}, 'request', None)
        owt.run()

        response.sendall.assert_has_calls([call(b'a')])

    def test_limit(self):
        """Should not send more than the limit of calls to the thread
        """
        request = unittest.mock.Mock()
        request.recv.side_effect = [bytes(i, 'utf-8') for i in 'aa']
        response = unittest.mock.Mock()

        db_conn = unittest.mock.Mock()
        owt = OneWayThread(db_conn, request, response,
                           {'request_length': 2},
                           'request', None)
        owt.run()

        response.sendall.assert_has_calls([call(b'a')])
