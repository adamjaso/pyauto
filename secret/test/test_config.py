import os
from unittest import TestCase
from pyauto.core import deploy, config
from pyauto.secret import config as secret_config

dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
secret = conf.secret

credentials_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'credentials.json'
)

def tearDownModule():
    if os.path.isfile(credentials_file):
        os.remove(credentials_file)

class Secret(TestCase):
    def test_get_group(self):
        group = secret.get_group('api')
        self.assertIsInstance(group, secret_config.GroupDefinition)
        with self.assertRaises(Exception):
            secret.get_group('abc')

    def test_get_value(self):
        value = secret.get_value('web', 'webapp1', 'manifest', 'id')
        expected = secret.get_value('web', 'webapp1', 'manifest', 'id')
        self.assertEqual(value, expected)
        value = secret.get_value('web', 'webapp1', 'manifest')
        expected = secret.get_value('web', 'webapp1', 'manifest')
        self.assertDictEqual(value, expected)
        value = secret.get_value('web', 'webapp1')
        expected = secret.get_value('web', 'webapp1')
        self.assertDictEqual(value, expected)

    def test_delete_value(self):
        value = secret.get_value('api', 'webapp1', 'manifest', 'id')
        secret.delete_value('api', 'webapp1', 'manifest', 'id')
        expected = secret.get_value('api', 'webapp1', 'manifest', 'id')
        self.assertNotEqual(value, expected)
        value = secret.get_value('api', 'webapp1', 'manifest')
        secret.delete_value('api', 'webapp1', 'manifest')
        expected = secret.get_value('api', 'webapp1', 'manifest')
        self.assertNotEqual(value['id'], expected['id'])
        value = secret.get_value('api', 'webapp1')
        secret.delete_value('api', 'webapp1')
        expected = secret.get_value('api', 'webapp1')
        self.assertNotEqual(value['manifest']['id'],
                                expected['manifest']['id'])

