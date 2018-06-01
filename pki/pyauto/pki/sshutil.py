import re
import os
import sys
import six
import base64
import struct


SSH_RSA = 'ssh-rsa'


if six.PY3:
    binary = bytes
else:
    binary = bytearray


class Keydata(object):
    algorithm = None
    exp = None
    modulus = None

    def __init__(self, algorithm=SSH_RSA, exp=None, modulus=None):
        self.set_algorithm(algorithm)
        self.exp = exp
        self.modulus = modulus

    def set_algorithm(self, algorithm):
        if SSH_RSA != algorithm:
            raise Exception('Unsupported algorithm "{0}".'.format(algorithm))
        self.algorithm = algorithm
        return self

    def decode(self, keydata):
        keydata = base64.b64decode(keydata)
        return self.decode_bytes(keydata)

    def decode_bytes(self, keydata):
        parts = []
        while keydata:
            # read the length of the data
            dlen = struct.unpack('>I', keydata[:4])[0]

            # read in <length> bytes
            data, keydata = keydata[4:dlen+4], keydata[4+dlen:]
            parts.append(data)

        exp = int('0x' + ''.join([byte_to_hex(x) for x in parts[1]]), 16)
        modulus = int('0x' + ''.join([byte_to_hex(x) for x in parts[2]]), 16)

        self.set_algorithm(parts[0].decode('utf-8'))
        self.exp = exp
        self.modulus = modulus

        return self

    def encode(self):
        keydata = self.encode_bytes()
        return base64.b64encode(keydata).decode('utf-8')

    def encode_bytes(self):
        if self.exp is None or self.modulus is None:
            raise Exception('exponent and modulus are required.')

        keydata = binary()

        exp_b = hex(self.exp)[2:].upper()
        exp_b = re.sub('L$', '', exp_b)
        exp_b = ('0' if len(exp_b) % 2 == 1 else '') + exp_b
        exp_b = binary.fromhex(exp_b)

        modulus_b = hex(self.modulus)[2:].upper()
        modulus_b = re.sub('L$', '', modulus_b)
        modulus_b = ('0' if len(modulus_b) % 2 == 1 else '') + modulus_b
        modulus_b = binary([0]) + binary.fromhex(modulus_b)

        keydata += struct.pack('>I', len(self.algorithm))
        keydata += self.algorithm.encode('utf-8')
        keydata += struct.pack('>I', len(exp_b))
        keydata += exp_b
        keydata += struct.pack('>I', len(modulus_b))
        keydata += modulus_b

        return keydata


class SshRsaPubKey(object):
    algorithm = None
    keydata = None
    comment = None

    def __init__(self, algorithm=SSH_RSA, keydata=None, comment=None):
        self.set_algorithm(algorithm)
        self.comment = comment
        if keydata is not None:
            self.keydata = Keydata().decode(keydata)

    def set_algorithm(self, algorithm):
        if SSH_RSA != algorithm:
            raise Exception('Unsupported algorithm "{0}".'.format(algorithm))
        self.algorithm = algorithm
        return self

    def encode(self):
        parts = [self.algorithm, self.keydata.encode()]
        if self.comment is not None:
            parts.append(self.comment)
        return ' '.join(parts)

    def decode(self, blob):
        parts = blob.split(None)
        self.set_algorithm(parts[0])
        self.keydata = Keydata().decode(parts[1])
        if len(parts) > 2:
            self.comment = parts[2]
        else:
            self.comment = None
        assert self.keydata.algorithm == self.algorithm
        return self


def load_key_file(filename):
    with open(filename) as f:
        return SshRsaPubKey().decode(f.read())


def byte_to_hex(x):
    if six.PY3:
        byte = bytes([x])
    else:
        byte = x
    return '%02X' % struct.unpack('B', byte)[0]
