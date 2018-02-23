import os
import six
import json
import random
from uuid import uuid4
from base64 import b64encode


rand_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def random_string(n):
    return ''.join(random.sample(rand_chars, int(n)))


def urandom_string(n):
    value = os.urandom(int(n))
    value = b64encode(value)
    value = value.decode('utf-8')
    return value


def uuid():
    return six.text_type(uuid4())


def nacl_secretbox_key():
    from nacl import utils, secret
    value = utils.random(secret.SecretBox.KEY_SIZE)
    return b64encode(value).decode('utf-8')


def nacl_signing_key():
    from nacl import signing
    value = six.binary_type(signing.SigningKey.generate())
    return b64encode(value).decode('utf-8')


def dh_param(n=2048):
    from pyauto.pki import pkiutil
    return pkiutil.DHParam().generate(int(n)).pem_str


def rsa_key(n=2048):
    from pyauto.pki import pkiutil
    return pkiutil.RSAKey().generate(int(n)).pem_str


def traditional_rsa_key(n=2048):
    from pyauto.pki import pkiutil
    return pkiutil.RSAKey().generate(int(n)).traditional_pem_str


def pki_self_signed(profile, n, common_name, num_days):
    from pyauto.pki import pkiutil
    rsa = pkiutil.RSAKey().generate(int(n))
    csr = getattr(pkiutil.CSR(), 'create_' + profile)(common_name, rsa)
    ca = pkiutil.Cert().create_ca(common_name, int(num_days), rsa)
    crt = pkiutil.Cert().create(csr, rsa, ca, int(num_days))
    return json.dumps({
        'key': rsa.pem_str.strip(),
        'pub': rsa.public.pem_str.strip(),
        'csr': csr.pem_str.strip(),
        'ca': ca.pem_str.strip(),
        'crt': crt.pem_str.strip(),
    })


def main():
    import argparse
    from pyauto.util import funcutil
    args = argparse.ArgumentParser()
    args.add_argument('function')
    args = args.parse_args()

    function = args.function
    if args.function.startswith('.'):
        function = '__main__' + function
    func = funcutil.Function(function)
    value = func.run()
    print(value)


if '__main__' == __name__:
    main()
