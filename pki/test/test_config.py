import os
import six
import shutil
from uuid import uuid4
from unittest import TestCase
from pyauto.core import __version__
from pyauto.core import deploy, config as pyauto_config
from pyauto.pki import config, pkiutil
from test_pkiutil import *
pyauto_config.set_id_key('id')


dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
local = conf.local
pki = conf.pki


ca_profile_tag = 'ca1'
profile_tag = 'user1'

example_client_id = str(uuid4())
example_key_tag = str(uuid4())
example_key_pass = 'abc123'
example_req_tag = str(uuid4())
example_crt_tag = str(uuid4())
example_crl_tag = str(uuid4())
example_dh_tag = str(uuid4())
example_ta_tag = str(uuid4())


def cleanup():
    if os.path.isdir(local.workspace_dir):
        shutil.rmtree(local.workspace_dir)


class PKI(TestCase):
    def tearDown(self):
        cleanup()

    def test_get_ca_profile(self):
        ca_profile = pki.get_ca_profile(ca_profile_tag)
        self.assertIsInstance(ca_profile, config.CAProfile)

    def test_get_profile(self):
        profile = pki.get_profile(profile_tag)
        self.assertIsInstance(profile, config.Profile)

    def test_init(self):
        self.assertIsInstance(pki.ca_profiles, list)
        self.assertIsInstance(pki.profiles, list)


class CAProfile(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ca_profile = pki.get_ca_profile(ca_profile_tag)
        cls.ca_profile.init_pki()
        cls.ca_profile.create_ca()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def test_create_ca(self):
        ca = self.ca_profile
        self.assertTrue(os.path.isfile(ca.ca_key_file))
        self.assertTrue(os.path.isfile(ca.ca_cert_file))
        self.assertTrue(os.path.isfile(ca.crl_file))
        self.assertIsInstance(ca.crl, pkiutil.CRL)
        self.assertIsInstance(ca.ca_key, pkiutil.RSAKey)
        self.assertIsInstance(ca.ca_cert, pkiutil.Cert)

    def test_load_key(self):
        ca = self.ca_profile
        key = ca.load_key(ca.ca_key_file, ca.passphrase)
        self.assertIsInstance(key, pkiutil.RSAKey)

    def test_load_cert(self):
        ca = self.ca_profile
        crt = ca.load_cert(ca.ca_cert_file)
        self.assertIsInstance(crt, pkiutil.Cert)

    def test_load_crl(self):
        ca = self.ca_profile
        crl = ca.load_crl(ca.crl_file)
        self.assertIsInstance(crl, pkiutil.CRL)

    def test_create_key(self):
        ca = self.ca_profile
        key = ca.create_key(example_key_tag, 2048, example_key_pass)
        self.assertIsInstance(key, pkiutil.RSAKey)

    def test_create_req(self):
        ca = self.ca_profile
        key = ca.create_key(example_key_tag, 2048, example_key_pass)
        self.assertIsInstance(key, pkiutil.RSAKey)
        for req_type in ['client', 'server', 'subca']:
            name = '_'.join([req_type, example_req_tag])
            req = ca.create_req(
                req_type, name, example_key_tag,
                name, example_key_pass)
            self.assertIsInstance(req, pkiutil.CSR)

    def test_create_cert(self):
        ca = self.ca_profile
        key = ca.create_key(example_key_tag, 2048, example_key_pass)
        self.assertIsInstance(key, pkiutil.RSAKey)
        for req_type in ['client', 'server', 'subca']:
            name = '_'.join([req_type, example_req_tag])
            req = ca.create_req(
                req_type, name, example_key_tag,
                name, example_key_pass)
            self.assertIsInstance(req, pkiutil.CSR)

            crt = ca.create_cert(name, example_crt_tag, 365)
            self.assertIsInstance(crt, pkiutil.Cert)

    def test_revoke_cert(self):
        ca = self.ca_profile
        key = ca.create_key(example_key_tag, 2048, example_key_pass)
        self.assertIsInstance(key, pkiutil.RSAKey)
        for req_type in ['client', 'server', 'subca']:
            name = '_'.join([req_type, example_req_tag])
            req = ca.create_req(
                req_type, name, example_key_tag,
                name, example_key_pass)
            self.assertIsInstance(req, pkiutil.CSR)

            crt = ca.create_cert(name, example_crt_tag, 365)
            self.assertIsInstance(crt, pkiutil.Cert)

            crl = ca.revoke_cert(example_crt_tag)
            self.assertIsInstance(crl, pkiutil.CRL)

    def test_create_profile(self):
        ca = self.ca_profile
        for req_type in ['client', 'server', 'subca']:
            name = '_'.join([req_type, example_req_tag])
            key, csr, crt = ca.create_profile(
                req_type, example_client_id, name, 2048, 365, example_key_pass)
            self.assertIsInstance(key, pkiutil.RSAKey)
            self.assertIsInstance(csr, pkiutil.CSR)
            self.assertIsInstance(crt, pkiutil.Cert)
            self.assertTrue(os.path.isfile(key.key_file))
            self.assertTrue(os.path.isfile(csr._file))
            self.assertTrue(os.path.isfile(crt._file))


class Profile(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ca_profile = pki.get_ca_profile(ca_profile_tag)
        cls.ca_profile.init_pki()
        cls.ca_profile.create_ca()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def test_create(self):
        profile = pki.get_profile(profile_tag)
        key, csr, crt = profile.create()
        self.assertIsInstance(key, pkiutil.RSAKey)
        self.assertIsInstance(csr, pkiutil.CSR)
        self.assertIsInstance(crt, pkiutil.Cert)
        self.assertTrue(os.path.isfile(key.key_file))
        self.assertTrue(os.path.isfile(csr._file))
        self.assertTrue(os.path.isfile(crt._file))

    def test_revoke(self):
        profile = pki.get_profile(profile_tag)
        crl = profile.revoke()
        self.assertIsInstance(crl, pkiutil.CRL)
