import os
import shutil
import hvac
import responses
from unittest import TestCase
from pyauto.core import deploy
from pyauto.core import config
from pyauto.vault import config as vault_config
config.set_id_key('id')

dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
local = conf.local
vault = conf.vault


def expect_login():
    responses.add(responses.POST,
                  'https://localhost/v1/auth/approle/login',
                  json={'auth': {'client_token': 'abc123'}})


def expect_read():
    with open(os.path.join(dirname, 'key1.txt')) as f1, \
            open(os.path.join(dirname, 'key2.txt')) as f2:
        responses.add(responses.GET,
                      'https://localhost/v1/secret/prod/myenv1',
                      json={'data': {'key1': f1.read(), 'key2': f2.read()}})


def expect_write():
    responses.add(responses.PUT,
                  'https://localhost/v1/secret/prod/myenv1',
                  json={})


def setUpModule():
    local.init_workspace()


def tearDownModule():
    shutil.rmtree(local.workspace_dir)


class Vault(TestCase):
    def test_get_endpoint(self):
        prod = vault.get_endpoint('prod')
        self.assertIsInstance(prod, vault_config.Endpoint)

    def test_get_path(self):
        path = vault.get_path('prod_myenv1')
        self.assertIsInstance(path, vault_config.Path)

    @responses.activate
    def test_read_path(self):
        expect_login()
        expect_read()
        path = conf.get_resource('vault/read_path,prod_myenv1')
        self.assertIsInstance(path, dict)


class Endpoint(TestCase):
    @responses.activate
    def test_get_client(self):
        expect_login()
        endpoint = vault.get_endpoint('prod')
        client = endpoint.get_client()
        self.assertIsInstance(client, hvac.Client)


class Path(TestCase):
    @responses.activate
    def test_read(self):
        expect_login()
        expect_read()
        path = vault.get_path('prod_myenv1')
        self.assertIsInstance(path, vault_config.Path)
        data = path.read()
        self.assertIsInstance(data, dict)

    @responses.activate
    def test_write(self):
        expect_login()
        expect_read()
        expect_write()
        path = vault.get_path('prod_myenv1')
        self.assertIsInstance(path, vault_config.Path)
        data = path.read()
        self.assertIsInstance(data, dict)
        data = path.write(**data)
        self.assertIsInstance(data, dict)

    @responses.activate
    def test_download_file_mapping(self):
        expect_login()
        expect_read()
        path = vault.get_path('prod_myenv1')
        values = {
            name: open(filename).read()
            for name, filename in path.mapping.items()
        }
        filenames = path.download_file()
        self.assertTrue(os.path.isfile(filenames['key1']))
        self.assertTrue(os.path.isfile(filenames['key2']))
        for name, orig in values.items():
            value = open(filenames[name]).read()
            self.assertEqual(orig, value)

    @responses.activate
    def test_download_file(self):
        expect_login()
        expect_read()
        path = vault.get_path('prod_myenv2')
        filename = path.download_file()
        self.assertTrue(os.path.isfile(filename))

    @responses.activate
    def test_upload_file_mapping(self):
        expect_login()
        expect_read()
        expect_write()
        path = vault.get_path('prod_myenv1')
        self.assertIsInstance(path, vault_config.Path)
        path.download_file()
        res = path.upload_file()
        self.assertIsInstance(res, dict)

    @responses.activate
    def test_upload_file(self):
        expect_login()
        expect_read()
        expect_write()
        path = vault.get_path('prod_myenv2')
        self.assertIsInstance(path, vault_config.Path)
        path.download_file()
        res = path.upload_file()
        self.assertIsInstance(res, dict)
