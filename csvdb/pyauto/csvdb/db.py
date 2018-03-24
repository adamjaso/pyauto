import os
import sys
import csv
import sqlite3
from collections import OrderedDict
from pyauto.util import strutil


class Table(object):
    def __init__(self, tablename, sqlite_filename, csv_filename,
                 *unique_columns, **column_types):
        self.tablename = tablename
        self.unique_columns = [strutil.camel_to_snake(name)
                               for name in unique_columns]
        self.column_types = column_types
        self.sqlite_filename = sqlite_filename
        self.csv_filename = csv_filename
        self.sqlite = None
        self.csv = None
        self.mapping = OrderedDict()
        self.create_sql = None
        self.insert_sql = None
        self._validate()

    def _validate(self):
#        if os.path.isfile(self.sqlite_filename):
#            raise Exception('sqlite file already exists: {0}'
#                            .format(self.sqlite_filename))
        if not os.path.isfile(self.csv_filename):
            raise Exception('csv file not found: {0}'
                            .format(self.csv_filename))

    def _build_mapping(self):
        for name in self.csv.fieldnames:
            if name:
                self.mapping[name] = strutil.camel_to_snake(name)

    def _build_column_defs(self):
        column_defs = [
            'CREATE TABLE IF NOT EXISTS', self.tablename, '(\n\t',
            ',\n\t'.join([' '.join([
                    col_name, self.column_types.get(name, 'TEXT'), 'NOT NULL'
                ])
                for name, col_name in self.mapping.items()
            ])
        ]
        insert_defs = [
            'INSERT INTO', self.tablename, '(\n', ',\n\t'.join([
                col_name for name, col_name in self.mapping.items()
            ]), '\n) VALUES (\n', ',\n\t'.join([
                '?' for name, col_name in self.mapping.items()
            ]), ')',
        ]
        if len(self.unique_columns) > 0:
            column_defs.append(', PRIMARY KEY(')
            column_defs.extend(', '.join([
                col_name
                for name, col_name in self.mapping.items()
                if name in self.unique_columns
            ]))
            column_defs.append(')')
        column_defs.append(')')
        self.create_sql = ' '.join(column_defs)
        self.insert_sql = ' '.join(insert_defs)

    def __enter__(self):
        self.sqlite = sqlite3.connect(self.sqlite_filename)
        self.sqlite.text_factory = str
        self.csv_fd = open(self.csv_filename)
        self.csv = csv.DictReader(self.csv_fd)
        self._build_mapping()
        self._build_column_defs()
        return self

    def __exit__(self, typ, value, tb):
        try:
            self.sqlite.close()
        except:
            print(str(e))
        try:
            self.csv_fd.close()
        except Exception as e:
            print(str(e))

    def create_table(self):
        self.sqlite.execute(self.create_sql)
        return self

    def insert_table(self, cols):
        if isinstance(cols, (dict, OrderedDict)):
            cols = [cols[name] for name in self.mapping.keys()]
        self.sqlite.execute(self.insert_sql, cols)
        return self

    def import_table(self):
        self.create_table()
        count = 0
        for row in self.csv:
            self.insert_table(row)
            count += 1
            if count % 1000 == 0:
                sys.stdout.write(
                    ' '.join(['imported', str(count), 'rows    \r']))
                sys.stdout.flush()
        self.sqlite.commit()


class DB(object):
    def __init__(self, filename):
        self.conn = None
        self.filename = filename

    def connect(self):
        self.conn = sqlite3.connect(self.filename)
        return self

    def create_table_str(self, tablename, fieldnames, fieldtypes):
        return 'CREATE TABLE {0} ( {1} )'.format(tablename, ' '.join([
            ' '.join([name, fieldtypes.get(name, 'TEXT')]) for name in fieldnames
        ]))


def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('-f', dest='filename', required=True)
    args.add_argument('-t', dest='tablename', required=True)
    args.add_argument('--field', nargs='+')
    args = args.parse_args()

    DB().create_table_str(args.tablename)


if '__main__' == __name__:
    main()
