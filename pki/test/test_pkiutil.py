import os
import six
from unittest import TestCase
from pyauto.pki import pkiutil

cleanup_files = []
dirname = os.path.dirname(os.path.abspath(__file__))

# DH
dh_example_file = os.path.join(dirname, 'samples/dh.pem')
dh_saved_example_file = os.path.join(dirname, 'saved_example_dh.pem')
dh_example = open(dh_example_file).read()
cleanup_files.append(dh_saved_example_file)

# TA
ta_saved_example_file = os.path.join(dirname, 'saved_example_ta.pem')
cleanup_files.append(ta_saved_example_file)

# RSA
rsa_passphrase = 'tehb3tspawss3rd'
rsa_example_file = os.path.join(dirname, 'samples/rsa.pem')
rsa_enc_example_file = os.path.join(dirname, 'samples/rsa_enc.pem')
rsa_pkcs1_example_file = os.path.join(dirname, 'samples/rsa_pkcs1.pem')
rsa_pub_example_file = os.path.join(dirname, 'samples/rsa.pub')
rsa_ssh_pub_example_file = os.path.join(dirname, 'samples/ssh-rsa.pub')
rsa_saved_example_file = os.path.join(dirname, 'saved_example_rsa.pem')
rsa_enc_saved_example_file = os.path.join(dirname, 'saved_example_rsa_enc.pem')
rsa_pkcs1_saved_example_file = os.path.join(
        dirname, 'saved_example_rsa_pkcs1.pem')
rsa_pub_saved_example_file = os.path.join(dirname, 'saved_example_rsa.pub')
rsa_example = open(rsa_example_file).read()
rsa_pub_example = open(rsa_pub_example_file).read()
rsa_ssh_pub_example = open(rsa_ssh_pub_example_file).read()
rsa_pkcs1_example = open(rsa_pkcs1_example_file).read()
rsa_pub_example = open(rsa_pub_example_file).read()
cleanup_files.append(rsa_saved_example_file)
cleanup_files.append(rsa_enc_saved_example_file)
cleanup_files.append(rsa_pkcs1_saved_example_file)
cleanup_files.append(rsa_pub_saved_example_file)

# CSR
csr_server_example_file = os.path.join(dirname, 'samples/server_csr.pem')
csr_client_example_file = os.path.join(dirname, 'samples/client_csr.pem')
csr_subca_example_file = os.path.join(dirname, 'samples/subca_csr.pem')
csr_server_saved_example_file = os.path.join(
        dirname, 'saved_example_server_csr.pem')
csr_client_saved_example_file = os.path.join(
        dirname, 'saved_example_client_csr.pem')
csr_subca_saved_example_file = os.path.join(
        dirname, 'saved_example_subca_csr.pem')
csr_server_example = open(csr_server_example_file).read()
csr_client_example = open(csr_client_example_file).read()
csr_subca_example = open(csr_subca_example_file).read()
cleanup_files.append(csr_server_saved_example_file)
cleanup_files.append(csr_client_saved_example_file)
cleanup_files.append(csr_subca_saved_example_file)

# Cert
crt_example_file = os.path.join(dirname, 'samples/crt.pem')
crt_ca_example_file = os.path.join(dirname, 'samples/crt_ca.pem')
crt_saved_example_file = os.path.join(dirname, 'saved_example_crt.pem')
crt_ca_saved_example_file = os.path.join(dirname, 'saved_example_crt_ca.pem')
crt_example = open(crt_example_file).read()
crt_ca_example = open(crt_ca_example_file).read()
cleanup_files.append(crt_saved_example_file)
cleanup_files.append(crt_ca_saved_example_file)

# CRL
crl_example_file = os.path.join(dirname, 'samples/crl.pem')
crl_saved_example_file = os.path.join(dirname, 'saved_example_crl.pem')
crl_example = open(crl_example_file).read()
cleanup_files.append(crl_saved_example_file)


def get_filename(fn):
    return os.path.join(dirname, fn)


def cleanup():
    for fn in cleanup_files:
        if os.path.isfile(fn):
            os.remove(fn)


class BaseTestCase(TestCase):
    def setUp(self):
        cleanup()

    def tearDown(self):
        cleanup()


class DHParam(BaseTestCase):

    def test_pem(self):
        dh = pkiutil.DHParam().set_file(dh_example_file).load()
        lines = dh.pem_str.split('\n')
        self.assertEqual(lines[0], pkiutil.BEGIN_DH_PARAMS)
        self.assertEqual(lines[-1], pkiutil.END_DH_PARAMS)
        for line in lines[1:-2]:
            self.assertEqual(len(line), 64)
        self.assertLessEqual(len(lines[-2]), 64)

    def test_load(self):
        dh = pkiutil.DHParam().set_file(dh_example_file).load()
        self.assertIsInstance(dh.pem, six.binary_type)

    def test_save(self):
        dh = pkiutil.DHParam().set_file(dh_saved_example_file)
        dh.load_pem(dh_example)
        dh.save()
        self.assertEqual(dh.pem_str.strip(),
                         dh_example.strip())


class TAKey(BaseTestCase):
    def test_generate(self):
        ta = pkiutil.TAKey().set_file(ta_saved_example_file).generate()
        self.assertTrue(os.path.isfile(ta.key_file))


