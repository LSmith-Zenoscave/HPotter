import unittest
# from unittest.mock import MagicMock, call
from hpotter.docker_shell.shell import change_directory


class TestTelnet(unittest.TestCase):
    def test_empty_change_directory(self):
        self.assertEqual(change_directory('cd', '/'), '/')
        self.assertEqual(change_directory('cd', '/foo/bar'), '/foo/bar')

    def test_dotdot_change_directory(self):
        self.assertEqual(change_directory('cd ..', '/foo/bar'), '/foo')
        self.assertEqual(change_directory('cd ../..', '/foo/bar'), '/')
        self.assertEqual(change_directory('cd ../../', '/foo/bar'), '/')
        self.assertEqual(change_directory('cd ..', '/foo'), '/')
        self.assertEqual(change_directory('cd ..', '/'), '/')
        self.assertEqual(change_directory('cd ../', '/foo/bar'), '/foo')
        self.assertEqual(change_directory('cd ../baz', '/foo/bar'), '/foo/baz')

    def test_dot_change_directory(self):
        self.assertEqual(change_directory('cd .', '/'), '/')
        self.assertEqual(change_directory('cd .', '/foo/bar'), '/foo/bar')

    def test_mixed_dot_change_directory(self):
        self.assertEqual(change_directory('cd ./.', '/foo/bar'), '/foo/bar')
        self.assertEqual(change_directory('cd ././.', '/foo/bar'), '/foo/bar')
        self.assertEqual(change_directory('cd ./../.', '/foo/bar'), '/foo')
        self.assertEqual(change_directory('cd .././.', '/foo/bar'), '/foo')
        self.assertEqual(change_directory('cd ../../.', '/foo/bar'), '/')
        self.assertEqual(change_directory('cd ../../..', '/foo/bar'), '/')

    def test_absolute_change_directory(self):
        self.assertEqual(change_directory('cd /', '/foo/bar'), '/')
        self.assertEqual(change_directory('cd /', '/'), '/')

    def test_relative_change_directory(self):
        self.assertEqual(change_directory('cd etc', '/'), '/etc')
        self.assertEqual(change_directory('cd etc', '/etc'), '/etc/etc')
