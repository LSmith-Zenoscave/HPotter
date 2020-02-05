import unittest
from unittest.mock import call
from hpotter.plugins.generic import OneWayThread


class TestGeneric(unittest.TestCase):
    # pylint: disable=R0201
    def test_no_data(self):
        source = unittest.mock.Mock()
        dest = unittest.mock.Mock()
        source.recv.side_effect = ""

        OneWayThread(source, dest).run()

        source.sendall.assert_has_calls = [call.recv(4096), call.close()]
        dest.sendall.assert_has_calls = [call.close()]

    def test_simple_data(self):
        source = unittest.mock.Mock()
        dest = unittest.mock.Mock()
        source.recv.side_effect = b'fubar'

        OneWayThread(source, dest).run()

        source.sendall.assert_has_calls = [call.recv(4096), call.close()]
        dest.sendall.assert_has_calls = [
            call.sendall('f'),
            call.sendall('u'),
            call.sendall('b'),
            call.sendall('a'),
            call.sendall('r'),
            call.close()]

    def test_too_many(self):
        source = unittest.mock.MagicMock()
        dest = unittest.mock.MagicMock()
        source.recv.return_value = b'fubar'

        OneWayThread(source, dest, limit=2).run()

        source.sendall.assert_has_calls = [call.recv(4096),
                                           call.recv(4096), call.close()]
        dest.sendall.assert_has_calls = [
            call.sendall('f'),
            call.sendall('u'),
            call.close()]
