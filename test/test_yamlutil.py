from unittest import TestCase
import yaml
from collections import OrderedDict
from pyauto import yamlutil


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


class TestBlockValues(TestCase):
    def test_dump_block_value(self):
        res = yamlutil.dump_dict(sample_block_dict).strip()
        self.assertEqual(sample_block_yaml, res)

    def test_load_block_value(self):
        res = yaml.safe_load(sample_block_yaml)
        self.assertDictEqual(sample_block_dict, res)
