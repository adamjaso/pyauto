from unittest import TestCase
import re
from pyauto import strutil


class TestRandStr(TestCase):
    def test_rand_str(self):
        rand = strutil.rand_str(32)
        self.assertIsNotNone(re.match('^[a-zA-Z0-9]{32}$', rand))


class TestSanitizeName(TestCase):
    def test_sanitize_name(self):
        names = {
                'asdf!@#$%^&*()_': 'asdf_',
                'asdf': 'asdf',
                'asdf.fdsa': 'asdf.fdsa',
                'asdf_fdsa': 'asdf_fdsa',
                'asdf-fdsa': 'asdf-fdsa',
        }
        for name, value in names.items():
            self.assertEqual(strutil.sanitize_name(name), value)


class TestCamelToSnake(TestCase):
    def test_camel_to_snake(self):
        names = {
                'TestCase': 'test_case',
                'testCase': 'test_case',
                '123TestCase': '123_test_case'
        }
        for name, value in names.items():
            self.assertEqual(strutil.camel_to_snake(name), value)
