import re
import os
import six
from base64 import b64encode, b64decode
from datetime import datetime
from datetime import timedelta
from Crypto.Util import asn1
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.x509.extensions import AuthorityKeyIdentifier, _key_identifier_from_public_key
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, dh
from cryptography.hazmat.primitives.serialization import load_pem_private_key, Encoding
from . import sshutil


BEGIN_DH_PARAMS = '-----BEGIN DH PARAMETERS-----'
END_DH_PARAMS = '-----END DH PARAMETERS-----'


def dh_decode(pemstr):
    pemstr = pemstr.strip().split('\n')
    if BEGIN_DH_PARAMS != pemstr[0]:
        raise Exception('Invalid PEM begin')
    if END_DH_PARAMS != pemstr[-1]:
        raise Exception('Invalid PEM end')
    enc64 = ''.join(pemstr[1:-1])
    derstr = b64decode(enc64)
    derseq = asn1.DerSequence()
    derseq.decode(derstr)
    return [i for i in derseq]


def dh_encode(p, g):
    derseq = asn1.DerSequence()
    derseq.append(p)
    derseq.append(g)
    derstr = derseq.encode()
    enc64 = b64encode(derstr)
    parts = [BEGIN_DH_PARAMS]
    for i in range(0, len(enc64), 64):
        row = enc64[i:i+64]
        if six.PY3:
            row = row.decode('ascii')
        parts.append(row)
    parts.append(END_DH_PARAMS)
    parts = os.linesep.join(parts)
    if six.PY3:
        return six.binary_type(parts, 'ascii')
    else:
        return parts


def build_aki(ca_cert):
    return AuthorityKeyIdentifier(
            _key_identifier_from_public_key(ca_cert.public_key()),
            [x509.DirectoryName(ca_cert.subject)],
            ca_cert.serial_number)


class DHParam(object):
    _file = None
    _dh = None

    def generate(self, key_size=2048):
        key_size = int(key_size)
        self._dh = dh.generate_parameters(
            generator=2, key_size=key_size, backend=default_backend())
        return self

    def set_file(self, pem_file):
        self._file = pem_file
        return self

    def _assert_file(self):
        if self._file is None:
            return Exception('DHParam file is not set')

    def load(self):
        self._assert_file()
        with open(self._file) as f:
            self.load_pem(f.read())
        return self

    def save(self, overwrite=False):
        self._assert_file()
        if os.path.isfile(self._file) and not overwrite:
            raise Exception('DHParam file already exists')
        with open(self._file, 'wb') as f:
            f.write(self.pem)
        return self

    def load_pem(self, pemstr):
        dhpnums = dh_decode(pemstr)
        n = dh.DHParameterNumbers(*dhpnums)
        self._dh = n.parameters(default_backend())
        return self

    @property
    def pem(self):
        if self._dh is None:
            raise Exception('Internal DHParam is not set')
        n = self._dh.parameter_numbers()
        return dh_encode(n.p, n.g)

    @property
    def pem_str(self):
        if not six.PY3:
            return self.pem
        else:
            return six.text_type(self.pem.decode('ascii'))


class TAKey(object):
    _key_file = None
    _openvpn_path = 'openvpn'

    def set_openvpn_path(self, openvpn_path):
        self._openvpn_path = openvpn_path
        return self

    def set_file(self, key_file):
        self._key_file = key_file
        return self

    def generate(self, overwrite=False):
        if not os.path.isfile(self.key_file) or overwrite:
            os.system(self.cmd)
            if not os.path.isfile(self.key_file):
                raise Exception('Key file was not generated! {0}'.format(self.key_file))
        return self

    @property
    def cmd(self):
        return ' '.join([
            self.openvpn_path, '--genkey', '--secret', self.key_file])

    @property
    def key_file(self):
        if re.search('^[^a-zA-Z0-9\-\._\/]+$', self._key_file):
            raise Exception('Invalid filename: {0}'.format(self._key_file))
        return self._key_file

    @property
    def openvpn_path(self):
        if re.search('^[^a-zA-Z0-9\-\._\/]+$', self._openvpn_path):
            raise Exception('Invalid filename: {0}'.format(self._openvpn_path))
        return self._openvpn_path

    @property
    def pem(self):
        with open(self.key_file) as f:
            return f.read()


