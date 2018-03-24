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

example_schema = OrderedDict([
    ('tag', 'test'),
    ('tables', [
        OrderedDict([
            ('name', 'urlset')
        ])
    ])])
example_database = OrderedDict([
    ('tag', 'test'),
    ('schema', 'sitemaps'),
    ('name', 'test.db')])
example_csv = OrderedDict([
    ('tag', 'test'),
    ('database', 'test'),
    ('tablename', 'test'),
    ('resource', 'local/get_workspace_path,example.csv')])


def tearDownModule():
    if os.path.isfile(example_db):
        os.remove(example_db)


class CSVDB(TestCase):
    def test_init(self):
        self.assertIsInstance(csvdb, csvdb_config.CSVDB)

    def test_append_schema(self):
        self.assertEqual(len(csvdb.schemas), 1)
        csvdb.append_schema(example_schema)
        self.assertEqual(len(csvdb.schemas), 2)
        self.assertIsInstance(csvdb.schemas[1], csvdb_config.Schema)

    def test_append_database(self):
        self.assertEqual(len(csvdb.databases), 1)
        csvdb.append_database(example_database)
        self.assertEqual(len(csvdb.databases), 2)
        self.assertIsInstance(csvdb.databases[1], csvdb_config.Database)

    def test_append_csv(self):
        self.assertEqual(len(csvdb.csvs), 1)
        csvdb.append_csv(example_csv)
        self.assertEqual(len(csvdb.csvs), 2)
        self.assertIsInstance(csvdb.csvs[1], csvdb_config.CSV)

    def test_get_schema(self):
        schema = csvdb.get_schema('sitemaps')
        self.assertIsInstance(schema, csvdb_config.Schema)

    def test_get_database(self):
        db = csvdb.get_database('sitemaps')
        self.assertIsInstance(db, csvdb_config.Database)

    def test_get_csv(self):
        csv = csvdb.get_csv('sitemaps')
        self.assertIsInstance(csv, csvdb_config.CSV)


class Schema(TestCase):
    def test_init(self):
        csvdb_config.Schema(example_schema, csvdb)

    def test_get_table(self):
        schema = csvdb.get_schema('sitemaps')
        self.assertIsInstance(schema, csvdb_config.Schema)


class Database(TestCase):
    def test_schema(self):
        db = csvdb.get_database('sitemaps')
        self.assertIsInstance(db, csvdb_config.Database)
        schema = db.schema
        self.assertIsInstance(schema, csvdb_config.Schema)

    def test_filename(self):
        db = csvdb.get_database('sitemaps')
        f1 = os.path.normpath(db.filename)
        f2 = local.get_workspace_path(db['name'])
        self.assertEqual(f1, f2)


class CSV(TestCase):
    def test_resource(self):
        csv = csvdb.get_csv('sitemaps')
        fn = csv.resource
        self.assertIsInstance(fn, six.string_types)
        self.assertTrue(os.path.isfile(fn))

    def test_database(self):
        csv = csvdb.get_csv('sitemaps')
        db = csv.database
        self.assertIsInstance(db, csvdb_config.Database)

    def test_table(self):
        csv = csvdb.get_csv('sitemaps')
        table = csv.table
        self.assertIsInstance(table, csvdb_config.SchemaTable)

    def test_filename(self):
        csv = csvdb.get_csv('sitemaps')
        filename = csv.filename
        self.assertTrue(os.path.isfile(filename))

    def test_get_import_table(self):
        csv = csvdb.get_csv('sitemaps')
        table = csv.get_import_table()
        self.assertIsInstance(table, db.Table)
