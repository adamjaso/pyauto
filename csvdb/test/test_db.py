import os
import six
from unittest import TestCase
from pyauto.core import deploy, config as core_config
from pyauto.csvdb import db, config as csvdb_config
from collections import OrderedDict

dirname = os.path.dirname(os.path.abspath(__file__))
example_db = os.path.join(dirname, 'sitemaps.db')
conf = deploy.Command(os.path.join(dirname, 'config.yml'), [])\
    .config
local = conf.local
csvdb = conf.csvdb


class Table(TestCase):
    def setUp(self):
        self.csv = csvdb.get_csv('sitemaps')
        self.table = self.csv.get_import_table()

    def tearDown(self):
        if os.path.isfile(example_db):
            os.remove(example_db)

    def test_build_mapping(self):
        with self.table as table:
            self.assertGreater(len(table.mapping), 0)

    def test_build_column_defs(self):
        with self.table as table:
            self.assertEqual(table.create_sql, 'CREATE TABLE IF NOT EXISTS sitemapindex (\n\t loc TEXT NOT NULL,\n\tlastmod TEXT NOT NULL )')
            self.assertEqual(table.insert_sql, 'INSERT INTO sitemapindex (\n loc,\n\tlastmod \n) VALUES (\n ?,\n\t? )')

    def test_create_table(self):
        with self.table as table:
            res = table.sqlite.execute(
                'SELECT name FROM sqlite_master '
                'WHERE type="table" AND name="sitemapindex"')
            res = res.fetchall()
            self.assertEqual(len(res), 0)
            table.create_table()
            res = table.sqlite.execute(
                'SELECT name FROM sqlite_master '
                'WHERE type="table" AND name="sitemapindex"')
            res = res.fetchall()
            self.assertEqual(len(res), 1)

    def test_insert_table(self):
        with self.table as table:
            table.create_table()
            count = get_count(table)
            self.assertEqual(count, 0)
            row = {
                'loc': 'https://jobs.washingtonpost.com/sitemap1-101.xml',
                'lastmod': '2017-12-20T03:14:29+00:00'
            }
            table.insert_table(row)
            count = get_count(table)
            self.assertEqual(count, 1)

    def test_import_table(self):
        with self.table as table:
            table.create_table()
            count = get_count(table)
            self.assertEqual(count, 0)
            table.import_table()
            count = get_count(table)
            self.assertEqual(count, 9)


def get_count(table):
    rows = table.sqlite.execute('SELECT count(*) FROM sitemapindex')
    count = next(iter(rows.fetchall()))[0]
    return count