class RSAPubKey(object):
    key_file = None
    _rsa = None

    @property
    def public(self):
        return self._rsa

    @property
    def size(self):
        return self._rsa.key_size

    @property
    def pem(self):
        if self._rsa is None:
            raise Exception('No key is set')
        return self._rsa.public_bytes(
            encoding=Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    @property
    def pem_str(self):
        if not six.PY3:
            return self.pem
        else:
            return six.text_type(self.pem.decode('ascii'))

    def get_ssh_str(self, comment=None):
        numbers = self._rsa.public_numbers()
        pk = sshutil.SshRsaPubKey(comment=comment)
        pk.keydata = sshutil.Keydata(exp=numbers.e, modulus=numbers.n)
        return pk.encode()

    def _assert_file(self):
        if self.key_file is None:
            raise Exception('No key file was found')

    def set_file(self, key_file):
        self.key_file = key_file
        return self

    def load_pem(self, pemstr):
        if six.PY3:
            pemstr = six.binary_type(pemstr.encode('utf-8'))
        self._rsa = serialization.load_pem_public_key(
            pemstr,
            backend=default_backend()
        )
        return self

    def load(self):
        self._assert_file()
        with open(self.key_file) as f:
            self.load_pem(f.read())
        return self

    def save(self, overwrite=False):
        self._assert_file()
        if os.path.isfile(self.key_file) and not overwrite:
            fk = RSAPubKey().set_file(self.key_file).load()
            if fk.to_decrypted_pem() != self.to_decrypted_pem():
                raise Exception('Key file exists and does not match')
        else:
            with open(self.key_file, 'wb') as f:
                f.write(self.pem)
        return self


class RSAKey(object):
    key_file = None
    passphrase = None
    _rsa = None

    @property
    def private(self):
        return self._rsa

    @property
    def size(self):
        return self._rsa.key_size

    @property
    def public_pem(self):
        if self._rsa is None:
            raise Exception('No key is set')
        return self._rsa.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @property
    def public(self):
        pub = RSAPubKey()
        pub._rsa = self._rsa.public_key()
        return pub

    @property
    def pem(self):
        if self._rsa is None:
            raise Exception('No key is set')
        if self.passphrase:
            ea = serialization.BestAvailableEncryption(self.passphrase)
        else:
            ea = serialization.NoEncryption()
        return self._rsa.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=ea
        )

    @property
    def pem_str(self):
        if not six.PY3:
            return self.pem
        else:
            return six.text_type(self.pem.decode('ascii'))

    @property
    def traditional_pem(self):
        if self._rsa is None:
            raise Exception('No key is set')
        return self._rsa.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

    @property
    def traditional_pem_str(self):
        if not six.PY3:
            return self.traditional_pem
        else:
            return six.text_type(self.traditional_pem.decode('ascii'))

    def set_file(self, key_file):
        self.key_file = key_file
        return self

    def _assert_file(self):
        if self.key_file is None:
            raise Exception('No key file was found')

    def set_passphrase(self, passphrase):
        if passphrase is not None and six.PY3 and \
                not isinstance(passphrase, six.binary_type):
            passphrase = six.binary_type(passphrase, 'utf8')
        self.passphrase = passphrase
        return self

    def generate(self, key_size=2048):
        self._rsa = rsa.generate_private_key(65537, int(key_size), backend=default_backend())
        return self

    def load(self):
        self._assert_file()
        with open(self.key_file) as f:
            self.load_pem(f.read())
        return self

    def save(self, overwrite=False):
        self._assert_file()
        if os.path.isfile(self.key_file) and not overwrite:
            fk = RSAKey().set_file(self.key_file).set_passphrase(self.passphrase).load()
            if fk.to_decrypted_pem() != self.to_decrypted_pem():
                raise Exception('Key file exists and does not match')
        else:
            with open(self.key_file, 'wb') as f:
                f.write(self.pem)
        return self

    def load_pem(self, pemstr):
        if six.PY3:
            pemstr = six.binary_type(pemstr.encode('utf-8'))
        self._rsa = serialization.load_pem_private_key(
            pemstr,
            password=self.passphrase,
            backend=default_backend()
        )
        return self

    def to_decrypted_pem(self):
        if self._rsa is None:
            raise Exception('No key is set')
        return self._rsa.private_bytes(
            encoding=Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

    def to_decrypted_pem_str(self):
        if not six.PY3:
            return self.to_decrypted_pem()
        else:
            return six.text_type(self.to_decrypted_pem().decode('ascii'))


class CSR(object):

    _csr = None
    _file = None

    @property
    def pem(self):
        if self._csr is None:
            raise Exception('Internal CSR is not set')
        return self._csr.public_bytes(Encoding.PEM)

    @property
    def pem_str(self):
        if not six.PY3:
            return self.pem
        else:
            return six.text_type(self.pem.decode('ascii'))

    def set_file(self, csr_file):
        self._file = csr_file
        return self

    def _assert_file(self):
        if self._file is None:
            raise Exception('No CSR file is set')

    def save(self, overwrite=False):
        self._assert_file()
        if os.path.isfile(self._file) and not overwrite:
            raise Exception('CSR file already exists')
        with open(self._file, 'wb') as f:
            f.write(self.pem)
        return self

    def load(self):
        self._assert_file()
        with open(self._file) as f:
            data = f.read()
            if six.PY3:
                data = six.binary_type(data.encode('utf-8'))
            self._csr = x509.load_pem_x509_csr(data, backend=default_backend())
        return self

    def create_server(self, common_name, rsa_key):
        key_ = load_pem_private_key(
                rsa_key.to_decrypted_pem(), password=None, backend=default_backend())
        builder = x509.CertificateSigningRequestBuilder()\
            .subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, six.text_type(common_name))]))\
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key_.public_key()), critical=False)\
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=False)\
            .add_extension(
                x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)\
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True, content_commitment=False, key_encipherment=True,
                    data_encipherment=False, key_agreement=False, key_cert_sign=False,
                    crl_sign=False, encipher_only=False, decipher_only=False), critical=False)
        csr = builder.sign(key_, hashes.SHA256(), default_backend())
        self._csr = csr
        return self

    def create_client(self, common_name, rsa_key):
        key_ = load_pem_private_key(
                rsa_key.to_decrypted_pem(), password=None, backend=default_backend())
        builder = x509.CertificateSigningRequestBuilder()\
            .subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, six.text_type(common_name))]))\
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key_.public_key()), critical=False)\
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=False)\
            .add_extension(
                x509.ExtendedKeyUsage([x509.ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False)\
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True, content_commitment=False, key_encipherment=False,
                    data_encipherment=False, key_agreement=False, key_cert_sign=False,
                    crl_sign=False, encipher_only=False, decipher_only=False), critical=False)
        csr = builder.sign(key_, hashes.SHA256(), default_backend())
        self._csr = csr
        return self

    def create_subca(self, common_name, rsa_key):
        key_ = load_pem_private_key(
                rsa_key.to_decrypted_pem(), password=None, backend=default_backend())
        builder = x509.CertificateSigningRequestBuilder()\
            .subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, six.text_type(common_name))]))\
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key_.public_key()), critical=False)\
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=False)\
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False, content_commitment=False, key_encipherment=False,
                    data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True,
                    encipher_only=False, decipher_only=False), critical=False)
        csr = builder.sign(key_, hashes.SHA256(), default_backend())
        self._csr = csr
        return self


