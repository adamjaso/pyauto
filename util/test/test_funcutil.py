import six
from unittest import TestCase
from pyauto.util import funcutil


def myfunc_noargs():
    return 'abc'


def myfunc_args(a, b):
    return '-'.join([a, b])


def myfunc_bytearray():
    return six.binary_type('abc', 'utf-8')


class Function(TestCase):
    def test_run_noargs(self):
        func = funcutil.Function('test_funcutil.myfunc_noargs')
        res = func.run()
        self.assertEqual(res, 'abc')

    def test_run_args(self):
        func = funcutil.Function('test_funcutil.myfunc_args 1 2')
        res = func.run()
        self.assertEqual(res, '1-2')

    def test_run_bytearray(self):
        func = funcutil.Function('test_funcutil.myfunc_bytearray')
        res = func.run()
        self.assertEqual(res, 'abc')
        self.assertIsInstance(res, six.text_type)

