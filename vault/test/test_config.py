import os
import sys
import mock
import shutil
import hvac
import responses
from six import StringIO
from unittest import TestCase
from pyauto.core import deploy
from pyauto.core import config
from pyauto.vault import config as vault_config
from pyauto.util import diffutil
config.set_id_key('id')

test_environ = {
    'VAULT_URL': 'http://localhost',
    'VAULT_SECRET_PATH': 'secret/mypath',
    'VAULT_SSL_VERIFY': 'false',
    'VAULT_ROLE_ID': 'role-id',
    'VAULT_SECRET_ID': 'secret-id',
    'VAULT_USERNAME': 'me',
    'VAULT_PASSWORD': 'youserpass',
}
os.environ.update(test_environ)

dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
local = conf.local
vault = conf.vault


def yngen(n):
    for i in range(n):
        if i % 2 == 0:
            yield 'y'
        else:
            yield 'n'


def expect_login():
    responses.add(responses.POST,
                  'https://localhost/v1/auth/approle/login',
                  json={'auth': {'client_token': 'abc123'}})


def expect_read(**data):
    if not data:
        with open(os.path.join(dirname, 'key1.txt')) as f1, \
                open(os.path.join(dirname, 'key2.txt')) as f2:
            data = {'key1': f1.read(), 'key2': f2.read()}
    responses.add(responses.GET,
                  'https://localhost/v1/secret/prod/myenv1',
                  json={'data': data})


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

    def test_endpoint_env(self):
        path = vault.get_endpoint('prodenv')
        for key, envname in path.items():
            if key.endswith('_env'):
                self.assertIn(envname, test_environ)
                real = path[key.replace('_env', '')]
                expected = test_environ[envname]
                if isinstance(real, bool):
                    if 'true' == expected:
                        self.assertTrue(real)
                    else:
                        self.assertFalse(real)
                else:
                    self.assertEqual(real, expected)

    @responses.activate
    def test_upload_confirm_diff(self):
        expect_login()
        expect_read(key1='def', key2='abc')
        expect_write()
        path = vault.get_path('prod_myenv1')

        output = StringIO()
        stdout_ = sys.stdout
        sys.stdout = output
        diffutil.raw_input = lambda _: 'y'
        path.upload_confirm_diff(plain=True)
        sys.stdout = stdout_
        self.assertEqual(output.getvalue().strip(), """
--- key1 [current]

+++ key1 [proposed]

@@ -1 +1 @@

-def
+abc
--- key2 [current]

+++ key2 [proposed]

@@ -1 +1 @@

-abc
+def
Approved  "key1"
Approved  "key2"
        """.strip())

    @responses.activate
    def test_download_confirm_diff(self):
        expect_login()
        expect_read(key1='bc', key2='def')
        expect_write()
        path = vault.get_path('prod_myenv1')

        output = StringIO()
        stdout_ = sys.stdout
        sys.stdout = output
        diffutil.raw_input = lambda _: 'n'
        path.download_confirm_diff(plain=True)
        sys.stdout = stdout_
        self.assertEqual(output.getvalue().strip(), """
--- key1 [current]

+++ key1 [proposed]

@@ -1 +1 @@

-abc
+bc

Declined  "key1"
No Change "key2"
        """.strip())

    @responses.activate
    def test_download_confirm_diff_union(self):
        expect_login()
        expect_read(key1='bc')
        expect_write()
        path = vault.get_path('prod_myenv1')

        output = StringIO()
        stdout_ = sys.stdout
        sys.stdout = output
        diffutil.raw_input = lambda _: 'n'
        path.download_confirm_diff(plain=True)
        sys.stdout = stdout_
        self.assertEqual(output.getvalue().strip(), """
--- key1 [current]

+++ key1 [proposed]

@@ -1 +1 @@

-abc
+bc
--- key2 [current]

+++ key2 [proposed]

@@ -1 +1 @@

-def
+
Declined  "key1"
Declined  "key2"
        """.strip())

    @responses.activate
    def test_download_confirm_diff_declined_and_preserved(self):
        expect_login()
        expect_read(key1='bc')
        expect_write()
        path = vault.get_path('prod_myenv1')

        gen = yngen(2)
        diffutil.raw_input = lambda _: next(gen)
        with mock.patch.object(vault_config.Path, 'save_mapping') as save:
            path.download_confirm_diff(plain=True)
            save.assert_called_once_with({'key1': 'bc', 'key2': 'def'})

    @responses.activate
    def test_upload_confirm_diff_declined_and_preserved(self):
        expect_login()
        expect_read(key1='bc', key2='abc')
        expect_write()
        path = vault.get_path('prod_myenv1')

        gen = yngen(2)
        diffutil.raw_input = lambda _: next(gen)
        with mock.patch.object(vault_config.Path, 'write') as save:
            path.upload_confirm_diff(plain=True)
            save.assert_called_once_with(**{'key1': 'abc', 'key2': 'abc'})
