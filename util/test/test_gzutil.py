import os
import six
from random import randint
from uuid import uuid4
from io import BytesIO
from unittest import TestCase
from pyauto.util import gzutil


def load_data():
    gzsample = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'samples/gzsample.txt')
    with open(gzsample, 'rb') as f:
        return f.read()


class GZUtil(TestCase):
    data = load_data()

    def test_compress_stream(self):
        in_ = BytesIO(self.data)
        out = BytesIO()
        gzutil.compress_stream(in_, out)
        self.assertGreater(len(in_.getvalue()), len(out.getvalue()))

    def test_compress_string(self):
        out = BytesIO()
        data = six.text_type(self.data)
        stat = gzutil.compress(data, out)
        self.assertGreater(len(data), len(out.getvalue()))
        self.assertGreater(stat['uncompressed_size'], stat['compressed_size'])

    def test_compress_bytes(self):
        out = BytesIO()
        data = six.binary_type(self.data)
        stat = gzutil.compress(data, out)
        self.assertGreater(len(data), len(out.getvalue()))
        self.assertGreater(stat['uncompressed_size'], stat['compressed_size'])

