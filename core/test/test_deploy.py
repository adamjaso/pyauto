import os
import six
import sys
import shutil
from six import StringIO
from base64 import b64encode
from unittest import TestCase
from pyauto.core import deploy, config


config_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'example/config.example.yml')
logs_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'example/testlogs')
action = 'do_things'
action_with_subtasks = 'do_all_things'


def tearDownModule():
    if os.path.isdir(logs_dir):
        shutil.rmtree(logs_dir)


class Command(TestCase):
    def setUp(self):
        pass

    def test_init(self):
        cmd = deploy.Command(config_file, [action])
        self.assertTrue(os.path.isfile(cmd.config_file))
        self.assertIsInstance(cmd.config, config.Config)
        self.assertIsInstance(cmd.action, list)

    def test_from_args(self):
        cmd = deploy.Command.from_args(args=['-c', config_file])
        self.assertEqual(cmd.config_file, config_file)
        self.assertIsInstance(cmd, deploy.Command)

    def test_config_inspect(self):
        cmd = deploy.Command.from_args(args=['-c', config_file, '-i'])
        stdout = capture_output(cmd)
        self.assertEqual(stdout, 'ZXhhbXBsZS5jb21tYW5kcy5kb190aGluZyAoIHRoaW5nX2lkICkKZXhhbXBsZS5jb21tYW5kcy5nZXRfbGlzdCAoIHRoaW5nX2lkICkKZXhhbXBsZS5jb21tYW5kcy5nZXRfdGhpbmcgKCB0aGluZ19pZCApCg==')

    def test_action_inspect(self):
        cmd = deploy.Command.from_args(args=['-c', config_file, '-i', action])
        stdout = capture_output(cmd)
        self.assertEqual(stdout, 'ZG9fdGhpbmdzICggICkKICAgIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCB0aGluZzEgKQogICAgZXhhbXBsZS5jb21tYW5kcy5kb190aGluZyAoIHRoaW5nMiApCiAgICBleGFtcGxlLmNvbW1hbmRzLmRvX3RoaW5nICggYWJjICkKICAgIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCBkZWYgKQo=')

    def test_config_tree(self):
        cmd = deploy.Command.from_args(args=['-c', config_file, '-t', action])
        stdout = capture_output(cmd)
        self.assertEqual(stdout, 'ZG9fdGhpbmdzOgotIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCB0aGluZzEgKQotIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCB0aGluZzIgKQotIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCBhYmMgKQotIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCBkZWYgKQoK')

    def test_action_quiet(self):
        cmd = deploy.Command.from_args(args=['-c', config_file, '-q', action])
        stdout = capture_output(cmd)
        self.assertEqual(stdout, 'T3JkZXJlZERpY3QoWygnaWQnLCAndGhpbmcxJyldKQoKT3JkZXJlZERpY3QoWygnaWQnLCAndGhpbmcyJyldKQoKT3JkZXJlZERpY3QoWygnaWQnLCAnYWJjJyldKQoKT3JkZXJlZERpY3QoWygnaWQnLCAnZGVmJyldKQoK')

    def test_execute_parallel(self):
        cmd = deploy.Command.from_args(args=[
            '-c', config_file, action, action, '--parallel', logs_dir])
        capture_output(cmd)


class ParallelCommand(TestCase):
    def test_init(self):
        deploy.Command.from_args(args=[
            '-c', config_file, action, action, '--parallel', logs_dir])

    def test_execute_single_task(self):
        cmd = deploy.Command.from_args(args=[
            '-c', config_file, action_with_subtasks, '--parallel', logs_dir])
        capture_output(cmd)
        verify_parallel_tree(self)

    def test_execute(self):
        cmd = deploy.Command.from_args(args=[
            '-c', config_file, action, action, '--parallel', logs_dir])
        capture_output(cmd)
        verify_parallel_tree(self)


def verify_parallel_tree(self):
    for time_dir in os.listdir(logs_dir):
        time_dir = os.path.join(logs_dir, time_dir)
        for action_log in os.listdir(time_dir):
            action_log = os.path.join(time_dir, action_log)
            self.assertEqual(b64encode(open(action_log, 'rb').read()), b'LS0tLS0gZXhhbXBsZS5jb21tYW5kcy5kb190aGluZyAoIHRoaW5nMSApIC0tLS0tCmRvX3RoaW5nLHRoaW5nMSA9IE9yZGVyZWREaWN0KFsoJ2lkJywgJ3RoaW5nMScpXSkKCi0tLS0tIGV4YW1wbGUuY29tbWFuZHMuZG9fdGhpbmcgKCB0aGluZzIgKSAtLS0tLQpkb190aGluZyx0aGluZzIgPSBPcmRlcmVkRGljdChbKCdpZCcsICd0aGluZzInKV0pCgotLS0tLSBleGFtcGxlLmNvbW1hbmRzLmRvX3RoaW5nICggYWJjICkgLS0tLS0KZG9fdGhpbmcsYWJjID0gT3JkZXJlZERpY3QoWygnaWQnLCAnYWJjJyldKQoKLS0tLS0gZXhhbXBsZS5jb21tYW5kcy5kb190aGluZyAoIGRlZiApIC0tLS0tCmRvX3RoaW5nLGRlZiA9IE9yZGVyZWREaWN0KFsoJ2lkJywgJ2RlZicpXSkKCg==')


def capture_output(cmd):
    tmp = sys.stdout
    out = StringIO()
    sys.stdout = out
    cmd.execute()
    sys.stdout = tmp
    if six.PY3:
        out = b64encode(six.binary_type(out.getvalue(), 'utf-8'))
        return out.decode('utf-8')
    else:
        out = b64encode(out.getvalue())
        return out
