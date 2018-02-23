import os
import sys
import json
import shlex
import shutil
import importlib
from pyauto.util import yamlutil, funcutil


class Store(object):
    filename = None
    data = None

    def __init__(self, filename):
        self.filename = os.path.abspath(filename)

    def get(self, owner_type, owner, namespace, key, value_generate=None):
        self.load()
        name = '/'.join([owner_type, owner, namespace, key])
        if name not in self.data:
            if value_generate is None:
                raise Exception('value generator not specified for {0}'
                                .format(name))
            elif callable(value_generate):
                value = value_generate()
            else:
                value = value_generate
            self.data[name] = value
            self.save()
        else:
            value = self.data[name]
        return value

    def delete(self, owner_type, owner, namespace, key):
        self.load()
        name = '/'.join([owner_type, owner, namespace, key])
        if name in self.data:
            del self.data[name]
            self.save()
        return self

    def get_dict(self, owner_type, owner, values):
        self.load()
        result = {}
        for namespace, value in values.items():
            if namespace not in result:
                result[namespace] = {}
            for key, value_generate in value.items():
                result[namespace][key] = self.get(
                        owner_type, owner, namespace, key, value_generate)
        return result

    def delete_keys(self, owner_type, owner, namespace, keys):
        self.load()
        if not keys:
            name = '/'.join([owner_type, owner, namespace, ''])
            for key in [k for k in self.data.keys()]:
                if key.startswith(name):
                    del self.data[key]
        else:
            for key in keys:
                name = '/'.join([owner_type, owner, namespace, key])
                if name in self.data:
                    del self.data[name]
        self.save()
        return self

    def get_group(self, owner_type, owner):
        return Group(self, owner_type, owner)

    def save(self):
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.data, indent=2))
        return self

    def load(self):
        if os.path.isfile(self.filename):
            with open(self.filename) as f:
                self.data = json.load(f)
        else:
            self.data = {}
        return self


class Group(object):
    def __init__(self, credentials_store, owner_type, owner):
        self.owner_type = owner_type
        self.owner = owner
        self.credentials_store = credentials_store

    def get(self, namespace, key, value_generate=None):
        return self.credentials_store.get(
            self.owner_type, self.owner, namespace, key, value_generate)

    def delete(self, namespace, key):
        self.credentials_store.delete(
            self.owner_type, self.owner, namespace, key)
        return self

    def get_dict(self, values):
        return self.credentials_store.get_dict(
            self.owner_type, self.owner, values)

    def delete_keys(self, namespace, keys):
        self.credentials_store.delete_keys(
            self.owner_type, self.owner, namespace, keys)
        return self


class GroupDefinition(object):
    def __init__(self, name, definition):
        self.name = name
        self.definition = {}
        for namespace, values in definition.items():
            if not isinstance(values, dict):
                raise Exception('Invalid definitions structure. Top-level '
                                'values must be instances of dict')
            for key, value in values.items():
                func = funcutil.Function(value)

                def generate_secret(func):
                    return lambda: func.run()

                values[key] = generate_secret(func)
            self.definition[namespace] = values

    def __repr__(self):
        return str(self.definition)

    @classmethod
    def parse_definitions(cls, definitions):
        return {
            name: cls(name, definition)
            for name, definition in definitions.items()
        }

    @classmethod
    def parse_definitions_file(cls, definitions_file, definition_format):
        with open(definitions_file) as f:
            if 'json' == definition_format:
                definitions = json.load(f)
            elif 'yaml' == definition_format:
                definitions = yamlutil.load_dict(f.read())
            else:
                raise Exception('invalid format {0}'.format(definitions_format))
        return cls.parse_definitions(definitions)
