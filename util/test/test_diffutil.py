import sys
from six import StringIO
from unittest import TestCase
from pyauto.util import diffutil as diff_
from pyauto.util.diffutil import Diff, DictDiff
from collections import OrderedDict


class TestDiff(TestCase):
    def test_has_diff(self):
        diff = Diff('abc', '123', '456')
        self.assertTrue(diff.has_diff())

    def test_to_string(self):
        diff = Diff('abc', '123', '456')
        self.assertEqual(diff.to_string().strip(), """
--- abc [current]

+++ abc [proposed]

@@ -1 +1 @@

-123
+456""".strip())

    def test_confirm(self):
        diff = Diff('abc', '123', '456')
        diff_.raw_input = lambda _: 'y'
        self.assertEqual(diff.confirm(), 'accepted')
        diff_.raw_input = lambda _: 'n'
        self.assertEqual(diff.confirm(), 'declined')
        diff = Diff('abc', '123', '123')
        diff_.raw_input = lambda _: 'y'
        self.assertEqual(diff.confirm(), 'none')


class TestDictDiff(TestCase):
    def test_show_and_confirm(self):
        output = StringIO()
        stdout_ = sys.stdout
        sys.stdout = output
        diff = DictDiff({'abc': '123'}, {'abc': '456'})
        diff_.raw_input = lambda _: 'y'
        self.assertDictEqual(diff.show_and_confirm(plain=True),
                             OrderedDict([('abc', '456')]))
        sys.stdout = stdout_
        self.assertEqual("""
--- abc [current]

+++ abc [proposed]

@@ -1 +1 @@

-123
+456
Approved  "abc"
        """.strip(), output.getvalue().strip())

    def test_union(self):
        first = {'abc1': '123'}
        second = {'abc2': '456'}
        DictDiff(first, second)
        self.assertEqual(first['abc2'], '')
        self.assertEqual(second['abc1'], '')
