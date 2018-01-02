from unittest import TestCase
from pyauto import uriutil
from collections import OrderedDict

test_uri = 'http://a:b@localhost:5000/abc?def=123#ghi567'


class TestParse(TestCase):
    def test_parse(self):
        parts = uriutil.parse(test_uri)
        self.assertEqual('http', parts['scheme'])
        self.assertEqual('a:b@localhost:5000', parts['netloc'])
        self.assertEqual('/abc', parts['path'])
        self.assertDictEqual(parts['query'], OrderedDict([('def', '123')]))
        self.assertEqual('ghi567', parts['frag'])

    def test_format(self):
        parts = uriutil.parse(test_uri)
        formatted = uriutil.format(**parts)
        self.assertEqual(test_uri, formatted)

    def test_format_query(self):
        query = OrderedDict([('abc', 456), ('def', 123)])
        self.assertEqual('abc=456&def=123', uriutil.format_query(query))
        self.assertEqual('abc=456&def=123', uriutil.format_query(**query))
