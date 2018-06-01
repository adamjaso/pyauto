import os
import six
from collections import OrderedDict
from pyauto.pki import sshutil
from unittest import TestCase


dirname = os.path.dirname(os.path.abspath(__file__))
ssh_dirname = os.path.join(dirname, 'ssh')

type_bits = OrderedDict([
    ('rsa', ['1024', '2048', '4096']),
])


def get_filename(typ, bit):
    fn = ''.join([typ, '-', str(bit), '.pub'])
    fn = os.path.join(ssh_dirname, fn)
    return fn


def load_key(typ, bit):
    fn = get_filename(typ, bit)
    return sshutil.load_key_file(fn)


def load_key_parts(typ, bit):
    fn = get_filename(typ, bit)
    with open(fn) as f:
        return f.read().split(None)


class SshRsaPubKey(TestCase):
    def test_init(self):
        with self.assertRaises(Exception) as context:
            sshutil.SshRsaPubKey('ssh-ecdsa')
            self.assertIn('Unsupported algorithm', context.exception.message)
        sshutil.SshRsaPubKey()

    def test_decode(self):
        for typ, bits in type_bits.items():
            for bit in bits:
                spk = load_key(typ, bit)
                if six.PY3:
                    tbit = len(hex(spk.keydata.modulus)[2:]) * 4
                else:
                    tbit = len(hex(spk.keydata.modulus)[2:-1]) * 4
                self.assertEqual(tbit, int(bit))

    def test_encode(self):
        for typ, bits in type_bits.items():
            for bit in bits:
                parts = load_key_parts(typ, bit)
                spk = load_key(typ, bit)
                keydata = spk.keydata.encode()
                self.assertEqual(keydata, parts[1])
