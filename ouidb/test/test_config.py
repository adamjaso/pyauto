import os
import json
import shutil
from unittest import TestCase
from pyauto.core import deploy
from pyauto.ouidb import config

example_row_lines = """3C-D9-2B   (hex)		Hewlett Packard
3CD92B     (base 16)		Hewlett Packard
				11445 Compaq Center Drive
				Houston    77070
				US""".split('\n')
example_row_parsed = {
    'post_code': '77070',
    'address': 'Hewlett Packard\n11445 Compaq Center Drive\nHouston    77070'
               '\nUS',
    'hex': '3C-D9-2B',
    'base16': '3CD92B',
    'org_name': 'Hewlett Packard',
    'country': 'US'
}

dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), [])\
    .config
ouidb = conf.ouidb
local = conf.local


def setUpModule():
    local.init_workspace()
    source_file = local.get_workspace_path('oui.txt')
    shutil.copy(os.path.join(dirname, 'example.txt'), source_file)


def tearDownModule():
    shutil.rmtree(local.workspace_dir)


class TestOUIDB(TestCase):
    def test_get_source_file(self):
        source_file = ouidb.get_source_file()
        expected_file = os.path.join(dirname, 'workspace/oui.txt')
        self.assertEqual(source_file, expected_file)

    def test_get_dest_file(self):
        dest_file = ouidb.get_dest_file()
        expected_file = os.path.join(dirname, 'workspace/oui.db')
        self.assertEqual(dest_file, expected_file)

    def test_get_db(self):
        ouidb.get_db()
        self.assertTrue(os.path.isfile(ouidb.get_dest_file()))

    def test_create_db(self):
        db = ouidb.create_db()
        try:
            db.execute('select * from mac_vendor limit 1').fetchall()
        finally:
            db.close()

    def test_parse_source(self):
        example_json = os.path.join(dirname, 'example.json')
        with open(example_json) as f:
            expected = json.load(f)
            example = [i for i in ouidb.parse_source()]
            self.assertListEqual(example, expected)

    def test_parse_entries(self):
        example = [line for line in ouidb.parse_entries(example_row_lines)]
        expected = [[
            '3C-D9-2B   (hex)\t\tHewlett Packard',
            '3CD92B     (base 16)\t\tHewlett Packard',
            '\t\t\t\t11445 Compaq Center Drive',
            '\t\t\t\tHouston    77070',
            '\t\t\t\tUS']]
        self.assertListEqual(example, expected)

    def test_parse_entry(self):
        entry = ouidb.parse_entry(example_row_lines)
        self.assertDictEqual(example_row_parsed, entry)

