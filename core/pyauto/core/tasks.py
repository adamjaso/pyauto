from __future__ import print_function
import os
import sys
import inspect
import importlib
import shlex
from collections import OrderedDict
from pyauto.util import yamlutil


def _get_arg_names(module, func_name):
    return inspect.getargspec(getattr(module, func_name))[0]


def _is_valid_func(task_module, task_name):
    func = getattr(task_module, task_name)
    if not callable(func) or inspect.isclass(func):
        return False
    arg_names = _get_arg_names(task_module, task_name)
    if len(arg_names) < 1:
        return False
    return 'config' == arg_names[0]


def logerr(*args):
    sys.stderr.write(' '.join([str(a) for a in args]) + '\n')


class TaskSequences(object):
    def __init__(self, task_modules, task_dict, config):
        self.config = config
        self.task_dict = task_dict
        self.task_modules = [sys.modules['__main__']]
        for m in task_modules:
            if '__main__' != m:
                m = importlib.import_module(m)
                self.task_modules.append(m)

    @property
    def module_names(self):
        return [m.__name__ for m in self.task_modules]

    def get_task(self, task_name):
        if '.' in task_name:
            parts = task_name.split('.')
            module = '.'.join(parts[:-1])
            func = parts[-1]
            for sm in self.task_modules:
                if sm.__name__ == module and hasattr(sm, func):
                    return sm, getattr(sm, func)
        else:
            for sm in self.task_modules:
                if hasattr(sm, task_name):
                    return sm, getattr(sm, task_name)
        raise Exception('Task module "{0}" not found'.format(task_name))

    def _get_task_sequence(self, task_name):
        return self.task_dict.get(task_name)

    def get_task_sequence(self, task_name):
        task_list = self._get_task_sequence(task_name)
        if task_list is None:
            task_list = [task_name]
        return TaskSequence(self, task_name, task_list)

    def run_task_sequence(self, task_name, **kwargs):
        task_seq = self.get_task_sequence(task_name)
        if kwargs.get('inspect'):
            print(task_seq)
        elif kwargs.get('tree'):
            print(yamlutil.dump_dict(task_seq.to_tree()))
        else:
            quiet = kwargs.get('quiet')
            for task in task_seq.get_tasks():
                if not quiet:
                    print('-----', task.module_func_args, '-----')
                res = task.invoke()
                if not quiet:
                    print(task.orig, '=', res)
                elif res is not None:
                    print(res)
                print()

    def show_tasks(self):
        for task in self.iter_tasks():
            print(task)

    def iter_tasks(self):
        for task_module in self.task_modules:
            if '__main__' == task_module.__name__:
                module_name = ''
            else:
                module_name = task_module.__name__
            for task_name in dir(task_module):
                if not task_name.startswith('_') and \
                        _is_valid_func(task_module, task_name):
                    yield ''.join([
                        module_name, '.', task_name, ' ( ',
                        ', '.join(_get_arg_names(task_module, task_name)[1:]),
                        ' )'])


class TaskSequence(object):
    def __init__(self, parent, task_name, task_list):
        self.tasks = parent
        self.task_name = task_name
        self.task_list = []
        for task in task_list:
            names = self.tasks._get_task_sequence(task)
            if names is None:
                self.task_list.append(Task(parent, task))
            else:
                self.task_list.append(TaskSequence(parent, task, names))

    @property
    def task_sig(self):
        return ''.join([self.task_name, ' (  )'])

    def get_tasks(self):
        task_list = []
        for task in self.task_list:
            if isinstance(task, TaskSequence):
                task_list.extend(task.get_tasks())
            else:
                task_list.append(task)
        return task_list

    def to_tree(self):
        task_list = [task.to_tree() for task in self.task_list]
        return OrderedDict([
            (self.task_name, task_list),
        ])

    def __repr__(self):
        return str((self.task_name, [
            task.__repr__() for task in self.task_list]))

    def __str__(self, top=True):
        lines = []
        if top:
            lines.append(self.task_sig)
        for task in self.task_list:
            if isinstance(task, Task):
                lines.append('    ' + task.__str__())
            else:
                lines.extend([task.__str__(False)])
        return os.linesep.join(lines)


class Task(object):
    def __init__(self, parent, task_str):
        self.tasks = parent
        self.orig = task_str
        self.spec = TaskSpec.parse(task_str)\
            .parse_module_func(self.tasks.task_modules)
        self.name = self.spec.name
        self.args = self.spec.args
        self.module = self.spec.module
        self.func = self.spec.func

    def to_tree(self):
        return self.spec.module_func_args

    @property
    def module_func_name(self):
        return self.spec.module_func_name

    @property
    def module_func_args(self):
        return self.spec.module_func_args

    def invoke(self):
        return self.func(self.tasks.config, *self.args)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.spec.module_func_args


class TaskSpec(object):
    default_parser = None
    module = None
    module_name = None
    func = None
    func_name = None
    name = None
    args = None

    def __init__(self, *parts):
        parts = list(parts)
        self.name = parts[0]
        self.args = parts[1:]

    @property
    def module_func_name(self):
        return '.'.join([self.module_name, self.func_name])

    @property
    def module_func_args(self):
        parts = [self.module_func_name, '(', ', '.join(self.args), ')']
        return ' '.join(parts)

    def parse_module_func(self, task_modules):
        if '.' in self.name:
            func_parts = self.name.split('.')
            self.module_name = '.'.join(func_parts[:-1])
            self.func_name = func_parts[-1]
            self.module = importlib.import_module(self.module_name)
            self.func = getattr(self.module, self.func_name)
            for sm in task_modules:
                if sm.__name__ == self.module_name and \
                        hasattr(sm, self.func_name):
                    return self
        else:
            for sm in task_modules:
                if hasattr(sm, self.name):
                    self.module_name = sm.__name__
                    self.func_name = self.name
                    self.module = sm
                    self.func = getattr(sm, self.name)
                    return self
        raise Exception('Task module "{0}" not found'.format(self.name))

    @classmethod
    def parse_comma_format(cls, orig):
        parts = [str(p) for p in orig.split(',')]
        return cls(*parts)

    @classmethod
    def parse_command_format(cls, orig):
        parts = shlex.split(orig)
        return cls(*parts)

    @classmethod
    def parse(cls, orig):
        if cls.default_parser is None:
            cls.default_parser = cls.parse_comma_format
        return cls.default_parser(orig)

    @classmethod
    def set_parser(cls, parser):
        cls.default_parser = parser
