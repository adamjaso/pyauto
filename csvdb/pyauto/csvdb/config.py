import os
import re
from pyauto.core import config
from pyauto.local import config as _
from .db import Table


class CSVDB(config.Config):
    def __init__(self, config, parent=None):
        super(CSVDB, self).__init__(config, parent)
#        self['task_modules'] = ['pyauto.filecache.commands']
        self['schemas'] = [Schema(s, self) for s in self['schemas']]
        self['databases'] = [Database(d, self) for d in self['databases']]
        self['csvs'] = [CSV(c, self) for c in self['csvs']]

    def append_schema(self, schema):
        schema = Schema(schema, self)
#        if self.get_schema(schema):
#            raise
        self['schemas'].append(schema)
        return self

    def append_database(self, db):
        db = Database(db, self)
#        if self.get_database(db.id):
#            raise Exception('database already exists: {0}'.format(db.id))
        db.schema
        self['databases'].append(db)
        return self

    def append_csv(self, csv):
        csv = CSV(csv, self)
#        if self.get_csv(csv.id):
#            raise Exception('csv already exists: {0}'.format(csv.id))
#        csv.get_import_table()
        self['csvs'].append(csv)
        return self

    def get_schema(self, schema):
        for s in self.schemas:
            if schema == s.get_id():
                return s
        raise Exception('unknown schema: {0}'.format(schema))

    def get_database(self, database):
        for db in self.databases:
            if database == db.get_id():
                return db
        raise Exception('unknown database: {0}'.format(database))

    def get_csv(self, csv):
        for c in self.csvs:
            if csv == c.get_id():
                return c
        raise Exception('unknown csv: {0}'.format(csv))


class SchemaTable(config.Config):
    @property
    def unique_columns(self):
        return self.get('unique_columns', [])

    @property
    def column_types(self):
        return self.get('column_types', {})


class Schema(config.Config):
    def __init__(self, config, parent=None):
        super(Schema, self).__init__(config, parent)
        self['tables'] = [SchemaTable(st, self) for st in self['tables']]

    def get_table(self, tablename):
        for table in self.tables:
            if tablename == table['name']:
                return table
        raise Exception('unknown schema table: {0}'.format(tablename))


class Database(config.Config):
    @property
    def schema(self):
        return self.config.get_schema(self['schema'])

    @property
    def filename(self):
        return self.config.config.local.get_workspace_path(
                self.config.directory, self.name)


class CSV(config.Config):

    def __init__(self, config, parent=None):
        super(CSV, self).__init__(config, parent)

    @property
    def resource(self):
        return self.config.config.get_resource(self['resource'])

    @property
    def database(self):
        return self.config.get_database(self['database'])

    @property
    def table(self):
        return self.database.schema.get_table(self.tablename)

    @property
    def filename(self):
        if 'resource' in self:
            return self.resource
        return self.config.config.local.get_workspace_file(
                self.config.directory, self.name)

    def get_import_table(self):
        db = self.database
        st = db.schema.get_table(self.tablename)
        return Table(
            self.tablename,
            db.filename,
            self.filename,
            unique_columns=st.unique_columns,
            column_types=st.column_types
        )


config.set_config_class('csvdb', CSVDB)
