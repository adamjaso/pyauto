import os
from unittest import TestCase
from pyauto.secret import store, utils

credentials_file = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'credentials.json'
)


def tearDownModule():
    if os.path.isfile(credentials_file):
        os.remove(credentials_file)


class Store(TestCase):
    def setUp(self):
        self.store = store.Store(credentials_file)

    def tearDown(self):
        if os.path.isfile(credentials_file):
            os.remove(credentials_file)

    def test_load_save(self):
        self.assertFalse(os.path.isfile(credentials_file))
        self.store.load()
        self.assertDictEqual(self.store.data, {})
        self.store.save()
        self.assertTrue(os.path.isfile(credentials_file))

    def test_get(self):
        with self.assertRaises(Exception):
            self.store.get('apps', 'my_app', 'config', 'secret')
        value = self.store.get('apps', 'my_app', 'config', 'secret', utils.uuid)
        expected = self.store.get('apps', 'my_app', 'config', 'secret')
        self.assertEqual(value, expected)

    def test_delete(self):
        value = self.store.get('apps', 'my_app', 'config', 'secret', utils.uuid)
        expected = self.store.delete('apps', 'my_app', 'config', 'secret')
        self.assertIsNotNone(expected)
        with self.assertRaises(Exception):
            self.store.get('apps', 'my_app', 'config', 'secret')

    def test_get_dict(self):
        template = {
            'config': {
                'secret': utils.uuid
            }
        }
        value = self.store.get_dict('apps', 'my_app', template)
        expected = self.store.get_dict('apps', 'my_app', template)
        self.assertDictEqual(value, expected)

    def test_delete(self):
        self.store.get('apps', 'my_app', 'config', 'secret', utils.uuid)
        self.store.get('apps', 'my_app', 'config', 'secret')
        self.store.delete('apps', 'my_app', 'config', 'secret')
        with self.assertRaises(Exception):
            self.store.get('apps', 'my_app', 'config', 'secret')

    def test_delete_keys_all(self):
        template = {
            'config': {
                'secret1': utils.uuid,
                'secret2': utils.uuid
            }
        }
        self.store.get_dict('apps', 'my_app', template)
        self.store.get('apps', 'my_app', 'config', 'secret1')
        self.store.get('apps', 'my_app', 'config', 'secret2')
        self.store.delete_keys('apps', 'my_app', 'config', None)
        with self.assertRaises(Exception):
            self.store.get('apps', 'my_app', 'config', 'secret1')
        with self.assertRaises(Exception):
            self.store.get('apps', 'my_app', 'config', 'secret2')

    def test_delete_keys_one(self):
        template = {
            'config': {
                'secret1': utils.uuid,
                'secret2': utils.uuid
            }
        }
        self.store.get_dict('apps', 'my_app', template)
        self.store.get('apps', 'my_app', 'config', 'secret1')
        self.store.get('apps', 'my_app', 'config', 'secret2')
        self.store.delete_keys('apps', 'my_app', 'config', ['secret1'])
        self.store.get('apps', 'my_app', 'config', 'secret2')
        with self.assertRaises(Exception):
            self.store.get('apps', 'my_app', 'config', 'secret1')

    def test_get_group(self):
        group = self.store.get_group('apps', 'my_app')
        self.assertIsInstance(group, store.Group)


class GroupDefinition(TestCase):
    def setUp(self):
        self.store = store.Store(credentials_file)
        self.group = self.store.get_group('apps', 'my_app')

    def tearDown(self):
        if os.path.isfile(credentials_file):
            os.remove(credentials_file)

    def test_init(self):
        group_def = store.GroupDefinition('auth', {
            'config': {
                'secret1': 'pyauto.secret.utils.uuid',
                'secret2': 'pyauto.secret.utils.uuid',
            }
        })
        func_type = type(group_def.definition['config']['secret1']).__name__
        self.assertEqual('function', func_type)