class Cert(object):
    _crt = None
    _file = None

    @property
    def pem(self):
        if self._crt is None:
            raise Exception('Internal Cert is not set')
        return self._crt.public_bytes(Encoding.PEM)

    @property
    def pem_str(self):
        if not six.PY3:
            return self.pem
        else:
            return six.text_type(self.pem.decode('ascii'))

    @property
    def serial_number(self):
        return self._crt.serial_number

    @property
    def signature(self):
        return self._crl.signature

    def set_file(self, cert_file):
        self._file = cert_file
        return self

    def _assert_file(self):
        if self._file is None:
            raise Exception('No cert file is set')

    def load(self):
        self._assert_file()
        with open(self._file) as f:
            data = f.read()
            if six.PY3:
                data = six.binary_type(data.encode('utf-8'))
            self._crt = x509.load_pem_x509_certificate(data, backend=default_backend())
        return self

    def save(self, overwrite=False):
        self._assert_file()
        if os.path.isfile(self._file) and not overwrite:
            raise Exception('Cert already exists')
        with open(self._file, 'wb') as f:
            f.write(self.pem)
        return self

    def create(self, csr, ca_key, ca_cert, num_days):
        num_days = int(num_days)
        ca_key = load_pem_private_key(
            ca_key.to_decrypted_pem(), password=None, backend=default_backend())
        ca_cert = x509.load_pem_x509_certificate(ca_cert.pem, backend=default_backend())
        csr = x509.load_pem_x509_csr(csr.pem, backend=default_backend())
        b = x509.CertificateBuilder()\
            .subject_name(csr.subject)\
            .issuer_name(ca_cert.subject)\
            .not_valid_before(datetime.today() - timedelta(days=1))\
            .not_valid_after(datetime.today() + timedelta(days=num_days))\
            .serial_number(x509.random_serial_number())\
            .public_key(csr.public_key())
        for ext in csr.extensions:
            b = b.add_extension(ext.value, critical=ext.critical)
            if isinstance(ext.value, x509.BasicConstraints) and ext.value.ca:
                b = b.add_extension(build_aki(ca_cert), critical=False)
        crt = b.sign(
            private_key=ca_key,
            algorithm=hashes.SHA256(),
            backend=default_backend()
        )
        self._crt = crt
        return self

    def create_ca(self, common_name, num_days, rsa_key):
        num_days = int(num_days)
        key_ = load_pem_private_key(
                rsa_key.to_decrypted_pem(), password=None, backend=default_backend())
        x509_name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, six.text_type(common_name))
        ])
        builder = x509.CertificateBuilder()\
            .serial_number(x509.random_serial_number())\
            .subject_name(x509_name)\
            .issuer_name(x509_name)\
            .not_valid_before(datetime.today() - timedelta(days=1))\
            .not_valid_after(datetime.today() + timedelta(days=num_days))\
            .public_key(key_.public_key())\
            .add_extension(
                x509.SubjectKeyIdentifier.from_public_key(key_.public_key()), critical=False)\
            .add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(key_.public_key()),
                critical=False)\
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=False)\
            .add_extension(
                x509.KeyUsage(
                    digital_signature=False, content_commitment=False, key_encipherment=False,
                    data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True,
                    encipher_only=False, decipher_only=False), critical=False)
        crt = builder.sign(key_, hashes.SHA256(), default_backend())
        self._crt = crt
        return self


