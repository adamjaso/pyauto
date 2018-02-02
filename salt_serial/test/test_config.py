import os
import sys
import six
import shutil
import subprocess
from unittest import TestCase
from collections import OrderedDict
from pyauto.util import yamlutil
from pyauto.core import deploy
from pyauto.salt_serial import config as ss_config
dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
local = conf.local
salt_serial = conf.salt_serial

states_serialized_file = local.get_workspace_path('states.txt')
pillar_serialized_file = local.get_workspace_path('pillar.txt')


def base64_decode_cmd():
    if 'darwin' == sys.platform:
        return 'base64 -D'
    else:
        return 'base64 -d'


def check_serialization(test, serialized_file):
    p = subprocess.Popen(
        'cat {0} | {1} | gzip -d | tar tf -'
            .format(serialized_file, base64_decode_cmd()),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=sys.stderr)
    p.communicate()
    test.assertEqual(p.returncode, 0)
    return p


def setUpModule():
    if not os.path.isdir(local.get_workspace_path()):
        os.makedirs(local.get_workspace_path())


def tearDownModule():
    shutil.rmtree(local.get_workspace_path())


class Salt(TestCase):
    def test_init(self):
        self.assertIsInstance(salt_serial.pillar, ss_config.Pillar)
        self.assertIsInstance(salt_serial.states, ss_config.States)


class States(TestCase):
    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(states_serialized_file):
            os.unlink(states_serialized_file)

    def test_get_serialized(self):
        serialized = salt_serial.states.get_serialized()
        with open(states_serialized_file, 'w') as f:
            f.write(serialized)

        check_serialization(self, states_serialized_file)


class Pillar(TestCase):
    @classmethod
    def tearDownClass(cls):
        if os.path.isfile(pillar_serialized_file):
            os.unlink(pillar_serialized_file)

    def test_get_serialized(self):
        pillar = yamlutil.dump_dict(OrderedDict([('abc', '123')]))
        if six.PY3:
            pillar_bytes = six.binary_type(pillar, 'utf-8')
        serialized = salt_serial.pillar.get_serialized([
            ('base', lambda fh, pil: fh.write(pillar_bytes)),
        ])
        with open(pillar_serialized_file, 'w') as f:
            f.write(serialized)

        check_serialization(self, pillar_serialized_file)

