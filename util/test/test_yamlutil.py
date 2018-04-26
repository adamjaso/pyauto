import yaml
from unittest import TestCase
from collections import OrderedDict
from pyauto.util import yamlutil


sample_ordered_dict = OrderedDict([
    ('q', 1),
    ('b', 2),
    ('c', OrderedDict([
        ('d', 3),
        ('e', 4),
        ('f', [
            OrderedDict([
                ('g', 5)
            ])
        ])
    ]))
])
sample_ordered_dict['h'] = 6


sample_unicode_ordered_dict = OrderedDict([
    (u'q', 1),
    (u'b', 2),
    (u'c', OrderedDict([
        (u'd', 3),
        (u'e', 4),
        (u'f', [
            OrderedDict([
                (u'g', 5)
            ])
        ])
    ]))
])
sample_unicode_ordered_dict['h'] = 6


sample_ordered_yaml = """
q: 1
b: 2
c:
  d: 3
  e: 4
  f:
  - g: 5
h: 6
""".strip()


sample_unicode_ordered_yaml = """
q: 1
b: 2
c:
  d: 3
  e: 4
  f:
  - g: 5
h: 6
""".strip()


sample_all = [
    {'a': 1, 'b': 2},
    {'c': 3, 'd': 4}
]


sample_all_yaml = """
a: 1
b: 2
---
c: 3
d: 4
""".strip()


sample_dict = dict(
    q=1,
    b=2,
    c=dict(
        d=3,
        e=4,
        f=[
            dict(
                g=5
            )
        ]
    ),
    h=6,
)


sample_yaml = """
b: 2
c:
  d: 3
  e: 4
  f:
  - g: 5
h: 6
q: 1
""".strip()


sample_block_dict = dict(
    a='abc123\n'
      'def456\n'
      'ghi789\n',
    b=1,
)


sample_block_yaml = """
a: |
  abc123
  def456
  ghi789
b: 1
""".strip()


class TestDumpDict(TestCase):
    def test_dump_dict_ordered(self):
        res = yamlutil.dump_dict(sample_ordered_dict).strip()
        self.assertEqual(sample_ordered_yaml, res)

    def test_dump_dict_unordered(self):
        res = yamlutil.dump_dict(sample_dict).strip()
        self.assertEqual(sample_yaml, res)

    def test_safe_dump_unicode(self):
        data = yamlutil.dump_dict(sample_unicode_ordered_dict, safe_dump=True)
        self.assertEqual(sample_unicode_ordered_yaml, data.strip())

    def test_dump_all_unordered(self):
        data = yamlutil.dump_dict(sample_all, dump_all=True)
        self.assertEqual(sample_all_yaml, data.strip())


class TestBlockValues(TestCase):
    def test_dump_block_value(self):
        res = yamlutil.dump_dict(sample_block_dict).strip()
        self.assertEqual(sample_block_yaml, res)

    def test_load_block_value(self):
        res = yaml.safe_load(sample_block_yaml)
        self.assertDictEqual(sample_block_dict, res)