class CRL(object):
    _crl = None
    _file = None

    @property
    def signature(self):
        return self._crl.signature

    def set_file(self, file_):
        self._file = file_
        return self

    def load(self):
        with open(self._file) as f:
            data = f.read()
            if six.PY3:
                data = six.binary_type(data.encode('utf-8'))
            self._crl = x509.load_pem_x509_crl(data, default_backend())
        return self

    def save(self):
        with open(self._file, 'wb') as f:
            f.write(self._crl.public_bytes(Encoding.PEM))
        return self

    def initialize(self, ca_key, ca_cert, next_update_days=1):
        if not os.path.isfile(self._file):
            ca_key = load_pem_private_key(ca_key.to_decrypted_pem(), None, default_backend())
            ca_cert = x509.load_pem_x509_certificate(ca_cert.pem, default_backend())
            crlb = x509.CertificateRevocationListBuilder()\
                .issuer_name(ca_cert.subject)\
                .last_update(datetime.today())\
                .next_update(datetime.today() + timedelta(days=next_update_days))
            self._crl = crlb.sign(
                private_key=ca_key,
                algorithm=hashes.SHA256(),
                backend=default_backend())

        else:
            self.load()
        return self

    def revoke_cert(self, cert, ca_key, ca_cert, next_update_days=1, revoked_date=None):
        revoked_date = revoked_date or datetime.today()
        cert = x509.load_pem_x509_certificate(cert.pem, default_backend())
        ca_key = load_pem_private_key(ca_key.to_decrypted_pem(), None, default_backend())
        ca_cert = x509.load_pem_x509_certificate(ca_cert.pem, default_backend())
        rc = x509.RevokedCertificateBuilder()\
            .revocation_date(revoked_date)\
            .serial_number(cert.serial_number)\
            .build(default_backend())
        crlb = x509.CertificateRevocationListBuilder(revoked_certificates=[rc for rc in self._crl])\
            .issuer_name(ca_cert.subject)\
            .last_update(datetime.today())\
            .next_update(datetime.today() + timedelta(days=next_update_days))\
            .add_extension(build_aki(ca_cert), False)\
            .add_revoked_certificate(rc)
        self._crl = crlb.sign(
            private_key=ca_key,
            algorithm=hashes.SHA256(),
            backend=default_backend())
        return self


