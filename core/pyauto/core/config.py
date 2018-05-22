import os
import sys
import json
from collections import OrderedDict
from . import tasks
from pyauto.util import yamlutil
from pyauto.util.strutil import root_prefix


_config_classes = {}
_id_key = 'tag'


def list_config_classes():
    return _config_classes.items()


class ConfigList(object):
    def __init__(self, items, parent, config_class):
        self.config_class = config_class
        self.items = items
        for index, item in enumerate(self.items):
            self.items[index] = config_class(item, parent)

    def get_tag(self, tag):
        for item in self.items:
            if item[_id_key] == tag:
                return item
        raise Exception('unknown {0}: {1}'
                        .format(self.config_class.__name__, tag))

    def __iter__(self):
        return self.items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, item, value):
        self.items[item] = value


class Config(object):
    _dict = None
    _cache = None
    _task_sequences = None
    _dirname = None

    def __init__(self, config_dict, parent=None, dirname=None):
        self.config = parent
        self._dict = config_dict
        self._cache = {}
        if dirname is not None:
            self._dirname = os.path.abspath(dirname)
        if dirname is None and parent is not None:
            self._dirname = parent._dirname
        if 'tasks' in config_dict:
            task_modules = config_dict.get('task_modules', [])
            self._task_sequences = tasks.TaskSequences(
                task_modules, config_dict['tasks'], self)

    def get_id(self):
        global _id_key
        return self[_id_key]

    @property
    def task_sequences(self):
        return self._task_sequences

    def __repr__(self):
        return str(self._dict)

    def __getattr__(self, item):
        return self.__getitem__(item, None)

    def __getitem__(self, item, default=None):
        val = self._dict.get(item, default)
        if self.__class__ != Config:
            return val
        if item not in _config_classes:
            return val
        if item not in self._cache:
            self._cache[item] = _config_classes[item](val, parent=self)
        return self._cache[item]

    def __setitem__(self, item, value):
        self._dict[item] = value

    def __contains__(self, item):
        return item in self._dict

    def __len__(self):
        return len(self._dict)

    def __iter__(self):
        return self._dict.keys()

    def keys(self):
        return self._dict.keys()

    def items(self):
        return self._dict.items()

    def get(self, item, default=None):
        return self.__getitem__(item, default)

    def get_path(self, *path):
        if self._dirname is None:
            raise Exception('Config dirname is not set')
        if path:
            path = os.path.join(*path)
            if not path.startswith(root_prefix):
                path = os.path.join(self._dirname, path)
        else:
            path = self._dirname
        return os.path.normpath(path)

    def get_resource(self, name):
        parts = name.split('/', 1)
        obj = self.__getitem__(parts[0])
        if len(parts) == 1:
            return obj

        func_parts = parts[1].split(',')
        if hasattr(obj, func_parts[0]):
            return getattr(obj, func_parts[0])(*func_parts[1:])

        raise Exception('Module "{0}" does not support get_by_id. {1}'
                        .format(parts[0], name))

    def get_task_sequence(self, task_name, **kwargs):
        return self._task_sequences.get_task_sequence(task_name, **kwargs)

    def _assert_tasks(self):
        if 'tasks' not in self:
            raise Exception('No tasks found. '
                            'The "tasks" attribute is not set.')

    def run_task_function(self, action):
        task = tasks.Task(self._task_sequences, action)
        return task.invoke()

    def run_task_sequences(self, *actions, **kwargs):
        inspect = kwargs.get('inspect', False)
        tree = kwargs.get('tree', False)

        if len(actions) == 0:
            if inspect:
                self._assert_tasks()
                self._task_sequences.show_tasks()
            elif tree:
                self._assert_tasks()
                print(yamlutil.dump_dict(self.to_dict()['tasks']))
            else:
                json.dump(self.to_dict(), sys.stdout, indent=2)

        else:
            self._assert_tasks()
            for action in actions:
                self._task_sequences.run_task_sequence(action, **kwargs)

    def to_dict(self):

        def to_dict(value):
            if isinstance(value, Config):
                return value.to_dict()
            elif not isinstance(value, (ConfigList, dict)):
                return value

            kvs = []
            for name, value in value.items():
                if isinstance(value, (Config, dict)):
                    kvs.append((name, to_dict(value)))
                elif isinstance(value, list):
                    kvs.append((name, [to_dict(v) for v in value]))
                else:
                    kvs.append((name, value))
            return OrderedDict(kvs)

        return to_dict(self._dict)

    @classmethod
    def wrap(cls, config, parent=None):
        if isinstance(config, list):
            return ConfigList(config, parent, cls)
        else:
            return cls(config, parent)


def load(filename, dirname=None):
    if dirname is None:
        dirname = os.getcwd()
    with open(filename) as f:
        config = yamlutil.load_dict(f)
        return Config(config, dirname=dirname)


def set_config_class(name, config_class):
    _config_classes[name] = config_class

def set_id_key(name):
    global _id_key
    _id_key = name

