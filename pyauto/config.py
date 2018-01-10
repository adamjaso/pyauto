import sys, json, yaml, os
from pyauto import yamlutil
from collections import OrderedDict
from .strutil import root_prefix
from . import tasks


_config_classes = {}


class Config(dict):
    _cache = None
    _task_sequences = None
    _dirname = None

    def __init__(self, config_dict, parent=None, dirname=None):
        super(Config, self).__init__(config_dict)
        self.config = parent
        self._cache = {}
        self._dirname = dirname
        if dirname is None and parent is not None:
            self._dirname = parent._dirname
        if 'tasks' in config_dict:
            task_modules = config_dict.get('task_modules', [])
            task_modules.insert(0, '__main__')
            self._task_sequences = tasks.TaskSequences(
                task_modules, config_dict['tasks'], self)

    def __getattr__(self, item):
        return self.__getitem__(item, None)

    def __getitem__(self, item, default=None):
        val = self.get(item, default)
        if self.__class__ != Config:
            return val
        if item not in _config_classes:
            return val
        if item not in self._cache:
            self._cache[item] = _config_classes[item](val, parent=self)
        return self._cache[item]

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

    def run_task_sequences(self, *actions, **kwargs):
        quiet = kwargs.get('quiet', False)
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
            if not isinstance(value, dict):
                return value

            kvs = []
            for name, value in value.items():
                if isinstance(value, Config):
                    kvs.append((name, value.to_dict()))
                elif isinstance(value, dict):
                    kvs.append((name, dict(value)))
                elif isinstance(value, list):
                    kvs.append((name, [to_dict(v) for v in value]))
                else:
                    kvs.append((name, value))
            return OrderedDict(kvs)

        return to_dict(self)


def load(filename, dirname=None):
    with open(filename) as f:
        config = yaml.load(f.read())
        return Config(config, dirname=dirname)


def set_config_class(name, config_class):
    _config_classes[name] = config_class