if '__main__' == __name__:
    def main():
        import argparse
        from getpass import getpass
        args = argparse.ArgumentParser()
        args.add_argument('--rsa', action='store_true')
        args.add_argument('--rsa-key', required=False)
        args.add_argument('--rsa-key-size', type=int, required=False)
        args.add_argument('--rsa-pass', action='store_true', dest='pass_')
        args.add_argument('--rsa-gen-key', action='store_true')
        args.add_argument('--rsa-public-pem', action='store_true')
        args.add_argument('--rsa-decrypted-pem', action='store_true')
        args.add_argument('--rsa-encrypted-pem', action='store_true')
        args.add_argument('--rsa-load', action='store_true')
        args.add_argument('--rsa-save', action='store_true')
        args.add_argument('--dh', action='store_true')
        args.add_argument('--dh-key-size', type=int, default=2048)
        args.add_argument('--dh-file', required=False)
        args.add_argument('--dh-gen', action='store_true')
        args.add_argument('--dh-save', action='store_true')
        args.add_argument('--ta', action='store_true')
        args.add_argument('--ta-gen', action='store_true')
        args.add_argument('--ta-file', required=False)
        args.add_argument('--ta-save', action='store_true')
        args.add_argument('--csr', action='store_true')
        args.add_argument('--csr-cn', required=False)
        args.add_argument('--csr-server', action='store_true')
        args.add_argument('--csr-client', action='store_true')
        args.add_argument('--csr-subca', action='store_true')
        args.add_argument('--csr-key', required=False)
        args.add_argument('--csr-file', required=False)
        args.add_argument('--csr-save', action='store_true')
        args.add_argument('--crt', action='store_true')
        args.add_argument('--crt-ca', action='store_true')
        args.add_argument('--crt-ca-key', required=False)
        args.add_argument('--crt-ca-crt', required=False)
        args.add_argument('--crt-csr', required=False)
        args.add_argument('--crt-file', required=False)
        args.add_argument('--crt-cn', required=False)
        args.add_argument('--crt-days', required=False, type=int, default=3650)
        args = args.parse_args()

        passphrase = getpass('Passphrase: ') if args.pass_ else None

        if args.rsa:
            k = RSAKey().set_passphrase(passphrase).set_file(args.rsa_key)
            if args.rsa_gen_key:
                k.generate(args.rsa_key_size)
            elif args.rsa_load:
                k.load()

            if args.rsa_public_pem:
                print(k.public_pem)
            elif args.rsa_decrypted_pem:
                print(k.to_decrypted_pem())
            elif args.rsa_encrypted_pem:
                print(k.pem)
            else:
                print(k)

            if args.rsa_save:
                k.save()

        if args.dh:
            dhp = DHParam().set_file(args.dh_file)
            if args.dh_gen:
                dhp.generate(args.dh_key_size)
                if args.dh_save:
                    dhp.save()
            else:
                dhp.load()
            print(dhp.pem)

        if args.ta:
            takey = TAKey().set_file(args.ta_file)
            if args.ta_gen:
                takey = takey.generate()
            print(takey.pem)

        if args.csr:
            csr = CSR().set_file(args.csr_file)
            rsakey = RSAKey().set_file(args.csr_key).load()
            if args.csr_server:
                csr.create_server(args.csr_cn, rsakey)
            elif args.csr_client:
                csr.create_client(args.csr_cn, rsakey)
            elif args.csr_subca:
                csr.create_subca(args.csr_cn, rsakey)
            elif args.csr_file:
                csr.load()
            else:
                raise Exception('Must be --csr-server or --csr-client or --csr-subca')
            if args.csr_save:
                csr.save()
            else:
                print(csr.pem)

        if args.crt:
            ca_key = RSAKey().set_file(args.crt_ca_key).load()
            crt = Cert().set_file(args.crt_file)
            if args.crt_ca:
                crt.create_ca(args.crt_cn, args.crt_days, ca_key)
            else:
                csr = CSR().set_file(args.crt_csr).load()
                ca_crt = Cert().set_file(args.crt_ca_crt).load()
                crt.create(csr, ca_key, ca_crt, args.crt_days)
            crt.save()
            print(crt.pem)

    main()