class RSAKey(BaseTestCase):
    def test_generate(self):
        key = pkiutil.RSAKey().set_file(rsa_saved_example_file).generate()
        self.assertIsInstance(key.pem, six.binary_type)

    def test_load(self):
        key = pkiutil.RSAKey().set_file(rsa_example_file)
        key.load()
        self.assertIsInstance(key.pem, six.binary_type)

    def test_save(self):
        self.assertFalse(os.path.isfile(rsa_saved_example_file))
        key = pkiutil.RSAKey().set_file(rsa_saved_example_file)\
            .load_pem(rsa_example)
        key.save()
        self.assertTrue(os.path.isfile(rsa_saved_example_file))
        self.assertEqual(key.to_decrypted_pem_str().strip(),
                         rsa_example.strip())

    def test_load_encrypted(self):
        key = pkiutil.RSAKey()\
                .set_file(rsa_enc_example_file)\
                .set_passphrase(rsa_passphrase)
        key.load()
        self.assertEqual(key.to_decrypted_pem_str().strip(),
                         rsa_example.strip())

    def test_save_encrypted(self):
        key = pkiutil.RSAKey()\
                .set_file(rsa_enc_saved_example_file)\
                .load_pem(rsa_example)\
                .set_passphrase(rsa_passphrase)
        key.save()
        self.assertNotEqual(key.pem_str.strip(), rsa_example.strip())
        self.assertIn('ENCRYPTED', key.pem_str)

    def test_public(self):
        key = pkiutil.RSAKey()\
                .set_file(rsa_enc_saved_example_file)\
                .load_pem(rsa_example)\
                .set_passphrase(rsa_passphrase)
        self.assertIsInstance(key.public, pkiutil.RSAPubKey)


class RSAPubKey(BaseTestCase):
    def test_rsa_pub_save(self):
        pubkey = pkiutil.RSAPubKey()\
                .set_file(rsa_pub_saved_example_file)\
                .load_pem(rsa_pub_example)
        pubkey.save()
        self.assertTrue(os.path.isfile(rsa_pub_saved_example_file))
        self.assertEqual(pubkey.pem_str.strip(), rsa_pub_example.strip())

    def test_rsa_pub_load(self):
        pubkey = pkiutil.RSAPubKey().set_file(rsa_pub_example_file)
        pubkey.load()
        self.assertEqual(pubkey.pem_str.strip(), rsa_pub_example.strip())

    def test_rsa_ssh_str(self):
        pubkey = pkiutil.RSAPubKey().set_file(rsa_pub_example_file)
        pubkey.load()
        sshpubkey = pubkey.get_ssh_str('samples/ssh-rsa.pub')
        self.assertEqual(sshpubkey.strip(), rsa_ssh_pub_example.strip())


class CSR(BaseTestCase):
    def test_load(self):
        csr = pkiutil.CSR().set_file(csr_server_example_file).load()
        self.assertEqual(csr.pem_str.strip(), csr_server_example.strip())

    def test_create_server(self):
        key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        csr = pkiutil.CSR().set_file(csr_server_saved_example_file)
        csr.create_server('test srv CN', key)
        csr.save()
        self.assertTrue(os.path.isfile(csr_server_saved_example_file))
        self.assertIsNotNone(csr._csr)
        self.assertIn('CERTIFICATE REQUEST', csr.pem_str)

    def test_create_client(self):
        key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        csr = pkiutil.CSR().set_file(csr_client_saved_example_file)
        csr.create_client('test cli CN', key)
        csr.save()
        self.assertTrue(os.path.isfile(csr_client_saved_example_file))
        self.assertIsNotNone(csr._csr)
        self.assertIn('CERTIFICATE REQUEST', csr.pem_str)

    def test_create_subca(self):
        key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        csr = pkiutil.CSR().set_file(csr_subca_saved_example_file)
        csr.create_client('test sca CN', key)
        csr.save()
        self.assertTrue(os.path.isfile(csr_subca_saved_example_file))
        self.assertIsNotNone(csr._csr)
        self.assertIn('CERTIFICATE REQUEST', csr.pem_str)


class Cert(BaseTestCase):
    def test_create_ca(self):
        key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        crt = pkiutil.Cert().set_file(crt_ca_saved_example_file)
        crt.create_ca('my ca', 7300, key).save()
        self.assertTrue(os.path.isfile(crt_ca_saved_example_file))
        self.assertIsNotNone(crt._crt)
        self.assertIn('CERTIFICATE', crt.pem_str)

    def test_create(self):
        key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        csr = pkiutil.CSR().set_file(csr_server_example_file).load()
        ca_crt = pkiutil.Cert().set_file(crt_ca_example_file).load()
        crt = pkiutil.Cert().set_file(crt_saved_example_file)
        crt.create(csr, key, ca_crt, 7300).save()
        self.assertTrue(os.path.isfile(crt_saved_example_file))
        self.assertIsNotNone(crt._crt)
        self.assertIn('CERTIFICATE', crt.pem_str)


class CRL(BaseTestCase):
    def test_initialize(self):
        ca_key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        ca_crt = pkiutil.Cert().set_file(crt_ca_example_file).load()
        crl = pkiutil.CRL().set_file(crl_saved_example_file)
        crl.initialize(ca_key, ca_crt).save()
        self.assertTrue(os.path.isfile(crl_saved_example_file))
        self.assertIsNotNone(crl._crl)
        with open(crl_saved_example_file) as f:
            self.assertIn('X509 CRL', f.read())

    def test_revoke_cert(self):
        crt = pkiutil.Cert().set_file(crt_example_file).load()
        ca_key = pkiutil.RSAKey().set_file(rsa_example_file).load()
        ca_crt = pkiutil.Cert().set_file(crt_ca_example_file).load()
        crl = pkiutil.CRL().set_file(crl_example_file).load()
        crl.revoke_cert(crt, ca_key, ca_crt)
        crl.set_file(crl_saved_example_file).save()
        self.assertTrue(os.path.isfile(crl_saved_example_file))
        self.assertIsNotNone(crl._crl)
        with open(crl_saved_example_file) as f:
            self.assertIn('X509 CRL', f.read())

